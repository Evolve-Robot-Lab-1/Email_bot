# Custom Template Mode - Quick Start Guide

## What This Does

You write your email. AI adds 2-3 lines explaining WHY that specific company needs your product. That's it!

---

## How to Use

### Step 1: Select Custom Template Mode

In Campaign Builder:
- **Email Style:** Select "Custom Template (AI adds WHY section only)"

### Step 2: Write Your Email Template

In the **Message Template** box, write your email and use `{{why}}` where you want AI to insert the personalized explanation:

```
Dear {{company}} Team,

I'm Praveen, Founder of DurgaAI.

{{why}}

Our product: AI-powered legal document automation that helps organizations streamline
legal workflows and reduce costs by 40%. We use advanced AI to generate legal drafts
that lawyers review, instead of writing from scratch.

We've helped companies like TechCorp and LegalPro achieve 50% faster document processing
and 40% cost reduction.

Would you be open to a brief call to discuss how we can help {{company}}?

Best regards,
Praveen Kumar
Founder, DurgaAI
Email: praveen@durgaai.com
Phone: +91-XXXXXXXXXX
```

### Step 3: Fill Product Description

This helps AI understand your product for personalization:

```
AI-powered legal document automation. Lawyers review AI-generated drafts instead of
writing from scratch. Reduces costs by 40%, increases speed by 50%. Live with 50+
lawyers, 3 enterprise clients.
```

### Step 4: Upload Your CSV

CSV should have:
- **Company** - Company name
- **Email** - Email address
- **Details** - Company background/description (important for personalization!)

Example CSV:
```csv
Company,Email,Details
Chiratae Ventures,swami@chiratae.com,"Early-stage VC firm focusing on Indian startups in AI SaaS and enterprise technology. Portfolio includes companies in legal-tech and business automation. Focus on Series A investments."
Sequoia Capital India,support@sequoiacap.com,"Leading VC with focus on AI and deep tech startups. Portfolio includes multiple legal-tech and enterprise SaaS companies. Investment focus on scalable technology solutions."
```

### Step 5: Generate Emails

Click **"Generate AI Emails"**

---

## What You Get

### Input Template:
```
Dear {{company}} Team,

I'm Praveen, Founder of DurgaAI.

{{why}}

Our product: AI-powered legal document automation...

Would you be open to a brief call?

Best regards,
Praveen
```

### Generated Email for Chiratae Ventures:
```
Dear Chiratae Ventures Team,

I'm Praveen, Founder of DurgaAI.

Given Chiratae Ventures' focus on AI and SaaS startups, particularly in the legal-tech
space, our solution aligns perfectly with your portfolio strategy. Your portfolio
companies in enterprise technology could benefit significantly from our AI-powered
automation platform. This represents a strong opportunity for portfolio value addition
and potential investment consideration.

Our product: AI-powered legal document automation that helps organizations streamline
legal workflows and reduce costs by 40%. We use advanced AI to generate legal drafts
that lawyers review, instead of writing from scratch.

We've helped companies like TechCorp and LegalPro achieve 50% faster document processing
and 40% cost reduction.

Would you be open to a brief call to discuss how we can help Chiratae Ventures?

Best regards,
Praveen Kumar
Founder, DurgaAI
Email: praveen@durgaai.com
Phone: +91-XXXXXXXXXX
```

---

## Placeholders You Can Use

- **{{company}}** - Replaced with actual company name
- **{{why}}** - AI generates 2-3 lines explaining WHY they need your product
- **{{product}}** - Your product description (if you want to use variable)
- **{{our_company}}** - Your company info (if you want to use variable)

**Most Common:** Just use `{{company}}` and `{{why}}`

---

## Tips for Best Results

### 1. Provide Detailed Company Information in CSV

**Bad CSV Details:**
```
"VC firm in India"
```

**Good CSV Details:**
```
"Early-stage VC firm focusing on Indian startups in AI, SaaS, and enterprise technology.
Portfolio includes companies in legal-tech and business automation. Focus on Series A
investments in B2B SaaS. Known for supporting startups in operational efficiency and
AI-driven solutions."
```

The more specific the company details, the better AI can explain WHY they need your product!

### 2. Keep Your Template Professional

- Use proper greeting
- Include your full name and title
- Add contact information
- Professional signature
- Clear call-to-action

### 3. Position {{why}} Strategically

**Good placement:**
```
I'm [Name], Founder of [Company].

{{why}}

Our product does [X, Y, Z]...
```

**Also good:**
```
Our product does [X, Y, Z]...

{{why}}

We've helped companies like...
```

### 4. Write Once, Personalize for All

Your template is used for ALL companies. The `{{why}}` section is the ONLY part that changes per company.

So make sure your template:
- Works for all target companies
- Doesn't mention specific company details (except in {{why}})
- Is general enough to apply broadly

---

## Example Templates

### Template 1: Short & Professional

