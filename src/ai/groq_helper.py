"""
Groq AI Integration for Email Writing Assistance
Provides intelligent email enhancement, company analysis, and conversational support
"""

import os
from typing import Dict, List, Optional
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GroqAssistant:
    """AI Assistant powered by Groq for email campaign support"""

    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        self.model = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
        self.temperature = float(os.getenv('AI_TEMPERATURE', '0.7'))
        self.max_tokens = int(os.getenv('MAX_AI_TOKENS', '1024'))

        if not self.api_key or self.api_key == 'your_groq_api_key_here':
            raise ValueError("GROQ_API_KEY not set in .env file. Get your free key at: https://console.groq.com/")

        self.client = Groq(api_key=self.api_key)
        self.conversation_history = []

    def chat(self, user_message: str, context: Optional[Dict] = None) -> str:
        """
        General chat with AI assistant

        Args:
            user_message: User's question or request
            context: Optional context about current page/email being edited

        Returns:
            AI assistant's response
        """
        # Build system message with context
        system_message = self._build_system_message(context)

        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_message})

        # Build messages for API call
        messages = [{"role": "system", "content": system_message}] + self.conversation_history[-10:]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            assistant_response = response.choices[0].message.content

            # Add to history
            self.conversation_history.append({"role": "assistant", "content": assistant_response})

            return assistant_response

        except Exception as e:
            return f"Error communicating with AI: {str(e)}"

    def enhance_email(self, email_body: str, company_name: str, audience_type: str = "VCs") -> Dict[str, str]:
        """
        Enhance an existing email with better language, personalization, and clarity

        Args:
            email_body: Original email text
            company_name: Target company name
            audience_type: Type of audience (VCs, Clients, Partners, etc.)

        Returns:
            Dict with 'subject' and 'body' improved versions
        """
        prompt = f"""You are an expert cold email writer. Improve the following email for a {audience_type} audience targeting {company_name}.

Requirements:
- Keep it concise (100-150 words)
- Personalize for {company_name}
- Make the value proposition crystal clear
- Use engaging, professional language
- Include a clear call-to-action
- Avoid buzzwords and fluff

Original email:
{email_body}

Return ONLY the improved email body, no explanations."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a cold email expert focused on high-converting, personalized outreach."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            improved_body = response.choices[0].message.content.strip()

            # Generate matching subject line
            subject = self.generate_subject_line(company_name, audience_type, improved_body)

            return {
                "subject": subject,
                "body": improved_body
            }

        except Exception as e:
            return {
                "subject": f"Partnership Opportunity with {company_name}",
                "body": email_body  # Return original on error
            }

    def generate_subject_line(self, company_name: str, audience_type: str, email_body: str = "") -> str:
        """
        Generate compelling subject line

        Args:
            company_name: Target company
            audience_type: Audience type
            email_body: Optional email body for context

        Returns:
            Subject line string
        """
        prompt = f"""Generate a short, compelling email subject line (5-8 words) for a cold email to {company_name} ({audience_type}).

Email preview:
{email_body[:200]}...

Requirements:
- Personalized to {company_name}
- Creates curiosity
- Professional, not spammy
- No emojis or ALL CAPS

