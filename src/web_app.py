from __future__ import annotations
import os
import base64
from typing import List, Optional

from flask import Flask, render_template, request, redirect, url_for, flash
import webbrowser
import threading
import re
from werkzeug.utils import secure_filename
import pandas as pd
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ['https://mail.google.com/']
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'.csv', '.xlsx'}


app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def gmail_service():
    creds = None
    token_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'token.json')
    credentials_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'credentials.json')

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                raise RuntimeError("Missing credentials.json next to project root")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token_file:
            token_file.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)


def allowed_file(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXTENSIONS


def _read_dataframe(path: str) -> Optional[pd.DataFrame]:
    _, ext = os.path.splitext(path.lower())
    try:
        if ext == '.csv':
            # Try multiple encodings and delimiter inference for CSVs
            for enc in ('utf-8', 'utf-8-sig', 'latin-1', 'cp1252'):
                try:
                    return pd.read_csv(path, encoding=enc, sep=None, engine='python', on_bad_lines='skip')
                except Exception:
                    continue
            # Fallback delimiters
            for delim in (',', ';', '\t', '|'):
                for enc in ('utf-8', 'utf-8-sig', 'latin-1', 'cp1252'):
                    try:
                        return pd.read_csv(path, encoding=enc, delimiter=delim, engine='python', on_bad_lines='skip')
                    except Exception:
                        continue
            return None
        if ext == '.xlsx':
            return pd.read_excel(path)
    except Exception:
        return None
    return None


def extract_emails_from_file(path: str) -> List[str]:
    df = _read_dataframe(path)
    if df is None or df.empty:
        return []

    # 1) Exact header match candidates
    header_candidates = {'email', 'emails', 'e-mail', 'mail', 'email id', 'email_id', 'work email', 'business email'}
    for col in df.columns:
        if str(col).strip().lower() in header_candidates:
            series = df[col]
            emails = _extract_emails_from_series(series)
            if emails:
                return list(dict.fromkeys(emails))

    # 2) Heuristic: choose column with most email-like values
    best_col = None
    best_count = -1
    for col in df.columns:
        series = df[col].dropna().astype(str)
        count = sum(1 for v in series if _extract_emails_from_text(v))
        if count > best_count:
            best_count = count
            best_col = col
    if best_col is not None and best_count > 0:
        series = df[best_col].dropna().astype(str)
        emails = []
        for v in series:
            emails.extend(_extract_emails_from_text(v))
        return list(dict.fromkeys(emails))

    # 3) Fallback: scan entire frame for any email-like tokens
    emails: List[str] = []
    for col in df.columns:
        series = df[col].dropna().astype(str)
        for v in series:
            emails.extend(_extract_emails_from_text(v))
    return list(dict.fromkeys(emails))


def extract_company_data_from_file(path: str) -> List[dict]:
    """Extract company data including names, emails, and details content"""
    df = _read_dataframe(path)
    if df is None or df.empty:
        return []

    companies = []
    
    # Find email column
    email_col = None
    header_candidates = {'email', 'emails', 'e-mail', 'mail', 'email id', 'email_id', 'work email', 'business email'}
    for col in df.columns:
        if str(col).strip().lower() in header_candidates:
            email_col = col
            break
    
    if not email_col:
        # Find column with most emails
        best_count = -1
        for col in df.columns:
            series = df[col].dropna().astype(str)
            count = sum(1 for v in series if _extract_emails_from_text(v))
            if count > best_count:
                best_count = count
                email_col = col

    # Find company name column
    company_col = None
    company_candidates = {'company', 'name', 'company name', 'organization', 'org'}
    for col in df.columns:
        if str(col).strip().lower() in company_candidates:
            company_col = col
            break
    
    if not company_col:
        # Use first column as company name
        company_col = df.columns[0]

    # Find details column (look for content with company information)
    details_col = None
    for col in df.columns:
        series = df[col].dropna().astype(str)
        if any(len(str(v).strip()) > 50 for v in series):  # Look for columns with substantial content
            details_col = col
            break

    # Extract data row by row
    for _, row in df.iterrows():
        email = None
        if email_col and email_col in row:
            emails = _extract_emails_from_text(str(row[email_col]))
            if emails:
                email = emails[0]  # Take first email found
        
        company_name = None
        if company_col and company_col in row:
            company_name = str(row[company_col]).strip()
        
        details_content = None
        if details_col and details_col in row:
            details_content = str(row[details_col]).strip()
            if len(details_content) < 20:  # Skip very short details
                details_content = None
        
        if email and company_name:
            companies.append({
                'email': email,
                'company': company_name,
                'details_content': details_content
            })
    
    return companies


def generate_cold_email(company_data: dict, product_description: str = "AI agent and robotics solutions") -> tuple[str, str]:
    """Generate cold email subject and body based on company details content"""
    company_name = company_data.get('company', 'your company')
    details_content = company_data.get('details_content', '')
    
    # Analyze company details to extract key information
    company_analysis = _analyze_company_details(company_name, details_content)
    
    # Generate subject based on company analysis
    subjects = [
        f"{product_description} for {company_name}",
        f"Transform {company_name} with {product_description}",
        f"Next-Gen {product_description} for {company_name}",
        f"Automate {company_name}'s Operations with {product_description}",
        f"{product_description} Tailored for {company_name}",
        f"Revolutionize {company_name} with {product_description}"
    ]
    subject = subjects[hash(company_name) % len(subjects)]
    
    # Generate personalized body based on company details analysis
    body = _generate_personalized_body_from_details(company_name, company_analysis, product_description, details_content)
    
    return subject, body


def _analyze_company_details(company_name: str, details_content: str) -> dict:
    """Analyze company details content to extract key information"""
    if not details_content:
        return {
            'industry': 'general',
            'size': 'medium',
            'focus_areas': [],
            'key_phrases': [],
            'company_description': ''
        }
    
    content_lower = details_content.lower()
    
    # Extract industry from content
    industry = 'general'
    industry_keywords = {
        'technology': ['tech', 'software', 'digital', 'ai', 'data', 'cloud', 'cyber', 'innovation', 'platform'],
        'finance': ['finance', 'bank', 'investment', 'capital', 'venture', 'fund', 'financial', 'wealth', 'portfolio'],
        'healthcare': ['health', 'medical', 'pharma', 'biotech', 'hospital', 'clinic', 'care', 'patient'],
        'manufacturing': ['manufacturing', 'production', 'factory', 'industrial', 'machinery', 'automotive'],
        'retail': ['retail', 'commerce', 'ecommerce', 'shopping', 'consumer', 'brand', 'marketplace'],
        'logistics': ['logistics', 'shipping', 'transport', 'supply', 'warehouse', 'distribution', 'delivery'],
        'education': ['education', 'university', 'college', 'school', 'learning', 'academy', 'institute'],
        'consulting': ['consulting', 'advisory', 'services', 'solutions', 'strategy', 'management']
    }
    
    for ind, keywords in industry_keywords.items():
        if any(keyword in content_lower for keyword in keywords):
            industry = ind
            break
    
    # Extract company size indicators
    size = 'medium'
    large_indicators = ['unicorn', 'billion', 'million', 'global', 'international', 'enterprise', 'corporation']
    small_indicators = ['startup', 'small', 'local', 'emerging']
    
    if any(indicator in content_lower for indicator in large_indicators):
        size = 'large'
    elif any(indicator in content_lower for indicator in small_indicators):
        size = 'small'
    
    # Extract key phrases and focus areas
    key_phrases = []
    focus_areas = []
    
    # Look for specific business focus areas
    focus_keywords = {
        'innovation': ['innovation', 'innovative', 'cutting-edge', 'advanced'],
        'growth': ['growth', 'scaling', 'expansion', 'development'],
        'automation': ['automation', 'automate', 'efficiency', 'streamline'],
        'digital': ['digital', 'digitalization', 'digital transformation'],
        'ai': ['artificial intelligence', 'ai', 'machine learning', 'ml'],
        'data': ['data', 'analytics', 'insights', 'intelligence'],
        'customer': ['customer', 'client', 'user experience', 'satisfaction'],
        'operations': ['operations', 'operational', 'process', 'workflow']
    }
    
    for area, keywords in focus_keywords.items():
        if any(keyword in content_lower for keyword in keywords):
            focus_areas.append(area)
    
    # Extract company description (first 200 characters)
    company_description = details_content[:200] + "..." if len(details_content) > 200 else details_content
    
    return {
        'industry': industry,
        'size': size,
        'focus_areas': focus_areas,
        'key_phrases': key_phrases,
        'company_description': company_description
    }


def _analyze_company_industry(company_name: str, details_link: str) -> str:
    """Analyze company name and details to determine industry"""
    company_lower = company_name.lower()
    
    # Industry keywords mapping
    industry_keywords = {
        'technology': ['tech', 'software', 'digital', 'ai', 'data', 'cloud', 'cyber', 'tech', 'innovation'],
        'manufacturing': ['manufacturing', 'production', 'factory', 'industrial', 'machinery', 'automotive', 'electronics'],
        'finance': ['finance', 'bank', 'investment', 'capital', 'venture', 'fund', 'financial', 'wealth'],
        'healthcare': ['health', 'medical', 'pharma', 'biotech', 'hospital', 'clinic', 'care'],
        'retail': ['retail', 'commerce', 'ecommerce', 'shopping', 'consumer', 'brand', 'marketplace'],
        'logistics': ['logistics', 'shipping', 'transport', 'supply', 'warehouse', 'distribution', 'delivery'],
        'energy': ['energy', 'power', 'oil', 'gas', 'renewable', 'solar', 'wind', 'electric'],
        'education': ['education', 'university', 'college', 'school', 'learning', 'academy', 'institute'],
        'real_estate': ['real estate', 'property', 'construction', 'development', 'housing', 'building'],
        'consulting': ['consulting', 'advisory', 'services', 'solutions', 'strategy', 'management']
    }
    
    # Check company name for industry indicators
    for industry, keywords in industry_keywords.items():
        if any(keyword in company_lower for keyword in keywords):
            return industry
    
    # If details link contains company_details, try to infer from filename
    if 'company_details' in details_link.lower():
        # Extract potential industry info from the link
        if any(keyword in details_link.lower() for keyword in ['tech', 'software']):
            return 'technology'
        elif any(keyword in details_link.lower() for keyword in ['manufacturing', 'industrial']):
            return 'manufacturing'
        elif any(keyword in details_link.lower() for keyword in ['finance', 'bank']):
            return 'finance'
    
    return 'general'


def _analyze_company_size(company_name: str) -> str:
    """Analyze company name to estimate size"""
    company_lower = company_name.lower()
    
    # Large company indicators
    large_indicators = ['corp', 'corporation', 'inc', 'incorporated', 'ltd', 'limited', 'group', 'holdings', 'enterprises']
    medium_indicators = ['solutions', 'systems', 'services', 'technologies', 'ventures', 'partners']
    
    if any(indicator in company_lower for indicator in large_indicators):
        return 'large'
    elif any(indicator in company_lower for indicator in medium_indicators):
        return 'medium'
    else:
        return 'small'


def _generate_personalized_body_from_details(company_name: str, company_analysis: dict, product_description: str, details_content: str) -> str:
    """Generate unique, varied email body based on detailed company analysis - 100-150 words"""
    
    industry = company_analysis.get('industry', 'general')
    size = company_analysis.get('size', 'medium')
    focus_areas = company_analysis.get('focus_areas', [])
    company_description = company_analysis.get('company_description', '')
    
    # Extract key company information from details
    company_focus = _extract_company_focus(details_content)
    company_mission = _extract_company_mission(details_content)
    company_services = _extract_company_services(details_content)
    company_values = _extract_company_values(details_content)
    company_achievements = _extract_company_achievements(details_content)
    
    # Generate different email styles based on company characteristics
    email_style = _determine_email_style(company_focus, company_size=size, company_values=company_values, company_name=company_name)
    
    # Generate unique email based on style
    if email_style == "achievement_focused":
        body = _generate_achievement_focused_email(company_name, company_focus, company_achievements, product_description)
    elif email_style == "mission_driven":
        body = _generate_mission_driven_email(company_name, company_mission, company_values, product_description)
    elif email_style == "innovation_forward":
        body = _generate_innovation_forward_email(company_name, company_focus, company_services, product_description)
    elif email_style == "partnership_oriented":
        body = _generate_partnership_oriented_email(company_name, company_focus, industry, product_description)
    elif email_style == "results_focused":
        body = _generate_results_focused_email(company_name, company_focus, company_services, product_description)
    else:
        body = _generate_collaborative_email(company_name, company_focus, company_mission, product_description)
    
    # Ensure the email is 100-150 words
    word_count = len(body.split())
    if word_count < 100:
        # Add more specific details based on company info
        additional_context = _generate_additional_context(company_focus, industry, company_achievements)
        body = f"""{body}

{additional_context}"""
    elif word_count > 150:
        # Trim to fit word limit while maintaining structure
        words = body.split()
        body = ' '.join(words[:150])
        # Ensure it ends properly with founder signature
        if not body.endswith(('[Your Name]', 'regards', 'thanks')):
            body += "\n\nWarm regards,\n[Your Name]"
    
    return body


def _determine_email_style(company_focus: str, company_size: str, company_values: str, company_name: str = "") -> str:
    """Determine the best email style based on company characteristics"""
    
    focus_lower = company_focus.lower()
    values_lower = company_values.lower()
    name_lower = company_name.lower()
    
    # Use company name to determine style if details are limited
    if not company_focus:
        if any(word in name_lower for word in ['sequoia', 'accel', 'matrix', 'nexus']):
            return "achievement_focused"
        elif any(word in name_lower for word in ['pi', 'stellaris', 'inventus']):
            return "innovation_forward"
        elif any(word in name_lower for word in ['chiratae', 'kalaari', 'orios']):
            return "partnership_oriented"
        elif any(word in name_lower for word in ['idg']):
            return "results_focused"
        else:
            return "collaborative"
    
    # Achievement-focused companies (large, established)
    if company_size == 'large' or any(word in focus_lower for word in ['venture', 'capital', 'investment', 'fund']):
        return "achievement_focused"
    
    # Mission-driven companies (non-profits, healthcare, education)
    elif any(word in focus_lower for word in ['health', 'education', 'social', 'care']):
        return "mission_driven"
    
    # Innovation-forward companies (tech, startups)
    elif any(word in focus_lower for word in ['tech', 'software', 'digital', 'innovation', 'startup']):
        return "innovation_forward"
    
    # Partnership-oriented companies (consulting, services)
    elif any(word in focus_lower for word in ['consulting', 'advisory', 'services', 'solutions']):
        return "partnership_oriented"
    
    # Results-focused companies (manufacturing, retail, logistics)
    elif any(word in focus_lower for word in ['manufacturing', 'retail', 'logistics', 'commerce']):
        return "results_focused"
    
    # Default collaborative approach
    else:
        return "collaborative"


def _generate_achievement_focused_email(company_name: str, company_focus: str, company_achievements: str, product_description: str) -> str:
    """Generate founder-style email for established companies like Sequoia, Accel, Matrix"""
    
    # Extract company-specific characteristics
    company_specific = _get_company_specific_info(company_name)
    
    # Generate product-specific content
    product_content = _get_founder_product_content(product_description)
    
    return f"""Dear {company_name} Team,

I'm [Your Name], Founder & CEO of [Your Company].
We're building {product_content['product_name']}, {product_content['product_description']} — without needing an army of analysts.

What makes {product_content['product_name']} different?
It's not just another {product_content['category']} tool. {product_content['product_name']} can:

{product_content['capability_1']}

{product_content['capability_2']}

{product_content['capability_3']}

In short — {product_content['value_proposition']}.

We're building {product_content['vision']} — designed to {product_content['impact']}.

We're now raising a seed round to scale {product_content['product_name']}'s core engine and onboard pilot clients in {product_content['target_sectors']}.

Would you be open to a quick call to explore how {product_content['product_name']} can redefine {product_content['market_disruption']} — and why this space is ripe for disruption?

Warm regards,
[Your Name]"""


def _generate_mission_driven_email(company_name: str, company_mission: str, company_values: str, product_description: str) -> str:
    """Generate founder-style email for purpose-focused companies"""
    
    company_specific = _get_company_specific_info(company_name)
    product_content = _get_founder_product_content(product_description)
    
    return f"""Dear {company_name} Team,

I'm [Your Name], Founder & CEO of [Your Company].
We're developing {product_content['product_name']}, {product_description} — created for organizations that prioritize purpose-driven impact and meaningful innovation.

What makes {product_content['product_name']} transformative?
It's not just another {product_content['category']} platform. {product_content['product_name']} enables:

{product_content['capability_1']}

{product_content['capability_2']}

{product_content['capability_3']}

Fundamentally — {product_content['value_proposition']}.

We're establishing {product_content['vision']} — crafted to {product_content['impact']}.

We're seeking mission-aligned partners for our seed round to scale {product_content['product_name']}'s impact and collaborate with purpose-driven organizations in {product_content['target_sectors']}.

Would you be interested in exploring how {product_content['product_name']} can advance {product_content['market_disruption']} — and discuss how we can create meaningful impact together?

Warm regards,
[Your Name]"""


def _generate_innovation_forward_email(company_name: str, company_focus: str, company_services: str, product_description: str) -> str:
    """Generate founder-style email for tech companies like Pi Ventures, Stellaris"""
    
    company_specific = _get_company_specific_info(company_name)
    product_content = _get_founder_product_content(product_description)
    
    return f"""Dear {company_name} Team,

I'm [Your Name], Founder & CEO of [Your Company].
We're building {product_content['product_name']}, {product_content['product_description']} — designed for companies that push technological boundaries.

What makes {product_content['product_name']} revolutionary?
It's not just another {product_content['category']} solution. {product_content['product_name']} delivers:

{product_content['capability_1']}

{product_content['capability_2']}

{product_content['capability_3']}

In essence — {product_content['value_proposition']}.

We're creating {product_content['vision']} — engineered to {product_content['impact']}.

We're currently raising our seed round to accelerate {product_content['product_name']}'s development and establish partnerships with innovative companies in {product_content['target_sectors']}.

Would you be interested in exploring how {product_content['product_name']} can revolutionize {product_content['market_disruption']} — and why this represents the next frontier in technology?

Best regards,
[Your Name]"""


def _generate_partnership_oriented_email(company_name: str, company_focus: str, industry: str, product_description: str) -> str:
    """Generate founder-style email for companies like Chiratae Ventures, Kalaari"""
    
    company_specific = _get_company_specific_info(company_name)
    product_content = _get_founder_product_content(product_description)
    
    return f"""Dear {company_name} Team,

I'm [Your Name], Founder & CEO of [Your Company].
We're developing {product_content['product_name']}, {product_content['product_description']} — built for forward-thinking organizations that value strategic partnerships.

What sets {product_content['product_name']} apart?
It's not just another {product_content['category']} platform. {product_content['product_name']} provides:

{product_content['capability_1']}

{product_content['capability_2']}

{product_content['capability_3']}

Simply put — {product_content['value_proposition']}.

We're establishing {product_content['vision']} — crafted to {product_content['impact']}.

We're seeking strategic partners for our seed round to scale {product_content['product_name']} and collaborate with industry leaders in {product_content['target_sectors']}.

Would you be open to discussing how {product_content['product_name']} can transform {product_content['market_disruption']} — and explore potential partnership opportunities?

Warm regards,
[Your Name]"""


def _generate_results_focused_email(company_name: str, company_focus: str, company_services: str, product_description: str) -> str:
    """Generate founder-style email for companies like IDG Ventures"""
    
    company_specific = _get_company_specific_info(company_name)
    product_content = _get_founder_product_content(product_description)
    
    return f"""Dear {company_name} Team,

I'm [Your Name], Founder & CEO of [Your Company].
We're launching {product_content['product_name']}, {product_description} — engineered for organizations that prioritize measurable results and data-driven decisions.

What makes {product_content['product_name']} exceptional?
It's not just another {product_content['category']} system. {product_content['product_name']} achieves:

{product_content['capability_1']}

{product_content['capability_2']}

{product_content['capability_3']}

Bottom line — {product_content['value_proposition']}.

We're delivering {product_content['vision']} — optimized to {product_content['impact']}.

We're raising our seed round to expand {product_content['product_name']}'s capabilities and demonstrate proven results with leading companies in {product_content['target_sectors']}.

Would you be interested in reviewing how {product_content['product_name']} can deliver measurable improvements in {product_content['market_disruption']} — with concrete ROI metrics and performance data?

Best regards,
[Your Name]"""


def _generate_collaborative_email(company_name: str, company_focus: str, company_mission: str, product_description: str) -> str:
    """Generate founder-style email for general companies"""
    
    company_specific = _get_company_specific_info(company_name)
    product_content = _get_founder_product_content(product_description)
    
    return f"""Dear {company_name} Team,

I'm [Your Name], Founder & CEO of [Your Company].
We're creating {product_content['product_name']}, {product_description} — designed to complement organizations that value thoughtful strategy and collaborative growth.

What distinguishes {product_content['product_name']}?
It's not just another {product_content['category']} solution. {product_content['product_name']} offers:

{product_content['capability_1']}

{product_content['capability_2']}

{product_content['capability_3']}

In summary — {product_content['value_proposition']}.

We're building {product_content['vision']} — designed to {product_content['impact']}.

We're seeking collaborative partners for our seed round to enhance {product_content['product_name']}'s capabilities and work alongside industry leaders in {product_content['target_sectors']}.

Would you be interested in exploring how {product_content['product_name']} can enhance {product_content['market_disruption']} — and discuss potential collaboration opportunities?

Kind regards,
[Your Name]"""


def _extract_company_values(details_content: str) -> str:
    """Extract company values or principles from details"""
    if not details_content:
        return ""
    
    content_lower = details_content.lower()
    
    # Look for value-related keywords
    value_keywords = [
        'values', 'principles', 'commitment', 'dedicated', 'passionate',
        'excellence', 'integrity', 'innovation', 'quality', 'service'
    ]
    
    for keyword in value_keywords:
        if keyword in content_lower:
            # Extract context around the keyword
            idx = content_lower.find(keyword)
            start = max(0, idx - 30)
            end = min(len(details_content), idx + 80)
            context = details_content[start:end].strip()
            # Clean up
            context = context.split('.')[0].split(',')[0].strip()
            if len(context) > 10:
                return context
    
    return ""


def _extract_company_achievements(details_content: str) -> str:
    """Extract company achievements or milestones from details"""
    if not details_content:
        return ""
    
    content_lower = details_content.lower()
    
    # Look for achievement-related keywords
    achievement_keywords = [
        'achieved', 'success', 'milestone', 'growth', 'expansion',
        'award', 'recognition', 'leading', 'pioneer', 'established'
    ]
    
    for keyword in achievement_keywords:
        if keyword in content_lower:
            # Extract context around the keyword
            idx = content_lower.find(keyword)
            start = max(0, idx - 40)
            end = min(len(details_content), idx + 100)
            context = details_content[start:end].strip()
            # Clean up
            context = context.split('.')[0].split(',')[0].strip()
            if len(context) > 15:
                return context
    
    return ""


def _get_product_specific_benefits(product_description: str, context: str) -> dict:
    """Generate product-specific benefits based on the product description"""
    product_lower = product_description.lower()
    
    # AI Agent benefits
    if 'ai agent' in product_lower or 'ai agent' in product_description:
        if context == "vc_portfolio":
            return {
                'primary_benefit': 'intelligent deal flow analysis and automated portfolio monitoring',
                'secondary_benefit': 'AI-powered market research and competitive intelligence',
                'metric': '60% faster deal evaluation and 40% improved portfolio insights'
            }
        elif context == "tech_innovation":
            return {
                'primary_benefit': 'intelligent automation and smart decision-making capabilities',
                'secondary_benefit': 'AI-driven process optimization and predictive analytics',
                'metric': '50% reduction in manual tasks and 35% faster decision cycles'
            }
        else:
            return {
                'primary_benefit': 'intelligent automation and smart workflow optimization',
                'secondary_benefit': 'AI-powered insights and predictive capabilities',
                'metric': '45% efficiency gains and 30% cost reduction'
            }
    
    # Robotics benefits
    elif 'robot' in product_lower or 'robotics' in product_lower:
        if context == "vc_portfolio":
            return {
                'primary_benefit': 'automated portfolio monitoring and intelligent data processing',
                'secondary_benefit': 'robotic process automation for investment workflows',
                'metric': '70% faster data analysis and 50% improved accuracy'
            }
        elif context == "tech_innovation":
            return {
                'primary_benefit': 'advanced robotic solutions and intelligent automation',
                'secondary_benefit': 'cutting-edge robotics technology and smart systems',
                'metric': '80% operational efficiency improvement and breakthrough innovation'
            }
        else:
            return {
                'primary_benefit': 'robotic process automation and intelligent systems',
                'secondary_benefit': 'advanced automation and smart operational control',
                'metric': '55% productivity increase and 40% error reduction'
            }
    
    # Startup AI Product benefits
    elif 'startup' in product_lower or 'ai product' in product_lower:
        if context == "vc_portfolio":
            return {
                'primary_benefit': 'revolutionary AI solutions for portfolio companies',
                'secondary_benefit': 'next-generation AI technology and innovative applications',
                'metric': '3x faster growth potential and 90% market differentiation'
            }
        elif context == "tech_innovation":
            return {
                'primary_benefit': 'groundbreaking AI technology and innovative solutions',
                'secondary_benefit': 'cutting-edge AI products and market-disrupting capabilities',
                'metric': '5x competitive advantage and breakthrough market positioning'
            }
        else:
            return {
                'primary_benefit': 'innovative AI solutions and revolutionary technology',
                'secondary_benefit': 'next-generation AI products and smart applications',
                'metric': '4x efficiency improvement and market-leading innovation'
            }
    
    # Software Development benefits
    elif 'software' in product_lower or 'development' in product_lower:
        if context == "vc_portfolio":
            return {
                'primary_benefit': 'custom software solutions for portfolio companies',
                'secondary_benefit': 'scalable development platforms and technical expertise',
                'metric': '50% faster time-to-market and 60% development cost reduction'
            }
        elif context == "tech_innovation":
            return {
                'primary_benefit': 'advanced software development and technical innovation',
                'secondary_benefit': 'cutting-edge development tools and scalable solutions',
                'metric': '70% faster development cycles and breakthrough technical capabilities'
            }
        else:
            return {
                'primary_benefit': 'professional software development and technical solutions',
                'secondary_benefit': 'scalable software platforms and development expertise',
                'metric': '45% faster delivery and 35% improved quality'
            }
    
    # Digital Marketing benefits
    elif 'marketing' in product_lower or 'digital' in product_lower:
        if context == "vc_portfolio":
            return {
                'primary_benefit': 'advanced digital marketing strategies for portfolio companies',
                'secondary_benefit': 'data-driven marketing automation and growth optimization',
                'metric': '80% increase in lead generation and 65% improved conversion rates'
            }
        elif context == "tech_innovation":
            return {
                'primary_benefit': 'innovative digital marketing and growth hacking solutions',
                'secondary_benefit': 'AI-powered marketing automation and predictive analytics',
                'metric': '3x customer acquisition and 90% marketing ROI improvement'
            }
        else:
            return {
                'primary_benefit': 'comprehensive digital marketing and growth strategies',
                'secondary_benefit': 'data-driven marketing automation and performance optimization',
                'metric': '60% increase in brand visibility and 50% cost reduction'
            }
    
    # Cloud Computing benefits
    elif 'cloud' in product_lower or 'computing' in product_lower:
        if context == "vc_portfolio":
            return {
                'primary_benefit': 'scalable cloud infrastructure for portfolio companies',
                'secondary_benefit': 'advanced cloud solutions and infrastructure optimization',
                'metric': '70% infrastructure cost reduction and 90% scalability improvement'
            }
        elif context == "tech_innovation":
            return {
                'primary_benefit': 'cutting-edge cloud technology and infrastructure innovation',
                'secondary_benefit': 'advanced cloud platforms and next-generation solutions',
                'metric': '5x performance improvement and breakthrough scalability'
            }
        else:
            return {
                'primary_benefit': 'comprehensive cloud solutions and infrastructure services',
                'secondary_benefit': 'scalable cloud platforms and performance optimization',
                'metric': '50% cost reduction and 80% performance improvement'
            }
    
    # Default benefits for any other product
    else:
        if context == "vc_portfolio":
            return {
                'primary_benefit': 'innovative solutions for portfolio companies',
                'secondary_benefit': 'advanced technology and strategic optimization',
                'metric': '40% efficiency gains and 30% competitive advantage'
            }
        elif context == "tech_innovation":
            return {
                'primary_benefit': 'cutting-edge technology and innovative solutions',
                'secondary_benefit': 'advanced capabilities and breakthrough innovation',
                'metric': '3x performance improvement and market leadership'
            }
        else:
            return {
                'primary_benefit': 'professional solutions and strategic optimization',
                'secondary_benefit': 'advanced technology and operational excellence',
                'metric': '35% efficiency improvement and 25% cost reduction'
            }


def _get_founder_product_content(product_description: str) -> dict:
    """Generate founder-style product content based on the product description"""
    product_lower = product_description.lower()
    
    # AI Agent content
    if 'ai agent' in product_lower or 'ai agent' in product_description:
        return {
            'product_name': 'Nexus AI',
            'product_description': 'an intelligent business automation platform that helps organizations streamline operations, automate complex workflows, and make data-driven decisions',
            'category': 'automation',
            'capability_1': 'Process and analyze business data with human-level intelligence and context awareness.',
            'capability_2': 'Auto-execute complex workflows and decision trees aligned with business rules and compliance requirements.',
            'capability_3': 'Continuously learn from operations, instantly adapting to business changes and generating AI-driven optimization recommendations.',
            'value_proposition': 'it turns static business processes into live operational intelligence',
            'vision': 'a unified AI automation layer for enterprises — bridging intelligence, automation, and business governance',
            'impact': 'cut operational overhead by up to 60% while improving accuracy and speed',
            'target_sectors': 'finance, manufacturing, and healthcare',
            'market_disruption': 'business process automation'
        }
    
    # Robotics content
    elif 'robot' in product_lower or 'robotics' in product_lower:
        return {
            'product_name': 'RoboTech Pro',
            'product_description': 'an advanced robotic automation system that helps organizations optimize production, enhance quality control, and reduce operational costs',
            'category': 'robotic automation',
            'capability_1': 'Deploy intelligent robotic systems that adapt to production environments with minimal human intervention.',
            'capability_2': 'Auto-optimize manufacturing workflows and quality control processes using advanced computer vision and machine learning.',
            'capability_3': 'Continuously monitor production metrics, instantly identifying bottlenecks and generating predictive maintenance alerts.',
            'value_proposition': 'it transforms traditional manufacturing into intelligent, self-optimizing production systems',
            'vision': 'a unified robotic intelligence platform for industrial operations — bridging automation, AI, and operational excellence',
            'impact': 'increase production efficiency by up to 80% while reducing defects and downtime',
            'target_sectors': 'manufacturing, logistics, and automotive',
            'market_disruption': 'industrial automation and smart manufacturing'
        }
    
    # Startup AI Product content
    elif 'startup' in product_lower or 'ai product' in product_lower:
        return {
            'product_name': 'StartupAI',
            'product_description': 'a revolutionary AI-powered startup acceleration platform that helps emerging companies scale faster, make better decisions, and achieve product-market fit',
            'category': 'startup acceleration',
            'capability_1': 'Analyze market trends and competitive landscapes with AI-powered insights to identify growth opportunities.',
            'capability_2': 'Auto-generate business strategies, financial models, and go-to-market plans tailored to specific industries and markets.',
            'capability_3': 'Continuously monitor startup metrics, instantly flagging risks and generating AI-driven recommendations for scaling.',
            'value_proposition': 'it turns startup challenges into systematic growth opportunities',
            'vision': 'a unified AI acceleration layer for startups — bridging innovation, strategy, and execution',
            'impact': 'accelerate startup growth by up to 300% while reducing failure rates significantly',
            'target_sectors': 'fintech, healthtech, and edtech',
            'market_disruption': 'startup acceleration and venture building'
        }
    
    # Software Development content
    elif 'software' in product_lower or 'development' in product_lower:
        return {
            'product_name': 'CodeForge AI',
            'product_description': 'an intelligent software development platform that helps teams build, test, and deploy applications faster with AI-powered code generation and optimization',
            'category': 'development',
            'capability_1': 'Generate production-ready code from natural language descriptions and architectural specifications.',
            'capability_2': 'Auto-detect bugs, security vulnerabilities, and performance issues while suggesting optimal fixes and improvements.',
            'capability_3': 'Continuously optimize code quality, instantly refactoring legacy systems and generating comprehensive test suites.',
            'value_proposition': 'it transforms software development from manual coding to intelligent engineering',
            'vision': 'a unified AI development platform for enterprises — bridging code, automation, and software excellence',
            'impact': 'reduce development time by up to 70% while improving code quality and security',
            'target_sectors': 'fintech, SaaS, and enterprise software',
            'market_disruption': 'software development and engineering productivity'
        }
    
    # Digital Marketing content
    elif 'marketing' in product_lower or 'digital' in product_lower:
        return {
            'product_name': 'MarketGenius AI',
            'product_description': 'an intelligent digital marketing platform that helps businesses create, optimize, and scale marketing campaigns with AI-powered insights and automation',
            'category': 'marketing automation',
            'capability_1': 'Generate personalized marketing content and campaigns tailored to specific audiences and market segments.',
            'capability_2': 'Auto-optimize ad spend, targeting, and creative elements using real-time performance data and predictive analytics.',
            'capability_3': 'Continuously analyze customer behavior, instantly identifying trends and generating AI-driven marketing strategies.',
            'value_proposition': 'it transforms marketing from guesswork into data-driven precision',
            'vision': 'a unified AI marketing platform for businesses — bridging creativity, data, and customer engagement',
            'impact': 'increase marketing ROI by up to 250% while reducing customer acquisition costs',
            'target_sectors': 'e-commerce, SaaS, and consumer brands',
            'market_disruption': 'digital marketing and customer acquisition'
        }
    
    # Cloud Computing content
    elif 'cloud' in product_lower or 'computing' in product_lower:
        return {
            'product_name': 'CloudNexus AI',
            'product_description': 'an intelligent cloud infrastructure platform that helps organizations optimize costs, enhance security, and scale applications with AI-powered automation',
            'category': 'cloud infrastructure',
            'capability_1': 'Auto-provision and optimize cloud resources based on application demands and performance requirements.',
            'capability_2': 'Detect security threats and compliance issues in real-time while suggesting remediation strategies.',
            'capability_3': 'Continuously monitor infrastructure costs, instantly identifying optimization opportunities and generating cost-saving recommendations.',
            'value_proposition': 'it transforms cloud infrastructure from static setup to intelligent, self-optimizing systems',
            'vision': 'a unified AI cloud platform for enterprises — bridging infrastructure, security, and operational excellence',
            'impact': 'reduce cloud costs by up to 50% while improving security and performance',
            'target_sectors': 'enterprise software, fintech, and healthcare',
            'market_disruption': 'cloud infrastructure and DevOps automation'
        }
    
    # Legal Tech content (like Durga AI example)
    elif 'legal' in product_lower or 'compliance' in product_lower:
        return {
            'product_name': 'Durga AI',
            'product_description': 'an intelligent legal compliance system that helps organizations stay compliant, audit-ready, and legally agile',
            'category': 'compliance',
            'capability_1': 'Read and interpret legal documents — policies, contracts, or regulatory filings — with human-level understanding.',
            'capability_2': 'Auto-draft and validate legal documents aligned with jurisdiction-specific requirements.',
            'capability_3': 'Continuously monitor law updates, instantly mapping them to business operations and generating AI-driven compliance actions.',
            'value_proposition': 'it turns static compliance data into live legal intelligence',
            'vision': 'a unified legal AI layer for enterprises — bridging law, automation, and data governance',
            'impact': 'cut compliance overhead by up to 70% while improving accuracy and reducing risk',
            'target_sectors': 'finance, manufacturing, and healthcare',
            'market_disruption': 'legal compliance automation'
        }
    
    # Default content for any other product
    else:
        return {
            'product_name': 'InnovateAI',
            'product_description': 'an intelligent business solution that helps organizations optimize operations, enhance productivity, and drive growth',
            'category': 'business optimization',
            'capability_1': 'Analyze business processes and identify optimization opportunities with AI-powered insights.',
            'capability_2': 'Auto-implement workflow improvements and generate data-driven recommendations for operational excellence.',
            'capability_3': 'Continuously monitor business metrics, instantly flagging issues and generating AI-driven solutions.',
            'value_proposition': 'it transforms business operations from reactive to proactive intelligence',
            'vision': 'a unified AI business platform for enterprises — bridging operations, intelligence, and growth',
            'impact': 'increase operational efficiency by up to 50% while reducing costs and improving outcomes',
            'target_sectors': 'technology, finance, and healthcare',
            'market_disruption': 'business process optimization'
        }


def _get_company_specific_info(company_name: str) -> dict:
    """Get company-specific information based on name"""
    name_lower = company_name.lower()
    
    company_info = {
        'sequoia': {'focus': 'early-stage investments', 'style': 'pioneering', 'strength': 'market leadership'},
        'accel': {'focus': 'growth-stage investments', 'style': 'scaling', 'strength': 'operational excellence'},
        'matrix': {'focus': 'consumer technology', 'style': 'innovative', 'strength': 'market disruption'},
        'nexus': {'focus': 'enterprise technology', 'style': 'strategic', 'strength': 'business transformation'},
        'chiratae': {'focus': 'technology investments', 'style': 'collaborative', 'strength': 'partnership approach'},
        'kalaari': {'focus': 'consumer internet', 'style': 'growth-oriented', 'strength': 'market expansion'},
        'orios': {'focus': 'early-stage ventures', 'style': 'supportive', 'strength': 'founder-friendly'},
        'pi': {'focus': 'AI and deep tech', 'style': 'cutting-edge', 'strength': 'technological innovation'},
        'stellaris': {'focus': 'technology startups', 'style': 'visionary', 'strength': 'future-focused'},
        'inventus': {'focus': 'technology investments', 'style': 'analytical', 'strength': 'data-driven decisions'},
        'idg': {'focus': 'technology ventures', 'style': 'comprehensive', 'strength': 'global perspective'}
    }
    
    for key, info in company_info.items():
        if key in name_lower:
            return info
    
    return {'focus': 'venture capital', 'style': 'professional', 'strength': 'strategic approach'}


def _generate_additional_context(company_focus: str, industry: str, company_achievements: str) -> str:
    """Generate additional context to reach 100-150 words"""
    
    if company_achievements:
        return f"Our track record includes helping similar companies achieve remarkable growth and operational excellence. We'd be honored to contribute to {company_focus} success."
    elif industry != 'general':
        return f"We've successfully implemented our solutions across the {industry} sector, consistently delivering measurable improvements in efficiency and performance."
    else:
        return f"Our proven approach has helped numerous companies optimize their operations and achieve sustainable competitive advantages."


def _extract_company_focus(details_content: str) -> str:
    """Extract the main focus/domain of the company from details"""
    if not details_content:
        return ""
    
    content_lower = details_content.lower()
    
    # Look for focus keywords
    focus_patterns = {
        'venture capital': ['venture', 'capital', 'investment', 'funding', 'portfolio'],
        'technology innovation': ['tech', 'innovation', 'digital', 'software', 'platform'],
        'healthcare solutions': ['health', 'medical', 'care', 'patient', 'clinical'],
        'financial services': ['finance', 'banking', 'financial', 'wealth', 'investment'],
        'manufacturing': ['manufacturing', 'production', 'industrial', 'factory'],
        'retail commerce': ['retail', 'commerce', 'consumer', 'shopping', 'ecommerce'],
        'logistics': ['logistics', 'supply chain', 'shipping', 'transport'],
        'education': ['education', 'learning', 'university', 'academic'],
        'consulting': ['consulting', 'advisory', 'strategy', 'services']
    }
    
    for focus, keywords in focus_patterns.items():
        if any(keyword in content_lower for keyword in keywords):
            return focus
    
    return ""


def _extract_company_mission(details_content: str) -> str:
    """Extract company mission or purpose from details"""
    if not details_content:
        return ""
    
    content_lower = details_content.lower()
    
    # Look for mission-related phrases
    mission_indicators = [
        'mission to', 'aim to', 'strive to', 'dedicated to', 'committed to',
        'focused on', 'specializing in', 'expertise in', 'leading in'
    ]
    
    for indicator in mission_indicators:
        if indicator in content_lower:
            # Extract the phrase after the indicator
            start_idx = content_lower.find(indicator)
            phrase_start = start_idx + len(indicator)
            phrase = details_content[phrase_start:phrase_start + 100].strip()
            # Clean up the phrase
            phrase = phrase.split('.')[0].split(',')[0].strip()
            if len(phrase) > 10:
                return phrase
    
    return ""


def _extract_company_services(details_content: str) -> str:
    """Extract company services or offerings from details"""
    if not details_content:
        return ""
    
    content_lower = details_content.lower()
    
    # Look for service-related keywords
    service_keywords = [
        'services', 'solutions', 'products', 'offerings', 'platform',
        'software', 'consulting', 'advisory', 'development', 'management'
    ]
    
    for keyword in service_keywords:
        if keyword in content_lower:
            # Extract context around the keyword
            idx = content_lower.find(keyword)
            start = max(0, idx - 50)
            end = min(len(details_content), idx + 100)
            context = details_content[start:end].strip()
            # Clean up
            context = context.split('.')[0].split(',')[0].strip()
            if len(context) > 15:
                return context
    
    return ""


def _generate_specific_benefits(company_focus: str, company_services: str, industry: str, product_description: str) -> str:
    """Generate specific benefits based on company focus and services"""
    
    if 'venture' in company_focus.lower() or 'capital' in company_focus.lower():
        return "automating portfolio analysis, enhancing due diligence processes, and providing real-time market insights"
    elif 'tech' in company_focus.lower() or 'software' in company_focus.lower():
        return "streamlining development workflows, automating testing processes, and optimizing deployment pipelines"
    elif 'health' in company_focus.lower() or 'medical' in company_focus.lower():
        return "improving patient data management, automating appointment scheduling, and enhancing diagnostic accuracy"
    elif 'finance' in company_focus.lower() or 'bank' in company_focus.lower():
        return "automating risk assessment, enhancing fraud detection, and streamlining compliance processes"
    elif 'manufacturing' in company_focus.lower():
        return "optimizing production lines, implementing predictive maintenance, and enhancing quality control"
    elif 'retail' in company_focus.lower() or 'commerce' in company_focus.lower():
        return "optimizing inventory management, personalizing customer experiences, and automating order processing"
    elif 'logistics' in company_focus.lower():
        return "optimizing route planning, automating warehouse operations, and enhancing supply chain visibility"
    elif 'education' in company_focus.lower():
        return "personalizing learning experiences, automating administrative tasks, and enhancing student engagement"
    elif 'consulting' in company_focus.lower():
        return "streamlining client onboarding, automating report generation, and enhancing project management"
    else:
        return "automating complex processes, enhancing operational efficiency, and driving data-driven decision making"


EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _extract_emails_from_text(text: str) -> List[str]:
    return [m.group(0).strip() for m in EMAIL_REGEX.finditer(text or '')]


def _extract_emails_from_series(series: pd.Series) -> List[str]:
    emails: List[str] = []
    for v in series.dropna().astype(str):
        emails.extend(_extract_emails_from_text(v))
    return emails


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/send', methods=['GET', 'POST'])
def send_email():
    if request.method == 'GET':
        return render_template('send.html')

    # POST
    subject = request.form.get('subject', '').strip()
    body = request.form.get('body', '').strip()
    single_email = request.form.get('single_email', '').strip()
    auto_generate = request.form.get('auto_generate') == 'on'
    product_description = request.form.get('product_description', '').strip()

    uploaded_file = request.files.get('file')
    emails: List[str] = []
    company_data_list: List[dict] = []

    if uploaded_file and uploaded_file.filename:
        if not allowed_file(uploaded_file.filename):
            flash('Only CSV or XLSX files are allowed.')
            return redirect(url_for('send_email'))
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        filename = secure_filename(uploaded_file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        uploaded_file.save(save_path)
        
        # Check if auto-generate is enabled and file has company data
        if auto_generate:
            company_data_list = extract_company_data_from_file(save_path)
            if company_data_list:
                emails = [company['email'] for company in company_data_list]
            else:
                emails = extract_emails_from_file(save_path)
        else:
            emails = extract_emails_from_file(save_path)
    elif single_email:
        emails = [single_email]
    else:
        flash('Provide a CSV/XLSX file or a single email address.')
        return redirect(url_for('send_email'))

    if not emails:
        flash('No valid email addresses found.')
        return redirect(url_for('send_email'))

    # If auto-generate is enabled and we have company data, generate personalized emails
    if auto_generate and company_data_list:
        # Generate subject and body for each company
        for company_data in company_data_list:
            subject, body = generate_cold_email(company_data, product_description)
            company_data['subject'] = subject
            company_data['body'] = body
        
        return render_template('cold_email_preview.html', 
                             company_data_list=company_data_list,
                             email_count=len(emails),
                             product_description=product_description)
    
    # Show preview instead of sending immediately
    return render_template('preview.html', 
                         subject=subject, 
                         body=body, 
                         emails=emails,
                         email_count=len(emails))


@app.route('/confirm_send', methods=['POST'])
def confirm_send():
    subject = request.form.get('subject', '').strip()
    body = request.form.get('body', '').strip()
    emails_str = request.form.get('emails', '')
    
    # Parse emails from hidden field
    emails = [email.strip() for email in emails_str.split(',') if email.strip()]
    
    if not emails:
        flash('No email addresses to send to.')
        return redirect(url_for('send_email'))

    # Start scheduled sending in background
    threading.Thread(target=_schedule_emails, args=(subject, body, emails), daemon=True).start()
    
    flash(f"📅 Scheduled {len(emails)} emails to be sent with 2-minute intervals. Check the terminal for progress.")
    return redirect(url_for('send_email'))


@app.route('/confirm_cold_email_send', methods=['POST'])
def confirm_cold_email_send():
    company_data_list = []
    product_description = request.form.get('product_description', 'AI agent and robotics solutions').strip()
    
    # Get all form data
    emails = request.form.getlist('company_email')
    names = request.form.getlist('company_name')
    details = request.form.getlist('company_details')
    
    # Get custom subjects and bodies
    subjects = []
    bodies = []
    for i in range(len(emails)):
        subject_key = f'subject_{i}'
        body_key = f'body_{i}'
        subjects.append(request.form.get(subject_key, '').strip())
        bodies.append(request.form.get(body_key, '').strip())
    
    # Combine the data into company dictionaries
    for i in range(len(emails)):
        if emails[i] and names[i]:  # Only add if both email and name exist
            company_data_list.append({
                'email': emails[i].strip(),
                'company': names[i].strip(),
                'details_content': details[i].strip() if i < len(details) else '',
                'custom_subject': subjects[i] if i < len(subjects) else '',
                'custom_body': bodies[i] if i < len(bodies) else ''
            })
    
    if not company_data_list:
        flash('No company data to send emails to.')
        return redirect(url_for('send_email'))

    # Start scheduled cold email sending in background
    threading.Thread(target=_schedule_cold_emails, args=(company_data_list, product_description), daemon=True).start()
    
    flash(f"📅 Scheduled {len(company_data_list)} personalized cold emails to be sent with 2-minute intervals. Check the terminal for progress.")
    return redirect(url_for('send_email'))


def _schedule_cold_emails(company_data_list: List[dict], product_description: str = "AI agent and robotics solutions"):
    """Send personalized cold emails with 2-minute intervals between each email"""
    import time
    
    service = gmail_service()
    sent_count = 0
    failed = []
    
    print(f"\n[COLD EMAIL] Starting scheduled cold email sending to {len(company_data_list)} companies...")
    print(f"[SCHEDULE] Interval: 2 minutes between each email")
    print(f"[TOPIC] {product_description}")
    print("-" * 60)
    
    for i, company_data in enumerate(company_data_list, 1):
        try:
            company_name = company_data.get('company', 'Unknown Company')
            email = company_data.get('email', '')
            
            print(f"[{i}/{len(company_data_list)}] Sending to: {company_name} ({email})")
            
            # Use custom subject and body if provided, otherwise generate
            custom_subject = company_data.get('custom_subject', '').strip()
            custom_body = company_data.get('custom_body', '').strip()
            
            if custom_subject and custom_body:
                subject = custom_subject
                body = custom_body
                print(f"[CUSTOM] Using custom subject and body for {company_name}")
            else:
                # Generate personalized email
                subject, body = generate_cold_email(company_data, product_description)
                print(f"[GENERATED] Using auto-generated content for {company_name}")
            
            msg = MIMEText(body)
            msg['to'] = email
            msg['subject'] = subject
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            message_body = {'raw': raw_message}
            
            service.users().messages().send(userId='me', body=message_body).execute()
            sent_count += 1
            print(f"[SUCCESS] Sent cold email to {company_name}")
            
            # Wait 2 minutes before next email (except for the last one)
            if i < len(company_data_list):
                print(f"[WAIT] Waiting 2 minutes before next email...")
                time.sleep(120)  # 2 minutes = 120 seconds
                
        except Exception as exc:
            failed.append((company_data.get('company', 'Unknown'), str(exc)))
            print(f"[ERROR] Failed to send to {company_data.get('company', 'Unknown')}: {exc}")
            
            # Still wait 2 minutes even if email failed
            if i < len(company_data_list):
                print(f"[WAIT] Waiting 2 minutes before next email...")
                time.sleep(120)
    
    print("-" * 60)
    print(f"[COMPLETE] Cold email campaign completed!")
    print(f"[SUCCESS] Successfully sent: {sent_count} cold emails")
    if failed:
        print(f"[FAILED] Failed: {len(failed)} emails")
        for company_name, error in failed:
            print(f"   - {company_name}: {error}")
    print("-" * 60)


def _schedule_emails(subject: str, body: str, emails: List[str]):
    """Send emails with 2-minute intervals between each email"""
    import time
    
    service = gmail_service()
    sent_count = 0
    failed = []
    
    print(f"\n[EMAIL] Starting scheduled email sending to {len(emails)} recipients...")
    print(f"[SCHEDULE] Interval: 2 minutes between each email")
    print(f"[SUBJECT] {subject}")
    print("-" * 50)
    
    for i, recipient in enumerate(emails, 1):
        try:
            print(f"[{i}/{len(emails)}] Sending to: {recipient}")
            
            msg = MIMEText(body)
            msg['to'] = recipient
            msg['subject'] = subject
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            message_body = {'raw': raw_message}
            
            service.users().messages().send(userId='me', body=message_body).execute()
            sent_count += 1
            print(f"[SUCCESS] Sent to {recipient}")
            
            # Wait 2 minutes before next email (except for the last one)
            if i < len(emails):
                print(f"[WAIT] Waiting 2 minutes before next email...")
                time.sleep(120)  # 2 minutes = 120 seconds
                
        except Exception as exc:
            failed.append((recipient, str(exc)))
            print(f"[ERROR] Failed to send to {recipient}: {exc}")
            
            # Still wait 2 minutes even if email failed
            if i < len(emails):
                print(f"[WAIT] Waiting 2 minutes before next email...")
                time.sleep(120)
    
    print("-" * 50)
    print(f"[COMPLETE] Scheduled sending completed!")
    print(f"[SUCCESS] Successfully sent: {sent_count} emails")
    if failed:
        print(f"[FAILED] Failed: {len(failed)} emails")
        for recipient, error in failed:
            print(f"   - {recipient}: {error}")
    print("-" * 50)


@app.route('/read')
def read_emails():
    service = gmail_service()
    try:
        results = service.users().messages().list(userId='me', maxResults=10).execute()
        messages = results.get('messages', [])
        items = []
        for msg in messages:
            data = service.users().messages().get(userId='me', id=msg['id']).execute()
            headers = data['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '(No Sender)')
            snippet = data.get('snippet', '')
            items.append({'id': msg['id'], 'subject': subject, 'from': sender, 'snippet': snippet, 'threadId': data.get('threadId')})
        return render_template('read.html', emails=items)
    except Exception as exc:  # noqa: BLE001
        flash(f"Failed to read emails: {exc}")
        return render_template('read.html', emails=[])


@app.route('/reply', methods=['GET', 'POST'])
def reply_email():
    if request.method == 'GET':
        return render_template('reply.html')

    message_id = request.form.get('message_id', '').strip()
    reply_text = request.form.get('reply_text', '').strip()
    if not message_id or not reply_text:
        flash('Message ID and reply text are required.')
        return redirect(url_for('reply_email'))

    service = gmail_service()
    try:
        original = service.users().messages().get(userId='me', id=message_id).execute()
        headers = original['payload']['headers']
        sender = next((h['value'] for h in headers if h['name'] == 'From'), None)
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Re: (No Subject)')

        msg = MIMEText(reply_text)
        msg['to'] = sender
        msg['subject'] = f"Re: {subject}"
        msg['In-Reply-To'] = message_id
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        body = {'raw': raw, 'threadId': original.get('threadId')}
        service.users().messages().send(userId='me', body=body).execute()
        flash('Reply sent successfully.')
    except Exception as exc:  # noqa: BLE001
        flash(f"Failed to send reply: {exc}")

    return redirect(url_for('reply_email'))


def create_app():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    return app


if __name__ == '__main__':
    def _open_browser():
        try:
            webbrowser.open('http://127.0.0.1:5000')
        except Exception:
            pass
    threading.Timer(1.0, _open_browser).start()
    create_app().run(host='127.0.0.1', port=5000, debug=True)


