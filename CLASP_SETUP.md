# Google Apps Script + Git Setup (clasp)

## What is clasp?

`clasp` (Command Line Apps Script Projects) lets you edit Google Apps Script files locally and sync them with Google Sheets. This means you can use Git for version control!

---

## Initial Setup (One-time)

### 1. Install Node.js
Download from: https://nodejs.org/ (LTS version)

### 2. Install clasp globally
```bash
npm install -g @google/clasp
```

### 3. Login to Google
```bash
clasp login
```
This opens a browser window. Sign in with your Google account that has access to the sheets.

---

## Option A: Link to Existing Google Apps Script Project

### 1. Get your Script ID
1. Open your Google Sheet
2. Extensions → Apps Script
3. Click the gear icon (Project Settings)
4. Copy the **Script ID** (looks like: `1a2b3c4d5e6f7g8h9i0j...`)

### 2. Clone the project
```bash
cd "C:\Users\noagi\Desktop\JGDC"
clasp clone <YOUR_SCRIPT_ID>
```

This creates `.clasp.json` with your project ID.

### 3. Pull current code
```bash
clasp pull
```

This downloads all files from Google Apps Script to your local folder.

---

## Option B: Create New Google Apps Script Project

### 1. Create new project linked to your sheet
```bash
cd "C:\Users\noagi\Desktop\JGDC"
clasp create --title "JGDC Provider Tools" --type sheets --rootDir .
```

### 2. When prompted, select your Google Sheet

---

## Daily Workflow

### Push local changes to Google Sheets
```bash
clasp push
```

This uploads your local `.js` and `.html` files to Google Apps Script.

### Pull changes from Google Sheets
```bash
clasp pull
```

Download any changes made in the online Apps Script editor.

### Open Apps Script editor in browser
```bash
clasp open
```

---

## Important Notes

### Files that sync:
- `.js` files → Code.gs, ToolboxSuite.gs, etc.
- `.html` files → HTML files in Apps Script

### Files that DON'T sync:
- `.md` files (README, TODO) - local only
- `.csv` files - local only (gitignored)
- Python scripts - local only

### Before pushing:
```bash
# Check what will be uploaded
clasp status

# View differences
git diff
```

### Workflow with Git:
```bash
# 1. Make changes to .js files locally
# 2. Test in Google Sheets (clasp push)
# 3. Once working, commit to git
git add ToolboxSuite.js
git commit -m "Add validation function"

# 4. Push to Google Sheets
clasp push
```

---

## Troubleshooting

### Error: "User has not enabled the Apps Script API"
1. Go to: https://script.google.com/home/usersettings
2. Turn ON "Google Apps Script API"

### Error: "Unable to read .clasp.json"
You need to run `clasp clone <SCRIPT_ID>` or `clasp create` first.

### Files not syncing
Check `.claspignore` file - it lists files that won't be uploaded.

### Multiple Google accounts
```bash
# Login with specific account
clasp login --creds <path-to-creds.json>
```

---

## .clasp.json Structure

After running `clasp clone` or `clasp create`, you'll have:

```json
{
  "scriptId": "YOUR_SCRIPT_ID_HERE",
  "rootDir": "."
}
```

**DO NOT commit this file to public repos** (it contains your project ID).
Already added to `.gitignore`.

---

## Quick Reference

| Command | What it does |
|---------|-------------|
| `clasp login` | Authenticate with Google |
| `clasp clone <ID>` | Download existing project |
| `clasp create` | Create new project |
| `clasp push` | Upload local → Google |
| `clasp pull` | Download Google → local |
| `clasp open` | Open in browser |
| `clasp status` | Show file status |
| `clasp logs` | View execution logs |

---

## Next Steps

1. Run `clasp clone <YOUR_SCRIPT_ID>` (get ID from your Google Sheet)
2. Edit files locally in VS Code or your preferred editor
3. `clasp push` to upload changes
4. Test in Google Sheets
5. Commit working changes to git
6. Repeat!

---

## Alternative: Manual Sync (No clasp)

If you prefer not to use clasp:

1. Edit `.js` and `.html` files locally
2. Copy-paste code into Apps Script editor in Google Sheets
3. Save in Google Sheets
4. Commit changes to git

**Downside:** More manual work, easy to forget to sync.
**Upside:** No command-line tools needed.