```
Dear {{company}} Team,

{{why}}

DurgaAI uses AI to automate legal document creation. Lawyers review AI drafts instead
of writing from scratch - earning 2x more per hour while customers pay 50% less.

Live with 50+ lawyers. 3 enterprise clients. $15K MRR growing 40% monthly.

Worth a call?

Praveen
Founder, DurgaAI
praveen@durgaai.com
```

### Template 2: Detailed Professional

```
Dear {{company}} Team,

I'm Praveen Kumar, Founder & CEO of DurgaAI.

{{why}}

We've built an AI-powered legal document automation platform that fundamentally changes
the economics of legal services. Lawyers review AI-generated drafts instead of writing
from scratch, which:
• Increases lawyer earnings by 2x per hour
• Reduces customer costs by 50%
• Maintains quality and compliance

We're live with 50+ active lawyers, 3 enterprise clients, and generating $15K MRR with
40% month-over-month growth. Companies like Crosby validated this model in the US with
$100M+ ARR. India's market is 10x larger and currently underserved.

Would you be open to a brief call to discuss how DurgaAI could fit into your portfolio
or serve {{company}}'s needs?

Best regards,
Praveen Kumar
Founder & CEO, DurgaAI
Email: praveen@durgaai.com
Phone: +91-XXXXXXXXXX
Website: durgaai.com
```

### Template 3: Partnership Focus

```
Hi {{company}} team,

{{why}}

I'm reaching out to explore a potential partnership. DurgaAI has developed AI-powered
legal document automation that's generating strong traction:

- 50+ active lawyers
- 3 enterprise pilots
- $15K MRR, 40% growth MoM
- 50% cost reduction for clients
- 2x earnings increase for lawyers

We're looking for [what you want from them - investment, partnership, pilot, etc.].

Interested in learning more?

Best,
Praveen
DurgaAI
```

---

## Comparison: Before vs After

### BEFORE (What you were getting):

```
Dear Chiratae Ventures - Chennai Team,

I'm [Your Name], Founder & CEO of [Your Company].

Our company specializes in DurgaAI (legal document ai). We're building InnovateAI,
an intelligent business solution that helps organizations optimize operations...

What makes InnovateAI different?
InnovateAI is not just another business optimization tool. It delivers:
• Analyze business processes and identify optimization opportunities...
• Auto-implement workflow improvements and generate data-driven...
• Continuously monitor business metrics, instantly flagging issues...

Simply put: it transforms business operations from reactive to proactive intelligence...

Warm regards,
[Your Name]
```

**Problems:**
- Generic placeholders not replaced
- Not personalized to Chiratae Ventures
- Too long and templated
- Doesn't explain WHY Chiratae needs it

### AFTER (Custom Template Mode):

```
Dear Chiratae Ventures Team,

I'm Praveen Kumar, Founder of DurgaAI.

Given Chiratae Ventures' focus on AI and SaaS startups, particularly in the legal-tech
space, our solution aligns perfectly with your portfolio strategy. Your portfolio
companies in enterprise technology could benefit significantly from our AI automation
platform. This represents a strong opportunity for portfolio value addition and
potential investment consideration.

Our product: AI-powered legal document automation that helps organizations streamline
legal workflows and reduce costs by 40%. Lawyers review AI drafts instead of writing
from scratch.

We've helped companies like TechCorp and LegalPro achieve 50% faster document
processing and 40% cost reduction. We're live with 50+ lawyers and 3 enterprise clients.

Would you be open to a brief call to discuss how we can help Chiratae Ventures?

Best regards,
Praveen Kumar
Founder, DurgaAI
praveen@durgaai.com
```

**Improvements:**
- All placeholders filled with real info
- Personalized to Chiratae Ventures specifically
- Explains WHY they need it (portfolio value, investment opportunity)
- Professional format
- Clear value proposition
- Specific metrics

---

## Common Questions

**Q: Do I have to use {{why}}?**
A: Yes! That's where the personalization happens. Without it, all emails will be identical.

**Q: Can I have multiple {{why}} in one template?**
A: No, use it once. If you repeat it, the same text will appear in both places.

**Q: What if I don't want ANY AI generation?**
A: Then don't use `{{why}}`. Just use `{{company}}` to replace company names. But you'll lose personalization.

**Q: Can I edit the generated emails before sending?**
A: Yes! After generation, you can click "Edit" on any email to modify it.

**Q: How long is the {{why}} section?**
A: 2-3 sentences (max 60 words). Professional and specific to that company.

---

## Troubleshooting

**Problem:** {{why}} section is too generic

**Solution:** Add more details in the CSV "Details" column. The AI uses this to personalize!

---

**Problem:** AI didn't replace {{why}}

**Solution:** Make sure you selected "Custom Template" email style

---

**Problem:** Email still has [Your Name] placeholders

**Solution:** Replace those manually in your template! {{company}} and {{why}} are the only auto-replaced placeholders.

---

## Ready to Launch!

1. **Select:** Custom Template style
2. **Write:** Your email with `{{why}}` placeholder
3. **Upload:** CSV with detailed company info
4. **Generate:** Let AI personalize for each company
5. **Review:** Edit if needed
6. **Send:** Launch your campaign!

That's it! Simple, professional, personalized. 🚀
