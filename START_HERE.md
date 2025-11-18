# ⚠️ IMPORTANT - Use The New App!

## The Problem

You're using the **OLD app** (port 3000) which generates full emails and ignores your template.

## The Solution

Use the **NEW app** (port 5001) which does EXACTLY what you want:
- Uses YOUR email template
- Adds ONLY company name + 2-3 WHY lines
- Nothing else changes

---

## How to Use the NEW App

### Step 1: Stop the Old App (if running)

If app.py is running on port 3000, stop it.

### Step 2: Start the NEW App

```bash
cd "/home/evolve/AI PROJECT/Gmail_integeration"
python3 app_v2.py
```

You'll see:
```
============================================================
 Gmail Campaign Builder V2 - AI-Powered
============================================================
 Running on: http://127.0.0.1:5001
 AI Assistant: Groq (Llama 3.3 70B)
 Features: Campaign Builder | Inbox | Analytics
============================================================
```

### Step 3: Open NEW URL

**NEW APP:** http://127.0.0.1:5001 ✅
**OLD APP:** http://127.0.0.1:3000 ❌ (don't use this)

### Step 4: Use It

1. **Email Style:** Select "Custom Template (AI adds WHY section only)"
2. **Your Email Message:** Already has your Durga AI template loaded!
3. **Upload CSV:** Your companies.csv
4. **Generate:** Click "Generate AI Emails"

That's it!

---

## What's Different

### OLD App (port 3000) ❌
- Has "Auto-generate cold emails" checkbox
- Generates FULL professional emails
- Ignores your template
- Adds lots of fluff

### NEW App (port 5001) ✅
- No checkbox needed
- Uses YOUR exact email
- Adds ONLY 2-3 personalized lines
- Keeps your style

---

## Quick Test

1. Start new app: `python3 app_v2.py`
2. Go to: http://127.0.0.1:5001
3. See your Durga AI email pre-loaded? ✅
4. Upload companies.csv
5. Click Generate
6. Check preview - only 2-3 lines added? ✅

Done!

---

## If You MUST Use Old App

If you really want to keep using the old app.py, I can update that too.
Just let me know!

But the NEW app is built specifically for your workflow. 🚀
