"""
Document Parser for Campaign Documents
Extracts campaign information from PDF and DOCX files using AI
"""

import os
from typing import Dict, Optional
import PyPDF2
from docx import Document
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class DocumentParser:
    """Parse campaign documents (PDF/DOCX) and extract structured information"""

    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        self.model = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')

        if not self.api_key or self.api_key == 'your_groq_api_key_here':
            raise ValueError("GROQ_API_KEY not configured")

        self.client = Groq(api_key=self.api_key)

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text content from PDF file"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")

    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text content from DOCX file"""
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise Exception(f"Error reading DOCX: {str(e)}")

    def extract_text(self, file_path: str) -> str:
        """Extract text from document based on file type"""
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_ext in ['.docx', '.doc']:
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

    def parse_campaign_document(self, file_path: str) -> Dict[str, str]:
        """
        Parse campaign document and extract structured information using AI

        Returns:
            Dict with keys: company, product, value_props, metrics, goal, description
        """
        try:
            # Extract raw text
            document_text = self.extract_text(file_path)

            if not document_text or len(document_text) < 50:
                raise ValueError("Document appears to be empty or too short")

            # Use AI to structure the information
            structured_data = self._analyze_with_ai(document_text)

            return structured_data

        except Exception as e:
            raise Exception(f"Error parsing document: {str(e)}")

    def _analyze_with_ai(self, document_text: str) -> Dict[str, str]:
        """Use AI to extract structured campaign information from text"""

        prompt = f"""Analyze this campaign/pitch document and extract key information.

Document Text:
{document_text[:4000]}

Extract and return ONLY a JSON object with these fields:
1. "company": Company name
2. "product": Product or service name and brief description
3. "value_props": Main value propositions (1-3 key benefits)
4. "metrics": Key achievements, metrics, or traction (revenue, users, growth, etc.)
5. "goal": Campaign goal (funding round, sales, partnership, etc.)
6. "description": 2-3 sentence company description

Example format:
{{
    "company": "TechCorp Inc",
    "product": "AI-powered analytics platform for e-commerce",
    "value_props": "70% faster insights, 10x ROI, Real-time analytics",
    "metrics": "1000+ customers, $2M ARR, 40% MoM growth",
    "goal": "Series A funding round",
    "description": "TechCorp provides AI analytics for e-commerce companies. Founded in 2022, backed by top VCs."
}}

Return ONLY valid JSON, no other text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a document analysis expert. Extract structured data from campaign documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON response
            import json

            # Remove markdown code blocks if present
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]

            structured_data = json.loads(result_text.strip())

            # Validate required fields
            required_fields = ['company', 'product', 'value_props', 'metrics', 'goal', 'description']
            for field in required_fields:
                if field not in structured_data:
                    structured_data[field] = "Not specified"

            return structured_data

        except json.JSONDecodeError as e:
            # Fallback: create basic structure from text
            return {
                "company": "Your Company",
                "product": document_text[:200],
                "value_props": "Please review and edit",
                "metrics": "Please add metrics",
                "goal": "Please specify goal",
                "description": document_text[:300]
            }
        except Exception as e:
            raise Exception(f"AI analysis failed: {str(e)}")

    def generate_email_template(self, campaign_data: Dict[str, str]) -> str:
        """Generate a base email template from campaign data"""

        template = f"""Dear {{{{company}}}},

{campaign_data.get('description', '')}

{{{{why}}}}

{campaign_data.get('value_props', '')}

{campaign_data.get('metrics', '')}

{campaign_data.get('goal', 'I would love to discuss how we can work together.')}

Best regards,
{campaign_data.get('company', 'Your Company')}"""

        return template


# Singleton instance
_parser = None

def get_parser() -> DocumentParser:
    """Get or create document parser instance"""
    global _parser
    if _parser is None:
        _parser = DocumentParser()
    return _parser
