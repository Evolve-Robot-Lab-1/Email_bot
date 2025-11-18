# Gmail Campaign Builder V2 - AI-Powered Email Outreach

## New Features in V2

### 1. AI-Powered Chatbot Assistant
- **Right-side floating chatbot** powered by Groq (Llama 3.3 70B)
- Real-time email writing assistance
- Company analysis and personalization suggestions
- Available commands: `/improve`, `/subject`, `/personalize`, `/analyze`

### 2. Enhanced Email Generation
The new system analyzes each company and generates emails with:
- **WHY this specific company needs your product** (AI analyzes company details)
- **Product details and benefits**
- **Your company credentials**
- **Personalized subject lines**

### 3. Modern UI
- Clean, card-based design with Tailwind CSS
- Three main pages: Campaign | Inbox | Analytics
- Real-time progress tracking
- Better CSV data preview and validation

### 4. Unified Inbox
- Fetch Gmail messages
- AI-suggested replies or manual composition
- Thread view with context

### 5. Analytics Dashboard
- Campaign history with charts
- Success/failure tracking
- Export data to CSV

---

## Setup Instructions

### Step 1: Install Dependencies

```bash
cd "/home/evolve/AI PROJECT/Gmail_integeration"
pip install -r requirements.txt
```

### Step 2: Get Groq API Key

1. Visit https://console.groq.com/
2. Sign up for a FREE account
3. Create an API key
4. Copy the key

### Step 3: Configure .env File

Edit the `.env` file and add your Groq API key:

```bash
GROQ_API_KEY=your_groq_api_key_here
```

### Step 4: Gmail Authentication

Make sure you have:
- `credentials.json` - Gmail API credentials (already present)
- `token.json` will be created automatically on first run

### Step 5: Run the Application

```bash
python3 app_v2.py
```

The app will start on: **http://127.0.0.1:5001**

---

## How to Use - Campaign Builder

### 1. Upload Recipients CSV

Your CSV file should have these columns:
- **Email** (required) - recipient email addresses
- **Company** or **Company Name** - company names
- **Details** - company background, description, website content, etc.
- Website, Phone (optional)

Example CSV structure:
```csv
Company,Email,Details
Sequoia Capital,support@sequoiacap.com,Leading VC firm investing in AI and deep tech startups...
Accel Partners,info@accel.com,Early stage VC with focus on SaaS and enterprise software...
```

### 2. Fill in Campaign Details

**Target Audience:** Choose from VCs, Clients, Partners, etc.

**Product/Service Description:**
```
AI-powered business automation platform that helps companies streamline operations,
reduce costs by 40%, and increase productivity through intelligent workflow automation.
```

**Your Company Details:**
```
TechCorp Inc. - Leading AI solutions provider with 50+ enterprise clients including
Fortune 500 companies. We've helped businesses save $10M+ through automation.
```

**Subject Template:**
```
Partnership Opportunity for {{company}}
```
(The `{{company}}` will be replaced with actual company name)

**Message Template (Optional):**
Leave empty for full AI generation, or provide structure:
```
Dear {{company}} team,

{{why}}

Our product: {{product}}

About us: {{our_company}}

Would you be open to a brief call?

Best regards
```

### 3. Generate AI Emails

Click **"Generate AI Emails"** and the system will:
1. Analyze each company's details
2. Determine WHY they specifically need your product
3. Generate personalized email with:
   - Why THEY need it (based on their business)
   - Your product benefits
   - Your company credentials
   - Compelling call-to-action

### 4. Review & Edit

- Preview all generated emails
- Click "Edit" on any email to refine
- Use AI chatbot for suggestions (click chat button bottom-right)
- Type `/improve` in chat to enhance current email

### 5. Launch Campaign

- Click "Launch Campaign"
- Emails sent with 2-minute intervals (to avoid spam filters)
- Watch real-time progress
- Pause/Resume/Cancel anytime

---

## Email Generation Logic

### What the AI Does:

1. **Company Analysis:**
   - Reads company details from CSV
   - Identifies their industry, focus areas, challenges
   - Determines their business context

2. **WHY Analysis (Key Feature!):**
   - AI explains specifically WHY this company needs your product
   - Based on THEIR actual business context
   - Not generic - highly personalized