Return ONLY the subject line, no quotes or explanations."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=50
            )

            subject = response.choices[0].message.content.strip().strip('"\'')
            return subject

        except Exception as e:
            return f"Partnership Opportunity - {company_name}"

    def analyze_company(self, company_data: Dict) -> Dict:
        """
        Analyze company details to provide insights for personalization

        Args:
            company_data: Dict with keys like 'Company', 'Details', 'Website', etc.

        Returns:
            Analysis dict with focus_areas, tone_suggestion, talking_points
        """
        company_name = company_data.get('Company', 'Unknown Company')
        details = company_data.get('Details', '')

        prompt = f"""Analyze this company for cold email personalization:

Company: {company_name}
Details: {details[:500]}

Provide:
1. Key focus areas (3-4 topics they care about)
2. Recommended email tone (formal/friendly/innovative)
3. Potential talking points for outreach

Format as JSON:
{{
    "focus_areas": ["area1", "area2", "area3"],
    "tone": "formal/friendly/innovative",
    "talking_points": ["point1", "point2", "point3"]
}}

Return ONLY valid JSON."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=300
            )

            import json
            analysis = json.loads(response.choices[0].message.content.strip())
            return analysis

        except Exception as e:
            # Fallback analysis
            return {
                "focus_areas": ["innovation", "growth", "partnership"],
                "tone": "professional",
                "talking_points": [
                    f"Potential synergy with {company_name}",
                    "Innovative solution for their industry",
                    "Proven track record and results"
                ]
            }

    def generate_personalized_from_csv(self, csv_row: Dict, campaign_info: Dict, email_template: str = None) -> Dict[str, str]:
        """
        Generate highly personalized email using CSV company details

        Args:
            csv_row: Row from CSV with Email, Phone, Company_Name, Company_Description,
                    Industry, Services/Products, Company_Size
            campaign_info: Campaign details from document parser (company, product, value_props,
                         metrics, goal, description)
            email_template: Optional email template with {{why}} placeholder

        Returns:
            Dict with 'subject' and 'body' personalized for this specific company
        """
        # Extract CSV company details
        recipient_company = csv_row.get('Company_Name', csv_row.get('Company', 'Unknown Company'))
        company_description = csv_row.get('Company_Description', '')
        industry = csv_row.get('Industry', '')
        services_products = csv_row.get('Services/Products', csv_row.get('Services', ''))
        company_size = csv_row.get('Company_Size', '')

        # Extract campaign info
        our_company = campaign_info.get('company', '')
        our_product = campaign_info.get('product', '')
        value_props = campaign_info.get('value_props', '')
        metrics = campaign_info.get('metrics', '')
        goal = campaign_info.get('goal', '')
        our_description = campaign_info.get('description', '')

        # Check if we have a template to use
        if email_template and '{{why}}' in email_template:
            # Determine the messaging based on the campaign goal
            is_funding_request = 'fund' in goal.lower() or 'invest' in goal.lower() or 'vc' in goal.lower() or 'seed' in goal.lower()

            if is_funding_request:
                # For VCs/Investors: Focus on investment opportunity, not product benefits
                prompt = f"""Write an investment pitch email to {recipient_company} with EXACTLY 3 PARAGRAPHS following this structure:

OUR COMPANY:
- Company: {our_company}
- Product: {our_product}
- Description: {our_description}
- Value Props: {value_props}
- Traction: {metrics}

TARGET INVESTOR:
- Firm: {recipient_company}
- Focus: {company_description}
- Sectors: {industry}

GREETING:
"Dear {recipient_company} Team,"

PARAGRAPH 1 - INTRO + PROBLEM + SOLUTION (90-100 words, 4-5 sentences):
Combine these elements in natural flow:
- Start: "I'm reaching out on behalf of {our_company}, where we are building {our_product} — an AI-powered legal assistant for Indian law and lawyers."
- Mission: "Founded by Praveen Pandiyan, our mission is to [use: {our_description} and {value_props}]."
- Problem: "India's legal sector faces inefficiency: over [realistic number] lawyers spend [percentage]% of time on [specific tasks from context]."
- Solution: "{our_product} directly addresses this by automating tasks such as [specific examples], enabling lawyers to [benefits]."

This paragraph flows from intro → problem → solution in one cohesive narrative.

PARAGRAPH 2 - INVESTMENT FIT + TRACTION (80-90 words, 3-4 sentences):
- Start: "Given {recipient_company}'s focus on [extract from: {company_description}], we believe {our_product} is a strong fit for your investment thesis in the [domain]."
- Continue with traction sentence: "[Use metrics: {metrics}] MVP ready, tested by practicing lawyers in Tamil Nadu, law firms showing interest in private deployments, colleges in talks for pilot programs."

This paragraph combines WHY THIS VC + OUR TRACTION in a natural flow.

PARAGRAPH 3 - CALL TO ACTION (30-35 words, 2 sentences):
- "We would love the opportunity to discuss potential investment collaboration and explore how {recipient_company} can help accelerate our next stage of growth."
- "Please feel free to contact us at your convenience for further updates or to schedule a meeting."

CLOSING:
"Best regards,"

CRITICAL RULES:
1. Write EXACTLY 3 paragraphs - separated by blank lines
2. Paragraph 1: Intro + Problem + Solution (flowing together naturally)
3. Paragraph 2: Why this VC + Traction
4. Paragraph 3: Call to action
5. Natural, conversational flow - not segmented or bullet-style
6. Professional, warm, confident tone
7. Total: 200-230 words
8. End with ONLY "Best regards," - nothing after

Return the complete email from greeting to "Best regards," - do NOT add signatures or extra text."""
            else:
                # For regular customers: Focus on product benefits
                prompt = f"""Generate a SHORT personalized explanation (2-3 sentences, max 50 words) of why {recipient_company} specifically would benefit from {our_product}.

YOUR COMPANY & PRODUCT:
{our_company} - {our_description}
Product: {our_product}
Value Props: {value_props}
Metrics: {metrics}
Goal: {goal}

