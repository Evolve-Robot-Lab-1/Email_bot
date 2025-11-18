# Quick Start - Send Your VC Emails in 5 Minutes

## What This Does

You write your email → AI adds 2-3 lines explaining why THAT company needs your product → Send!

---

## Step-by-Step (5 Minutes)

### 1. Run the App
```bash
cd "/home/evolve/AI PROJECT/Gmail_integeration"
python3 app_v2.py
```
Open: http://127.0.0.1:5001

### 2. Setup (One Time Only)

**Get Groq API Key** (FREE - takes 2 minutes):
1. Go to https://console.groq.com/
2. Sign up
3. Create API key
4. Copy it

**Update .env file:**
```bash
GROQ_API_KEY=your_actual_key_here
```

### 3. Upload Your VC List (CSV)

Your CSV should have:
- **Company** - VC firm name
- **Email** - Contact email
- **Details** - Company focus, portfolio, investment areas

Example `companies.csv`:
```csv
Company,Email,Details
Chiratae Ventures,swami@chiratae.com,"Early-stage VC focusing on AI, SaaS, and enterprise tech. Portfolio includes legal-tech companies. Series A focus."
Sequoia Capital India,support@sequoiacap.com,"Leading VC with focus on AI and deep tech. Portfolio includes legal-tech and enterprise SaaS."
```

### 4. Select "Custom Template"

Email Style: **"Custom Template (AI adds WHY section only)"**

### 5. Write Your Email

The default template is already loaded with your Durga AI email:

```
Dear {{company}},

Legal marketplaces failed because lawyers made less money through platforms than working direct.

AI changed this. Now lawyers review AI drafts instead of writing from scratch. They earn more per hour. Customers pay less. Platform wins. First time the economics work.

{{why}}

We're live. Lawyers joining unprompted. Enterprise pilots starting. Early revenue flowing.

Crosby proved this in the US. India's 10x bigger. Nobody's figured it out here yet.

6 month window before competitors catch up.

Building India's legal infrastructure, starting with documents, expanding to everything.

Worth a call?

Praveen
Founder, Durga AI
```

**Note:** `{{why}}` is where AI inserts 2-3 personalized lines

### 6. Click "Generate AI Emails"

### 7. Review & Send!

---

## What You Get

### For Chiratae Ventures:

**Subject:** Legal AI - India opportunity

**Body:**
```
Dear Chiratae Ventures,

Legal marketplaces failed because lawyers made less money through platforms than working direct.

AI changed this. Now lawyers review AI drafts instead of writing from scratch. They earn more per hour. Customers pay less. Platform wins. First time the economics work.

Chiratae's portfolio in AI and SaaS startups makes this especially relevant. Your legal-tech investments could benefit from this proven economic model.

We're live. Lawyers joining unprompted. Enterprise pilots starting. Early revenue flowing.

Crosby proved this in the US. India's 10x bigger. Nobody's figured it out here yet.

6 month window before competitors catch up.

Building India's legal infrastructure, starting with documents, expanding to everything.

Worth a call?

Praveen
Founder, Durga AI
```

**See the 2 lines added?** They're personalized to Chiratae's focus on AI/SaaS and legal-tech!

### For Sequoia Capital India:

```
Dear Sequoia Capital India,

Legal marketplaces failed because lawyers made less money through platforms than working direct.

AI changed this. Now lawyers review AI drafts instead of writing from scratch. They earn more per hour. Customers pay less. Platform wins. First time the economics work.

Given your deep tech portfolio and focus on scalable AI solutions, the India legal infrastructure opportunity aligns perfectly with your investment thesis.

We're live. Lawyers joining unprompted. Enterprise pilots starting. Early revenue flowing.

Crosby proved this in the US. India's 10x bigger. Nobody's figured it out here yet.

6 month window before competitors catch up.

Building India's legal infrastructure, starting with documents, expanding to everything.

Worth a call?

Praveen
Founder, Durga AI
```

**Different WHY** - personalized to Sequoia's deep tech focus!

---

## Customization

### Change Your Email

Just edit the "Your Email Message" box. Make sure to keep `{{why}}` where you want personalization.

### Change Subject Line

Default: "Legal AI - India opportunity"

Change to anything:
- "Quick question"
- "Partnership opportunity for {{company}}"
- "India legal tech - 6 month window"

### Update Product Info

This helps AI understand your product for better personalization:
```
AI-powered legal document automation. Lawyers review AI drafts vs writing from scratch.
50+ active lawyers, 3 enterprise pilots, $15K MRR growing 40% MoM.
```

### Upload Additional Materials (Optional)

You can now upload supporting materials:
- **PDF** - Pitch decks, product brochures
- **DOCX** - Documents, case studies
- **Images** - Product screenshots, logos
- **Videos** - Demo videos, product tours
- **GIF** - Animated demos

**How to use:**
1. Click the "Additional Materials" upload area
2. Select files (max 10MB each)
3. Files will be uploaded and displayed
4. AI can reference these materials for context

**Tip:** Upload your pitch deck or product demo to give AI more context about your product!

---

## Tips for Best Results

### 1. Add Detailed Company Info in CSV

**Bad:**
```csv
Company,Email,Details
Chiratae Ventures,swami@chiratae.com,"VC firm"
```

**Good:**
```csv
Company,Email,Details
Chiratae Ventures,swami@chiratae.com,"Early-stage VC focusing on AI, SaaS, enterprise tech. Portfolio in legal-tech, automation. Series A. Known for backing founder-friendly deals in India."
```

More details = Better personalization!

### 2. Position {{why}} Strategically

**Good Placement:**
- After problem/solution (like in default template)
- Before traction
- Anywhere it makes sense in YOUR flow

**Bad Placement:**
- At the very start (no context yet)
- At the very end (too late)

### 3. Keep Your Style

The AI matches YOUR tone:
- Concise → AI writes concise WHY
- Formal → AI writes formal WHY
- Punchy → AI writes punchy WHY

---

## Troubleshooting

**Q: AI didn't add the WHY section**

A: Make sure you selected "Custom Template" style and added `{{why}}` in your message

---

**Q: WHY section is too long**

A: AI is instructed to write max 2-3 lines (50 words). If it's longer, the company details might be too generic. Add more specific info.

---

**Q: WHY is too generic**

A: Add more details in the CSV "Details" column about the company's focus, portfolio, investment thesis

---

**Q: Can I use this for clients instead of VCs?**

A: Yes! Just change your email message and upload client list. AI adapts.

---

## Ready to Launch!

1. ✅ Update .env with Groq API key
2. ✅ Run: `python3 app_v2.py`
3. ✅ Open: http://127.0.0.1:5001
4. ✅ Select "Custom Template"
5. ✅ Upload companies.csv
6. ✅ Click "Generate AI Emails"
7. ✅ Review and Send!

**That's it!** Your personalized VC emails are ready. 🚀