3. **Email Structure:**
   ```
   Dear [Company] team,

   [WHY THEY NEED IT - Personalized analysis]
   Based on your focus on [their industry/challenge], our solution
   would help you [specific benefit].

   [PRODUCT DETAILS]
   Our platform offers [features, benefits, results]

   [YOUR COMPANY]
   We've helped [social proof, credentials]

   [CALL TO ACTION]
   Would you be open to a brief call?
   ```

### Example Output:

**To: Sequoia Capital**

Subject: Partnership Opportunity for Sequoia Capital

Body:
```
Dear Sequoia Capital team,

Given your extensive portfolio in AI and deep tech startups, our
automation platform could significantly benefit your portfolio companies.
We've seen 40% operational cost reduction across similar VC-backed startups.

Our AI-powered platform streamlines business operations through intelligent
workflow automation, helping companies scale faster while reducing overhead.
Key features include automated data processing, smart decision engines, and
real-time analytics.

TechCorp Inc. has partnered with 50+ enterprises including Fortune 500
companies, collectively saving over $10M through automation. Our solutions
are specifically designed for high-growth technology companies.

Would you be open to a brief call to explore how we can add value to your
portfolio companies?

Best regards
```

---

## Using the AI Chatbot

### Open the Chatbot
Click the floating blue button (bottom-right corner)

### Quick Commands:

- **/improve** - Enhance the current email you're editing
- **/subject** - Generate 3 alternative subject lines
- **/personalize** - Analyze company for personalization insights
- **/help** - Show all commands

### Natural Chat:
Just type questions like:
- "How can I make this subject line better?"
- "What should I emphasize for VC firms?"
- "Is this email too long?"

---

## Inbox Features

1. **Fetch Emails:** Load your Gmail inbox
2. **View Details:** Click any email to read full content
3. **AI Reply:** Generate intelligent reply with context
4. **Manual Reply:** Write your own reply
5. **Search & Filter:** Find specific emails quickly

---

## Analytics Dashboard

Track your campaign performance:
- Total emails sent
- Success/failure rates
- Campaign history
- Detailed progress logs
- Export data to CSV

---

## Tips for Best Results

### 1. Provide Detailed Company Information
The better the company details in your CSV, the better the personalization:
- Company background
- Their focus areas
- Recent news/achievements
- Technologies they use

### 2. Clear Product Description
Include:
- What it does
- Key benefits (quantifiable)
- Who it's for
- Unique value proposition

### 3. Strong Company Credentials
Add social proof:
- Number of clients
- Results achieved
- Notable customers
- Industry recognition

### 4. Test with Small Batch First
- Upload 5-10 companies first
- Review AI-generated emails
- Refine your inputs
- Then scale to larger batches

### 5. Use the AI Assistant
- Ask for improvements before sending
- Get suggestions for better personalization
- Refine subject lines

---

## Troubleshooting

### "GROQ_API_KEY not set" Error
1. Make sure you edited `.env` file
2. Replace `your_groq_api_key_here` with your actual key
3. Restart the application

### Gmail Authentication Issues
1. Make sure `credentials.json` exists
2. Delete `token.json` if present
3. Restart app - browser will open for authentication

### Emails Not Sending
1. Check Gmail API quotas (500/day for free tier)
2. Verify internet connection
3. Check terminal for error messages

### AI Generation Slow
- Groq is fast, but generating 100 emails takes ~5-10 minutes
- Each email requires 2 AI calls (WHY analysis + email generation)
- Be patient or reduce batch size

---

## Port Configuration

- **Old App (v1):** http://127.0.0.1:3000 (still works)
- **New App (v2):** http://127.0.0.1:5001

Both can run simultaneously!

---

## Support & Feedback

For issues or questions:
1. Check terminal output for error messages
2. Verify .env configuration
3. Test with sample CSV (companies.csv included)

---

## Next Steps

1. Get your Groq API key
2. Update .env file
3. Prepare your company list CSV
4. Launch the app: `python3 app_v2.py`
5. Open http://127.0.0.1:5001
6. Start your first campaign!

**Happy Campaigning!** 🚀
