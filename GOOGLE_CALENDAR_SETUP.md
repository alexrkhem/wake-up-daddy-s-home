# Google Calendar Setup — Step-by-Step Checklist

Follow these steps exactly to get your `credentials.json` file.
**Time required: ~10 minutes.**

---

## Step 1 — Create a Google Cloud Project

- [ ] Go to [https://console.cloud.google.com](https://console.cloud.google.com)
- [ ] Click the project dropdown (top left, next to "Google Cloud")
- [ ] Click **"New Project"**
- [ ] Name it `Jarvis Dashboard` (or anything)
- [ ] Click **Create** and wait ~30 seconds for it to provision
- [ ] Make sure the new project is selected in the dropdown

---

## Step 2 — Enable the Google Calendar API

- [ ] In the left sidebar, go to **APIs & Services → Library**
- [ ] Search for `Google Calendar API`
- [ ] Click on it → Click **Enable**
- [ ] Wait for it to enable (green checkmark)

---

## Step 3 — Configure OAuth Consent Screen

- [ ] Go to **APIs & Services → OAuth consent screen**
- [ ] Select **External** → Click **Create**
- [ ] Fill in required fields:
  - App name: `Jarvis Dashboard`
  - User support email: your Gmail address
  - Developer contact email: your Gmail address
- [ ] Click **Save and Continue**
- [ ] On **Scopes** page: Click **Save and Continue** (no need to add scopes here)
- [ ] On **Test Users** page:
  - [ ] Click **+ Add Users**
  - [ ] Add your own Gmail address
  - [ ] Click **Add** → **Save and Continue**
- [ ] Click **Back to Dashboard**

> ⚠️ **Important:** You MUST add yourself as a Test User or the authorization will fail with a "403 access denied" error.

---

## Step 4 — Create OAuth 2.0 Credentials

- [ ] Go to **APIs & Services → Credentials**
- [ ] Click **+ Create Credentials** → **OAuth client ID**
- [ ] Application type: **Desktop app**
- [ ] Name: `Jarvis Dashboard Desktop`
- [ ] Click **Create**
- [ ] A dialog will appear — click **Download JSON**
- [ ] The file downloads as something like `client_secret_XXXXX.json`

---

## Step 5 — Install the credentials file

- [ ] Rename the downloaded file to exactly: **`credentials.json`**
- [ ] Move it into your dashboard folder (same folder as `app.py`)
- [ ] Your folder should now look like:
  ```
  dashboard/
  ├── app.py
  ├── credentials.json   ← here
  ├── database.py
  └── ...
  ```

---

## Step 6 — Authorize on first use

- [ ] Start your dashboard: `streamlit run app.py`
- [ ] Navigate to the **📅 Calendar** page
- [ ] A browser window will automatically open asking you to authorize
- [ ] Log in with your Google account → Click **Allow**
- [ ] You'll see a "The authentication flow has completed" message
- [ ] A `token.json` file will be created automatically — **don't delete it**
- [ ] Go back to the dashboard — your calendar events should now appear

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "403 access_denied" | Make sure you added your Gmail as a Test User in Step 3 |
| "credentials.json not found" | Make sure the file is in the same folder as app.py |
| "redirect_uri_mismatch" | Make sure you chose **Desktop app** (not Web app) in Step 4 |
| Token expired | Delete `token.json` and re-authorize |
| Events not showing | Click "🔄 Refresh Calendar" on the Calendar page |

---

## Revoking Access (if needed)

Go to [https://myaccount.google.com/permissions](https://myaccount.google.com/permissions) and remove `Jarvis Dashboard` from authorized apps. Then delete `token.json` and re-authorize.