TARGET COMPANY (from web research):
Company: {recipient_company}
Description: {company_description}
Industry: {industry}
Services/Products: {services_products}
Company Size: {company_size}

CRITICAL REQUIREMENTS:
- Only 2-3 sentences (max 50 words)
- Be SPECIFIC to {recipient_company}'s industry and business
- Reference their {industry} sector and {services_products} context
- Explain how {our_product} solves THEIR specific pain points
- Direct, confident, no fluff

Return ONLY the personalized WHY statement, nothing else."""

        else:
            # Generate complete email
            prompt = f"""Write a highly personalized cold email based on detailed company research.

YOUR COMPANY:
{our_company}
Product: {our_product}
Value Props: {value_props}
Metrics: {metrics}
Goal: {goal}
Description: {our_description}

TARGET COMPANY (from web research):
Company: {recipient_company}
Description: {company_description}
Industry: {industry}
Services/Products: {services_products}
Company Size: {company_size}

CRITICAL REQUIREMENTS:
1. Analyze {recipient_company}'s industry, services, and size to identify specific pain points
2. Connect YOUR product's value props to THEIR specific business context
3. Reference their industry ({industry}) and services ({services_products}) naturally
4. Use company size ({company_size}) to tailor the pitch appropriately
5. Make it feel like you researched them specifically - NOT a template
6. Keep it concise (100-150 words)
7. Include clear CTA related to your goal: {goal}

STRUCTURE:
1. Opening with specific reference to their business/industry
2. Why YOUR solution is relevant to THEIR specific context
3. Brief value prop + metrics that matter to them
4. Clear next step

TONE: Professional, researched, specific (not generic)

