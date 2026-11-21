"""Download Patty Press newsletters from the fg2065 inbox and extract their text.

The Patty Press email body is only a Constant Contact "Download Newsletter" link
to an Egnyte file. The PDF is usually image-only, so text extraction falls back
to Windows built-in OCR (winocr) when pypdf finds nothing. Built 2026-11-21 for
the daily brief audit (the brief had never actually read a Patty Press issue).

Usage:
    python scraper/patty_press_fetch.py --days 10   (default out: BobbyWorkspace/_reference/patty-press)
Outputs:
    <out>/patty-press-YYYY-MM-DD.pdf   (one per issue, week-of date)
    <out>/patty-press-YYYY-MM-DD.txt   (extracted / OCR text)
"""
from __future__ import annotations

import argparse
import asyncio
import io
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import read_outlook_via_gmail as R  # noqa: E402

UA = {"User-Agent": "Mozilla/5.0"}


def list_issues(token: str, days: int) -> list[dict]:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = (f"{R.REST_BASE}/messages?$top=50&$select=Subject,ReceivedDateTime,Body"
           f"&$filter=ReceivedDateTime ge {cutoff}&$orderby=ReceivedDateTime desc")
    headers = {"Authorization": f"Bearer {token}", "Prefer": 'outlook.body-content-type="text"'}
    msgs = []
    while url:
        r = requests.get(url, headers=headers, timeout=60)
        r.raise_for_status()
        j = r.json()
        msgs.extend(j.get("value", []))
        url = j.get("@odata.nextLink")
    out, seen = [], set()
    for m in msgs:
        s = m.get("Subject") or ""
        if "Patty Press Newsletter - Week of" not in s or s.startswith(("Reminder", "Fw", "FW", "RE")):
            continue
        wk = re.search(r"Week of (\w+ \d+, \d{4})", s)
        link = re.search(r"Download Newsletter<(https?://[^>]+)>", (m.get("Body") or {}).get("Content", ""))
        if not wk or not link:
            continue
        d = datetime.strptime(wk.group(1), "%B %d, %Y").strftime("%Y-%m-%d")
        if d not in seen:
            seen.add(d)
            out.append({"date": d, "link": link.group(1)})
    return out


def download(link: str) -> bytes | None:
    sess = requests.Session()
    r = sess.get(link, headers=UA, allow_redirects=True, timeout=60)
    if r.content[:4] == b"%PDF":
        return r.content
    tok = re.search(r"/dl/([A-Za-z0-9]+)", r.url)
    if not tok:
        return None
    host = re.match(r"https://[^/]+", r.url).group(0)
    for u in (f"{host}/dd/{tok.group(1)}", f"{host}/dl/{tok.group(1)}?dl=1"):
        rr = sess.get(u, headers=UA, timeout=180)
        if rr.content[:4] == b"%PDF":
            return rr.content
    return None


def pdf_text(pdf: bytes) -> str:
    from pypdf import PdfReader
    txt = "".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(pdf)).pages)
    if len(txt) > 2000:
        return txt
    try:
        import fitz
        import winocr
        from PIL import Image
    except ImportError:
        return txt + "\n[image-only PDF; install pymupdf + winocr for OCR]"

    async def run() -> str:
        parts = []
        for i, page in enumerate(fitz.open(stream=pdf, filetype="pdf")):
            img = Image.open(io.BytesIO(page.get_pixmap(dpi=110).tobytes("png"))).convert("RGB")
            W, H = img.size
            parts.append(f"--- page {i + 1}")
            for y in range(0, H, 2400):
                res = await winocr.recognize_pil(img.crop((0, y, W, min(H, y + 2460))), "en-US")
                parts.append("\n".join(l.text for l in res.lines))
        return "\n".join(parts)

    return asyncio.run(run())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=10)
    # PDFs run 15-40 MB each -- keep them OUT of the repo.
    ap.add_argument("--out", default=r"C:\Users\bobby\OneDrive\BobbyWorkspace\_reference\patty-press")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    issues = list_issues(R._rest_token(), a.days)
    for it in issues:
        pdf_path = out / f"patty-press-{it['date']}.pdf"
        txt_path = out / f"patty-press-{it['date']}.txt"
        if txt_path.exists():
            print(it["date"], "already extracted")
            continue
        pdf = pdf_path.read_bytes() if pdf_path.exists() else download(it["link"])
        if not pdf:
            print(it["date"], "DOWNLOAD FAILED")
            continue
        pdf_path.write_bytes(pdf)
        txt_path.write_text(pdf_text(pdf), encoding="utf-8")
        print(it["date"], "OK", txt_path)
    if not issues:
        print("no Patty Press issues in window")
    return 0


if __name__ == "__main__":
    sys.exit(main())
