# Crea8it AI Career Launch Program — Setup & Deployment Guide

Complete step-by-step guide to get the app live on Streamlit Cloud.

---

## Overview

What you're setting up:

```
Google Sheet (your database)
    ↕
Google Cloud Service Account (the bridge)
    ↕
Streamlit Cloud App (what participants see)
```

Total setup time: ~30–45 minutes, done once.

---

## Step 1 — Create your Google Sheet

1. Go to [sheets.google.com](https://sheets.google.com) and create a new spreadsheet
2. Name it: **Crea8it Career Launch — Cohort 1**
3. Copy the Sheet ID from the URL:
   `https://docs.google.com/spreadsheets/d/` **THIS-IS-YOUR-ID** `/edit`
4. Save that ID — you'll need it later

### Create these 4 worksheets (tabs):

Rename "Sheet1" and add 3 more tabs at the bottom.

---

### Tab 1: Participants

Add these headers in **Row 1** exactly as written:

| A | B | C | D | E | F |
|---|---|---|---|---|---|
| full_name | email | phone | cohort_type | payment_code | registered_at |

Leave all other rows empty — the app fills them automatically.

---

### Tab 2: Progress

Add these headers in **Row 1**:

| A | B | C | D |
|---|---|---|---|
| email | week | task_index | completed_at |

Leave all other rows empty.

---

### Tab 3: PaymentCodes

Add these headers in **Row 1**:

| A | B |
|---|---|
| code | used |

Then add your payment codes below — one per row:

| code | used |
|------|------|
| CREA8-001 | |
| CREA8-002 | |
| CREA8-003 | |

**How to generate codes:** Use any pattern you like — `CREA8-001`, `ABDUL-2024`, or random strings. The `used` column stays blank until someone registers with that code. The app then writes "yes" automatically.

> 💡 Each time someone buys the Enter AI book, add their unique code to this sheet. You can batch-add codes in advance.

---

### Tab 4: Settings

Add this in **Row 1**:

| A | B |
|---|---|
| active_week | 1 |

This is the only cell you control from the admin panel. When you're ready to unlock Week 2, the app updates B1 to 2, and so on.

---

## Step 2 — Set up Google Cloud Service Account

This is the account your app uses to read/write the sheet. It takes about 10 minutes.

### 2a. Create a Google Cloud project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click the project dropdown at the top → **New Project**
3. Name it: `crea8it-career-launch`
4. Click **Create**

### 2b. Enable the APIs

With your project selected:

1. Go to **APIs & Services → Library**
2. Search for **Google Sheets API** → click it → click **Enable**
3. Go back to Library
4. Search for **Google Drive API** → click it → click **Enable**

### 2c. Create a service account

1. Go to **APIs & Services → Credentials**
2. Click **+ Create Credentials → Service Account**
3. Name: `crea8it-sheets-bot`
4. Click **Create and Continue** → skip optional steps → click **Done**

### 2d. Download the JSON key

1. Click your new service account (`crea8it-sheets-bot`)
2. Go to the **Keys** tab
3. Click **Add Key → Create new key → JSON**
4. A `.json` file downloads to your computer — keep it safe

Open the JSON file. It looks like this:

```json
{
  "type": "service_account",
  "project_id": "crea8it-career-launch",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n",
  "client_email": "crea8it-sheets-bot@crea8it-career-launch.iam.gserviceaccount.com",
  "client_id": "123456789",
  ...
}
```

You'll copy values from this file into your Streamlit secrets.

### 2e. Share your Google Sheet with the service account

1. Open your Google Sheet
2. Click **Share** (top right)
3. Paste the `client_email` from your JSON file
4. Set role to **Editor**
5. Click **Send**

> ⚠️ This step is easy to forget and will cause a "permission denied" error if skipped.

---

## Step 3 — Push the app to GitHub

1. Create a new **private** repo on GitHub — name it `crea8it-career-launch`
2. Upload all the app files maintaining this structure:

```
crea8it-career-launch/
├── app.py
├── config.py
├── requirements.txt
├── data/
│   └── content.py
├── pages/
│   ├── register.py
│   ├── dashboard.py
│   └── admin.py
└── utils/
    ├── sheets.py
    └── auth.py
```

> ⚠️ Do NOT push `secrets.toml` to GitHub — it contains your credentials. Add `.streamlit/secrets.toml` to your `.gitignore`.

---

## Step 4 — Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
2. Click **New app**
3. Select your repo: `crea8it-career-launch`
4. Branch: `main`
5. Main file path: `app.py`
6. Click **Advanced settings** — this is where you add your secrets

### Adding secrets on Streamlit Cloud

In the **Secrets** box, paste this (fill in your real values):

```toml
[gsheets]
spreadsheet_id         = "paste-your-sheet-id-here"
worksheet_participants = "Participants"
worksheet_progress     = "Progress"
worksheet_codes        = "PaymentCodes"

[admin]
password = "choose-a-strong-password"

[gcp_service_account]
type                        = "service_account"
project_id                  = "crea8it-career-launch"
private_key_id              = "paste from your JSON"
private_key                 = "-----BEGIN RSA PRIVATE KEY-----\npaste the full key here\n-----END RSA PRIVATE KEY-----\n"
client_email                = "crea8it-sheets-bot@crea8it-career-launch.iam.gserviceaccount.com"
client_id                   = "paste from your JSON"
auth_uri                    = "https://accounts.google.com/o/oauth2/auth"
token_uri                   = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url        = "paste from your JSON"
```

> 💡 For the `private_key` field — copy the entire key from the JSON file including the `-----BEGIN` and `-----END` lines. Replace actual newlines with `\n`.

7. Click **Save** → Click **Deploy**

Streamlit Cloud builds and deploys your app. Takes 2–3 minutes.

Your app URL will be:
`https://your-app-name.streamlit.app`

---

## Step 5 — Test before launching

Run through this checklist before announcing the program:

- [ ] Add 2–3 test payment codes to the PaymentCodes sheet
- [ ] Open your app URL and register with a test code
- [ ] Confirm the registration appears in the Participants sheet
- [ ] Log in to the admin panel with your password
- [ ] Check that the test participant shows in the admin view
- [ ] Mark a task complete — confirm it appears in the Progress sheet
- [ ] Unlock Week 2 from admin and verify it opens on the participant dashboard
- [ ] Try registering with the same code again — it should fail
- [ ] Try logging in with a non-existent email — it should fail cleanly

---

## Step 6 — Managing payment codes

Every time someone pays for the Enter AI book:

1. Open your PaymentCodes sheet
2. Add a new row with their unique code, `used` column blank
3. Send the code to the buyer (via WhatsApp, email, or Paystack webhook if automated later)

**Suggested code format:** `C8-XXXX` where XXXX is a random 4-digit number
Example: `C8-4821`, `C8-0073`, `C8-9156`

Keep a separate record of who got which code in case of disputes.

---

## Week-by-week operation

| Action | When | How |
|--------|------|-----|
| Add payment codes | When book is sold | Manually in PaymentCodes sheet |
| Unlock next week | Every Monday (or your schedule) | Admin panel → Cohort control |
| Check engagement | Any time | Admin panel → Engagement tab |
| Export participant list | Any time | Admin panel → Participants → Export CSV |
| Update content/tasks | Before each week | Edit `data/content.py` and push to GitHub |

---

## Troubleshooting

**"Permission denied" error on launch**
→ You didn't share the Google Sheet with the service account email. See Step 2e.

**"Spreadsheet not found" error**
→ Check that `spreadsheet_id` in secrets matches the ID in your sheet URL.

**"Invalid payment code" even for new codes**
→ Check column header in PaymentCodes sheet is exactly `code` (lowercase).

**App not updating after code push**
→ Streamlit Cloud auto-deploys on push. Wait 1–2 minutes and refresh.

**Secrets not working**
→ Make sure there are no trailing spaces in secret values. The `private_key` must have `\n` not actual line breaks inside the TOML string.

---

## Costs

| Service | Cost |
|---------|------|
| Google Sheets | Free |
| Google Cloud (Sheets + Drive API) | Free (well within free tier) |
| Streamlit Cloud | Free (1 app on free plan) |
| **Total** | **₦0** |

---

*Built for the Crea8it AI Career Launch Program — Cohort 1*