Return ONLY the email body, no subject line."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at writing hyper-personalized cold emails using company research data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=600 if not email_template else 200
            )

            why_statement = response.choices[0].message.content.strip()

            # If template provided, use it
            if email_template and '{{why}}' in email_template:
                body = email_template.replace('{{company}}', recipient_company)
                body = body.replace('{{why}}', why_statement)
                # Replace any other placeholders
                body = body.replace('{{product}}', our_product)
                body = body.replace('{{value_props}}', value_props)
                body = body.replace('{{metrics}}', metrics)
            else:
                body = why_statement

            # Add contact signature if this is a funding request
            is_funding_request = 'fund' in goal.lower() or 'invest' in goal.lower() or 'vc' in goal.lower() or 'seed' in goal.lower()
            if is_funding_request:
                # Extract founder/contact info from campaign_info or csv_row
                founder_name = campaign_info.get('founder', csv_row.get('Founder', 'Praveen Pandiyan'))
                contact_phone = campaign_info.get('contact_phone', csv_row.get('Contact_Phone', '+91 7358006064'))
                website = campaign_info.get('website', csv_row.get('Website', 'https://evolverobot.in/ & https://durgaai.com/'))

                # Aggressively clean the body - remove everything after "Warm regards," or "Best regards,"
                import re
                # Find the closing phrase
                for closing in ["Warm regards,", "Best regards,", "Regards,"]:
                    if closing in body:
                        # Split and keep only up to the closing
                        parts = body.split(closing)
                        body = parts[0].strip() + "\n\n" + closing
                        break

                # Also remove common patterns that appear after regards
                body = re.sub(r'(Warm regards,|Best regards,|Regards,)\s*.*?(Founder|CEO|building|Founded by).*', r'\1', body, flags=re.DOTALL | re.IGNORECASE)

                # Ensure it ends with just the closing
                for closing in ["Warm regards,", "Best regards,", "Regards,"]:
                    if closing in body and not body.strip().endswith(closing):
                        body = body.split(closing)[0].strip() + "\n\n" + closing

                # Add clean signature with just name, phone, and website (NO title or company)
                signature = f"\n{founder_name}\n📞 Phone: {contact_phone}\n🌐 Website: {website}"

                body += signature

            # Generate matching subject line
            subject_prompt = f"""Generate a personalized subject line (5-8 words) for this cold email to {recipient_company}.

Their context: {industry} company, {company_size}, focused on {services_products}
Our goal: {goal}
Email preview: {body[:200]}

Requirements:
- Reference their industry or business naturally
- Create curiosity
- Professional, not spammy
- No emojis or ALL CAPS

Return ONLY the subject line, no quotes."""

            subject_response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": subject_prompt}],
                temperature=0.8,
                max_tokens=50
            )

            subject = subject_response.choices[0].message.content.strip().strip('"\'')

            return {
                "subject": subject,
                "body": body,
                "personalization_data": {
                    "company": recipient_company,
                    "industry": industry,
                    "company_size": company_size
                },
                "why_analysis": why_statement if email_template else None
            }

        except Exception as e:
            # Fallback with basic personalization
            fallback_body = f"""Dear {recipient_company} team,

I noticed {recipient_company} operates in {industry}. {our_description}

{value_props}

{metrics}

{goal}

Would you be open to a brief conversation?

Best regards"""

            return {
                "subject": f"{our_company} + {recipient_company}: {goal}",
                "body": fallback_body
            }

    def generate_cold_email(self, company_data: Dict, product_info: str, audience_type: str = "VCs",
                           subject_template: str = "", message_template: str = "", our_company: str = "",
                           email_style: str = "concise", campaign_goal: str = "") -> Dict[str, str]:
        """
        Generate a complete cold email with personalized analysis

        Args:
            company_data: Company information dict (with Company, Details, Email, etc.)
            product_info: Description of your product/service
            audience_type: Target audience type
            subject_template: Subject line template with {{company}} placeholder
            message_template: Optional message structure with placeholders
            our_company: Your company information

        Returns:
            Dict with 'subject' and 'body'
        """
        company_name = company_data.get('Company', company_data.get('company', 'Unknown Company'))
        details = company_data.get('Details', company_data.get('details', ''))

        # Map campaign goals to context
        goal_context = {
            "vc_funding": "seeking investment from VCs and investors",
            "ai_robotics_sales": "selling AI and robotics services to enterprises",
            "partnership": "establishing strategic partnerships",
            "customer_acquisition": "acquiring new customers",
            "product_launch": "launching a new product"
        }

        goal_message = goal_context.get(campaign_goal, "business development")

        # Step 1: Analyze WHY this company needs the product
        if email_style == "custom":
            # For custom templates: generate SHORT, contextual WHY (2-3 lines max)
            why_prompt = f"""Write 2-3 SHORT lines (max 50 words) explaining why {company_name} specifically needs this product for {goal_message}.

Company: {company_name}
Company Details: {details[:500]}

Product: {product_info}
Campaign Goal: {goal_message}

CRITICAL REQUIREMENTS:
- ONLY 2-3 lines (max 50 words total)
- Match the user's email tone (concise, direct, factual)
- Be SPECIFIC to {company_name}'s context
- Reference their actual business/portfolio/focus
- NO generic statements
- NO fluff or buzzwords
- Direct and confident

EXAMPLE (adapt to this company):
"{company_name}'s portfolio in [their sector] makes this relevant. Your [specific area] investments could benefit from proven economics."

OR

"Given your focus on [their area], the India opportunity is 10x. Perfect timing for [their investment thesis]."

Write ONLY 2-3 contextual lines now:"""
        else:
            # For AI-generated styles: more detailed analysis
            why_prompt = f"""Analyze this company and explain in 2-3 sentences WHY they specifically would benefit from this product.

Company: {company_name}
Company Details: {details[:500]}

Product: {product_info}

Write ONLY 2-3 sentences explaining why {company_name} specifically needs this product based on their background/details. Be specific and reference their actual business context."""

        try:
            # Get the WHY analysis
            why_response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing companies and identifying product-market fit."},
                    {"role": "user", "content": why_prompt}
                ],
                temperature=0.6,
                max_tokens=200
            )

            why_they_need_it = why_response.choices[0].message.content.strip()

            # Step 2: Generate the complete email
            if email_style == "custom" and message_template:
                # Custom template: Only generate WHY, insert into user's template
                body = message_template.replace('{{company}}', company_name)
                body = body.replace('{{why}}', why_they_need_it)
                body = body.replace('{{product}}', product_info)
                body = body.replace('{{our_company}}', our_company)

                # Generate subject if template provided
                if subject_template:
                    subject = subject_template.replace('{{company}}', company_name)
                else:
                    subject = self.generate_subject_line(company_name, audience_type, body)

                return {
                    "subject": subject,
                    "body": body,
                    "why_analysis": why_they_need_it
                }

            elif message_template:
                # Use template structure with AI generation
                email_prompt = f"""Fill in this email template with the provided information:

Template:
{message_template}

Fill these placeholders:
- {{{{company}}}}: {company_name}
- {{{{why}}}}: {why_they_need_it}
- {{{{product}}}}: {product_info}
- {{{{our_company}}}}: {our_company}

Requirements:
- Maintain professional tone
- Keep it concise (100-150 words)
- Make it compelling and personalized
- Include clear call-to-action

Return ONLY the filled email body."""

            elif email_style == "concise":
                # Concise VC pitch style (Durga AI format)
                email_prompt = f"""Write a concise, punchy cold email to {company_name} in this EXACT structure:

REQUIRED STRUCTURE:
1. Problem statement (1-2 sentences: why existing solutions failed)
2. AI solution (2-3 sentences: how AI changed the economics/game)
3. Traction (2-3 short sentences: live, customers, revenue, early metrics)
4. Market validation (1-2 sentences: proof this works elsewhere, market size)
5. Urgency (1 sentence: timing/window)
6. Vision (1 sentence: bigger picture)
7. CTA: "Worth a call?"
8. Sign off with founder name

CONTEXT:
- Target company: {company_name}
- Their context: {details[:300]}
- Product: {product_info}
- Our company: {our_company}

STYLE REQUIREMENTS:
- Short, punchy sentences. No fluff.
- Start sentences directly. No "We believe" or "Our mission"
- Use active voice. State facts.
- Max 150 words total
- Each sentence = new line for readability
- No buzzwords or jargon
- Confidence, not arrogance

EXAMPLE STRUCTURE (adapt to our product):
[Problem statement]

AI changed this. [How AI solves it]. [Economics]. [Outcome].

We're live. [Metric]. [Metric]. [Metric].

[Validation] proved this in [market]. [Our market comparison].

[Timing urgency].

[Vision statement].

Worth a call?

[Name]
[Title], [Company]

Return ONLY the email body in this format."""

            else:
                # Generate full email from scratch (standard style)
                email_prompt = f"""Write a compelling cold email for {audience_type} to {company_name}.

STRUCTURE THE EMAIL WITH THESE SECTIONS:

1. Opening greeting to {company_name}

2. WHY {company_name} NEEDS THIS:
{why_they_need_it}

3. PRODUCT DETAILS:
{product_info}

4. ABOUT US:
{our_company}

5. Clear call-to-action

Requirements:
- 100-150 words total
- Professional yet warm tone
- Specific to {company_name} (not generic)
- Strong value proposition
- Compelling CTA

Return ONLY the email body."""

            email_response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are an expert at writing high-converting cold emails for {audience_type}."},
                    {"role": "user", "content": email_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            body = email_response.choices[0].message.content.strip()

            # Step 3: Generate subject line
            if subject_template:
                subject = subject_template.replace('{{company}}', company_name)
            else:
                subject = self.generate_subject_line(company_name, audience_type, body)

            return {
                "subject": subject,
                "body": body,
                "why_analysis": why_they_need_it  # Include for reference
            }

        except Exception as e:
            # Fallback email
            fallback_body = f"""Dear {company_name} team,

{product_info}

{our_company if our_company else 'We specialize in helping companies like yours achieve their goals.'}

Would you be open to a brief call to discuss how we can help?

Best regards"""

            return {
                "subject": subject_template.replace('{{company}}', company_name) if subject_template else f"Partnership Opportunity for {company_name}",
                "body": fallback_body
            }

    def suggest_improvements(self, email_subject: str, email_body: str) -> List[str]:
        """
        Provide specific improvement suggestions for an email

        Args:
            email_subject: Email subject line
            email_body: Email body text

        Returns:
            List of actionable improvement suggestions
        """
        prompt = f"""Review this cold email and provide 3-5 specific, actionable improvements:

Subject: {email_subject}

Body:
{email_body}

Focus on:
- Personalization opportunities
- Value proposition clarity
- Call-to-action strength
- Length and readability
- Professional tone

Return as a numbered list."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=400
            )

            suggestions_text = response.choices[0].message.content.strip()
            # Parse into list
            suggestions = [s.strip() for s in suggestions_text.split('\n') if s.strip() and any(c.isalpha() for c in s)]

            return suggestions

        except Exception as e:
            return ["Unable to generate suggestions. Please check your API connection."]

    def _build_system_message(self, context: Optional[Dict] = None) -> str:
        """Build system message with optional context"""
        base_message = """You are an AI assistant helping with cold email campaigns. You specialize in:
- Writing compelling, personalized cold emails
- Improving subject lines and email copy
- Analyzing companies for outreach personalization
- Providing email campaign strategy advice

Be concise, actionable, and professional."""

        if context:
            if context.get('page') == 'campaign':
                base_message += "\n\nThe user is currently building an email campaign."
            if context.get('company_name'):
                base_message += f"\n\nCurrent target company: {context['company_name']}"
            if context.get('audience_type'):
                base_message += f"\n\nTarget audience: {context['audience_type']}"

        return base_message

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []


# Global instance
_assistant = None

def get_assistant() -> GroqAssistant:
    """Get or create global assistant instance"""
    global _assistant
    if _assistant is None:
        _assistant = GroqAssistant()
    return _assistant
