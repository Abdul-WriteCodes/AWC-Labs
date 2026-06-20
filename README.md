# Crea8it AI Career Launch Program App

Streamlit + Google Sheets app for running the Crea8it cohort program.

## Setup

### 1. Google Sheets structure
Create a Google Sheet with these 4 worksheets:

**Participants** (columns in order):
`full_name | email | phone | cohort_type | payment_code | registered_at`

**Progress** (columns in order):
`email | week | task_index | completed_at`

**PaymentCodes** (columns in order):
`code | used`
→ Pre-fill this sheet with payment codes after each book sale. Set `used` to blank initially.

**Settings** (just one cell):
`Cell A1`: "active_week" | `Cell B1`: 1
→ You update B1 via the admin panel to unlock each week.

### 2. Google Cloud service account
- Create a project at console.cloud.google.com
- Enable Google Sheets API and Google Drive API
- Create a service account and download the JSON key
- Share your Google Sheet with the service account email (Editor access)

### 3. Secrets
- Copy `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml`
- Fill in your spreadsheet ID, service account credentials, and admin password

### 4. Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

### 5. Deploy on Streamlit Cloud
- Push to GitHub (keep secrets.toml out of git — it's in .gitignore)
- Connect repo to share.streamlit.io
- Add secrets in the Streamlit Cloud dashboard

## How it works

1. Participant buys Enter AI book (₦5,000) → receives a unique payment code
2. They register on the app with their code → account created, code marked used
3. Each Monday you unlock the next week from the Admin panel
4. Participants log in, read materials, check off tasks, track progress
5. Week 6 complete → they submit their 90-day roadmap and graduate

## Admin panel
- View all registrations and export CSV
- Track task completion per participant per week
- Control which week is currently active
- See revenue estimate

## File structure
```
app.py              # Entry point + routing
config.py           # Constants and secrets
pages/
  register.py       # Registration + login
  dashboard.py      # Participant dashboard
  admin.py          # Admin control panel
utils/
  sheets.py         # All Google Sheets operations
  auth.py           # Session management
data/
  content.py        # Week content and tasks
.streamlit/
  secrets.toml      # Your credentials (not in git)
```
