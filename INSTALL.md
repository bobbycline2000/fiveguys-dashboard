# SCG Dashboard — Installation

This folder is your dashboard package. To install on a new PC, you only need to do this once.

---

## What you need before you start

- A Windows PC that stays on overnight (the dashboard updates each morning)
- Python 3.10 or newer — download from <https://www.python.org/downloads/>
  - **Important:** during install, check the box that says **"Add Python to PATH"**
- The Gmail address that receives your Par Brink scheduled-report emails
- About 5 minutes

---

## Step 1 — Copy the folder

Copy the entire `fiveguys-dashboard` folder to your PC. Anywhere is fine, but a stable location like `C:\SCG\fiveguys-dashboard` is recommended.

---

## Step 2 — Run the installer

Open the folder and **double-click `scg_install.bat`**.

A black window will open and walk you through three questions:

1. **Store number** — your Five Guys store number (e.g., `2065`)
2. **Store display name** — how it should appear on the dashboard (e.g., `KY-2065 Dixie Highway`)
3. **Gmail address** — the email account where Par Brink reports arrive

After you answer, the installer will:

- Install the Python packages it needs
- Create your store's config file
- Open your web browser so you can sign into Gmail

---

## Step 3 — Grant Gmail access

In the browser:

1. Sign in with the Gmail address you typed in Step 2
2. You'll see a warning that says **"Google hasn't verified this app"** — this is normal during testing
3. Click **Advanced**, then **"Go to Savior Consulting Group Dashboard (unsafe)"**
4. Check both Gmail permission boxes (or check **"Select all"**)
5. Click **Continue**

The browser will say "The authentication flow has completed." Close the tab.

Back in the installer window, you'll see:

```
  [4/4] Verifying setup...
        [OK] OAuth client present
        [OK] Refresh token saved
        [OK] Store config present

  Setup complete!
```

Press any key to close.

---

## Step 4 — Schedule it to run daily (optional)

The installer connects your Gmail but doesn't yet run on a schedule. To have your dashboard update automatically every morning:

1. Open Windows **Task Scheduler** (search Start menu)
2. Click **Create Basic Task**
3. Name: `SCG Dashboard Daily`
4. Trigger: **Daily**, time **8:15 AM**
5. Action: **Start a program**
6. Program: `python.exe`
7. Arguments:
   ```
   "C:\SCG\fiveguys-dashboard\scraper\parbrink_email_pickup.py" --store YOUR_STORE_NUMBER
   ```
   (replace `YOUR_STORE_NUMBER` with the number you typed earlier)
8. Click **Finish**

Your dashboard will update every morning automatically. The PC must be on at the scheduled time — sleeping is fine, the task will wake it.

---

## Testing it now

To check that everything works without waiting until morning, open Command Prompt in the folder and run:

```
python scraper\parbrink_email_pickup.py --store YOUR_STORE_NUMBER
```

If reports have arrived for yesterday, you'll see them downloaded under `data\raw\parbrink\YOUR_STORE_NUMBER\`.

---

## Re-running the wizard

If you switch Gmail accounts or something goes wrong, just double-click `scg_install.bat` again. It's safe to re-run.

---

## Troubleshooting

- **"Python is not installed"** — install Python from <https://www.python.org/downloads/> and check "Add Python to PATH"
- **Browser doesn't open** — copy the `https://accounts.google.com/...` URL from the installer window and paste into your browser manually
- **"Access blocked: ... has not completed verification"** — Bobby (the developer) needs to add your Gmail address as a test user. Send him your email.
- **Reports not appearing** — verify the Par Brink schedule is sending to the same Gmail you connected. Forwarded emails do not work.

---

## What gets stored on this PC

- `secrets/scg_oauth_client.json` — the SCG product's app credentials (same file ships with every install)
- `secrets/scg_refresh_token.json` — your private Gmail access token. **Do not share this file.**
- `config/{your_store}.json` — your store's settings
- `data/raw/parbrink/{your_store}/{date}/` — downloaded PDFs each day

The `secrets/` folder is excluded from git automatically. Your token never leaves this PC.
