"""
Gmail Campaign Builder V2 - AI-Powered Email Outreach
Modern interface with Groq AI assistant
Port: 5001
"""

import os
import sys
import json
import time
import threading
import pandas as pd
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import existing Gmail modules
from gmail.auth import gmail_authenticate
from gmail.mail import create_message, send_message, list_messages, read_message
from ai.groq_helper import get_assistant
from ai.document_parser import get_parser
from database import get_db

# Alias for compatibility
get_gmail_service = gmail_authenticate
get_message = read_message

# Load environment variables (override existing environment)
load_dotenv(override=True)

# Flask app configuration
app = Flask(__name__,
            template_folder='src_v2/templates',
            static_folder='src_v2/static')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Disable template caching for development
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Configuration
UPLOAD_FOLDER = 'uploads'
MATERIALS_FOLDER = 'uploads/materials'
DOCUMENTS_FOLDER = 'uploads/documents'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
ALLOWED_MATERIALS = {'pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png', 'gif', 'mp4', 'avi', 'mov', 'mkv'}
ALLOWED_DOCUMENTS = {'pdf', 'docx', 'doc'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB for regular uploads
MAX_ATTACHMENT_SIZE = 100 * 1024 * 1024  # 100MB for email attachments

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MATERIALS_FOLDER'] = MATERIALS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_ATTACHMENT_SIZE  # Allow larger attachments

# Ensure upload folders exist
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
Path(MATERIALS_FOLDER).mkdir(exist_ok=True)
Path(DOCUMENTS_FOLDER).mkdir(exist_ok=True)

# Store uploaded materials info
uploaded_materials_info = {}

# Global variables for tracking campaigns
active_campaign = {
    'status': 'idle',  # idle, running, paused, completed
    'total': 0,
    'sent': 0,
    'failed': 0,
    'current_email': '',
    'progress': [],
    'attachments': []  # List of attachment file paths for current campaign
}

# Campaign history storage (in production, use database)
campaign_history = []


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================================
# ROUTES - Main Pages
# ============================================================================

@app.route('/')
def index():
    """Home page - redirect to campaign builder"""
    return redirect(url_for('campaign'))


@app.route('/campaign')
def campaign():
    """Campaign builder page"""
    # Use v3 template for cleaner UI
    return render_template('campaign-v3.html')


@app.route('/inbox')
def inbox():
    """Unified inbox page"""
    # Use v3 template for cleaner UI
    return render_template('inbox-v3.html')


@app.route('/analytics')
def analytics():
    """Analytics dashboard"""
    # Use v3 template for cleaner UI
    return render_template('analytics-v3.html',
                         campaign_history=campaign_history,
                         total_sent=sum(c.get('sent', 0) for c in campaign_history))


@app.route('/authenticate')
def authenticate():
    """Trigger Gmail authentication"""
    try:
        # This will trigger the OAuth flow if token doesn't exist or is invalid
        creds = get_gmail_service()

        # If we reach here, authentication was successful
        flash('Gmail authenticated successfully!', 'success')
        return redirect(url_for('campaign'))
    except Exception as e:
        flash(f'Authentication failed: {str(e)}', 'error')
        return redirect(url_for('campaign'))


# ============================================================================
# API ROUTES - Authentication
# ============================================================================

@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """Check Gmail authentication status"""
    try:
        # Check if credentials exist
        if not os.path.exists('token.json'):
            return jsonify({'authenticated': False, 'message': 'No authentication token found'})

        # Try to get service to validate token
        try:
            from googleapiclient.discovery import build
            creds = get_gmail_service()
            service = build('gmail', 'v1', credentials=creds)
            # Test the service with a simple API call
            service.users().getProfile(userId='me').execute()
            return jsonify({'authenticated': True, 'message': 'Gmail authenticated successfully'})
        except Exception as e:
            return jsonify({'authenticated': False, 'message': f'Token expired or invalid: {str(e)}'})

    except Exception as e:
        return jsonify({'authenticated': False, 'error': str(e)}), 500


# ============================================================================
# API ROUTES - File Upload & Processing
# ============================================================================

@app.route('/api/upload', methods=['POST'])
def upload_csv():
    """Handle CSV/Excel file upload and return parsed data"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Use CSV or Excel files'}), 400

    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Parse file
        if filename.endswith('.csv'):
            # Try multiple encodings
            for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(filepath, encoding=encoding)
                    break
                except Exception:
                    continue
        else:
            df = pd.read_excel(filepath)

        # Find email column
        email_col = None
        email_patterns = ['email', 'emails', 'e-mail', 'mail', 'email id', 'email address']

        for col in df.columns:
            if col.lower() in email_patterns:
                email_col = col
                break

        if not email_col:
            # Heuristic: find column with most @
            for col in df.columns:
                if df[col].astype(str).str.contains('@').sum() > len(df) * 0.5:
                    email_col = col
                    break

        if not email_col:
            return jsonify({'error': 'No email column found in file'}), 400

        # Prepare data - keep ALL columns from CSV
        recipients = []
        for idx, row in df.iterrows():
            email = row.get(email_col, '')
            if pd.isna(email) or '@' not in str(email):
                continue

            # Convert row to dictionary and keep all columns
            recipient = row.to_dict()

            # Ensure email is set
            recipient['email'] = str(email).strip()
            recipient['Email'] = str(email).strip()

            # Try to find company name from various possible column names
            company_name = None
            for col_name in ['company name', 'Company Name', 'Company', 'company', 'COMPANY', 'Firm', 'firm', 'Organization', 'organization']:
                if col_name in recipient and not pd.isna(recipient[col_name]):
                    company_name = str(recipient[col_name]).strip()
                    break

            # Set standardized company field
            recipient['Company_Name'] = company_name or f'Company {idx+1}'
            recipient['company'] = company_name or f'Company {idx+1}'

            # Clean up NaN values
            for key, value in recipient.items():
                if pd.isna(value):
                    recipient[key] = ''
                elif not isinstance(value, str):
                    recipient[key] = str(value)

            # Debug logging
            print(f"DEBUG: Parsed recipient {idx+1}: Company_Name='{recipient.get('Company_Name')}', email='{recipient.get('email')}'")

            recipients.append(recipient)

        return jsonify({
            'success': True,
            'total': len(recipients),
            'recipients': recipients,
            'filename': filename
        })

    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500


@app.route('/api/upload-materials', methods=['POST'])
def upload_materials():
    """Handle additional materials upload (PDF, DOCX, images, videos)"""
    if 'files' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400

    files = request.files.getlist('files')
    uploaded_files = []

    try:
        for file in files:
            if file.filename == '':
                continue

            # Check file extension
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            if ext not in ALLOWED_MATERIALS:
                continue

            # Save file
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['MATERIALS_FOLDER'], filename)
            file.save(filepath)

            # Store file info
            file_info = {
                'filename': filename,
                'filepath': filepath,
                'type': ext,
                'size': os.path.getsize(filepath)
            }

            # Extract text content from documents (basic)
            if ext in ['pdf', 'docx', 'doc']:
                # For now, just store filepath. Can add text extraction later
                file_info['content_type'] = 'document'
            elif ext in ['jpg', 'jpeg', 'png', 'gif']:
                file_info['content_type'] = 'image'
            elif ext in ['mp4', 'avi', 'mov']:
                file_info['content_type'] = 'video'

            uploaded_files.append(file_info)

        # Store in global variable (in production, use database)
        session_id = request.headers.get('X-Session-ID', 'default')
        uploaded_materials_info[session_id] = uploaded_files

        return jsonify({
            'success': True,
            'files': uploaded_files,
            'total': len(uploaded_files)
        })

    except Exception as e:
        return jsonify({'error': f'Error uploading materials: {str(e)}'}), 500


@app.route('/api/upload-attachments', methods=['POST'])
def upload_attachments():
    """Upload email attachments for campaign"""
    try:
        if 'files' not in request.files:
            print("ERROR: No files in request")
            return jsonify({'error': 'No files uploaded'}), 400

        files = request.files.getlist('files')
        print(f"Received {len(files)} file(s) for upload")

        if not files or len(files) == 0:
            print("ERROR: Empty files list")
            return jsonify({'error': 'No files provided'}), 400

        uploaded_files = []

        # Create attachments folder if it doesn't exist
        attachments_folder = os.path.join(app.config.get('MATERIALS_FOLDER', 'uploads/materials'), 'attachments')
        Path(attachments_folder).mkdir(parents=True, exist_ok=True)
        print(f"Attachment folder: {attachments_folder}")

        for file in files:
            if file and file.filename:
                print(f"Processing file: {file.filename}, size: {file.content_length if hasattr(file, 'content_length') else 'unknown'}")
                filename = secure_filename(file.filename)
                # Add timestamp to avoid conflicts
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                unique_filename = f"{timestamp}_{filename}"
                filepath = os.path.join(attachments_folder, unique_filename)
                file.save(filepath)
                print(f"Saved to: {filepath}")
                uploaded_files.append(unique_filename)
            else:
                print(f"Skipping empty file or no filename")

        print(f"Successfully uploaded {len(uploaded_files)} file(s)")
        return jsonify({
            'success': True,
            'filenames': uploaded_files,
            'message': f'Uploaded {len(uploaded_files)} attachment(s)'
        })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR uploading attachments: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'error': f'Error uploading attachments: {str(e)}'}), 500


# ============================================================================
# API ROUTES - AI Assistant
# ============================================================================

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """Chat with AI assistant"""
    try:
        data = request.json
        user_message = data.get('message', '')
        context = data.get('context', {})

        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        assistant = get_assistant()
        response = assistant.chat(user_message, context)

        return jsonify({
            'success': True,
            'response': response
        })

    except ValueError as e:
        # API key not configured
        return jsonify({
            'error': str(e),
            'setup_required': True
        }), 400
    except Exception as e:
        return jsonify({'error': f'AI error: {str(e)}'}), 500


@app.route('/api/ai/enhance-email', methods=['POST'])
def ai_enhance_email():
    """Enhance email with AI"""
    try:
        data = request.json
        email_body = data.get('body', '')
        company_name = data.get('company', 'Company')
        audience_type = data.get('audience', 'VCs')

        if not email_body:
            return jsonify({'error': 'No email body provided'}), 400

        assistant = get_assistant()
        enhanced = assistant.enhance_email(email_body, company_name, audience_type)

        return jsonify({
            'success': True,
            **enhanced
        })

    except Exception as e:
        return jsonify({'error': f'Enhancement error: {str(e)}'}), 500


@app.route('/api/ai/generate-email', methods=['POST'])
def ai_generate_email():
    """Generate cold email with AI"""
    try:
        data = request.json
        company_data = data.get('company', {})
        product_info = data.get('product', '')
        audience_type = data.get('audience', 'VCs')
        email_style = data.get('email_style', 'concise')
        subject_template = data.get('subject_template', '')
        message_template = data.get('message_template', '')
        our_company = data.get('our_company', '')
        campaign_goal = data.get('campaign_goal', '')

        assistant = get_assistant()
        generated = assistant.generate_cold_email(
            company_data,
            product_info,
            audience_type,
            subject_template,
            message_template,
            our_company,
            email_style,
            campaign_goal
        )

        return jsonify({
            'success': True,
            **generated
        })

    except Exception as e:
        return jsonify({'error': f'Generation error: {str(e)}'}), 500


@app.route('/api/ai/generate-personalized-email', methods=['POST'])
def ai_generate_personalized_email():
    """Generate personalized email using CSV company details and campaign data"""
    try:
        data = request.json
        csv_row = data.get('csv_row', {})
        campaign_info = data.get('campaign_info', {})
        email_template = data.get('email_template', '')

        if not csv_row or not campaign_info:
            return jsonify({'error': 'Missing csv_row or campaign_info'}), 400

        assistant = get_assistant()
        generated = assistant.generate_personalized_from_csv(csv_row, campaign_info, email_template)

        return jsonify({
            'success': True,
            **generated
        })

    except Exception as e:
        return jsonify({'error': f'Generation error: {str(e)}'}), 500


@app.route('/api/ai/analyze-company', methods=['POST'])
def ai_analyze_company():
    """Analyze company for insights"""
    try:
        data = request.json
        company_data = data.get('company', {})

        assistant = get_assistant()
        analysis = assistant.analyze_company(company_data)

        return jsonify({
            'success': True,
            **analysis
        })

    except Exception as e:
        return jsonify({'error': f'Analysis error: {str(e)}'}), 500


@app.route('/api/ai/suggest-improvements', methods=['POST'])
def ai_suggest_improvements():
    """Get improvement suggestions for email"""
    try:
        data = request.json
        subject = data.get('subject', '')
        body = data.get('body', '')

        assistant = get_assistant()
        suggestions = assistant.suggest_improvements(subject, body)

        return jsonify({
            'success': True,
            'suggestions': suggestions
        })

    except Exception as e:
        return jsonify({'error': f'Suggestion error: {str(e)}'}), 500


# ============================================================================
# API ROUTES - Document Upload & Parsing
# ============================================================================

@app.route('/api/chatbot/upload-document', methods=['POST'])
def upload_document():
    """Handle campaign document upload (PDF/DOCX)"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Check file extension
    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if file_ext not in ALLOWED_DOCUMENTS:
        return jsonify({'error': 'Invalid file type. Use PDF or DOCX files'}), 400

    try:
        from werkzeug.utils import secure_filename
        filename = secure_filename(file.filename)
        filepath = os.path.join(DOCUMENTS_FOLDER, filename)
        file.save(filepath)

        # Parse the document
        parser = get_parser()
        campaign_data = parser.parse_campaign_document(filepath)

        return jsonify({
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'campaign_data': campaign_data
        })

    except Exception as e:
        return jsonify({'error': f'Error processing document: {str(e)}'}), 500


@app.route('/api/chatbot/parse-document', methods=['POST'])
def parse_document():
    """Parse an already uploaded document"""
    try:
        data = request.json
        filepath = data.get('filepath', '')

        if not filepath or not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 400

        parser = get_parser()
        campaign_data = parser.parse_campaign_document(filepath)

        # Generate email template from campaign data
        email_template = parser.generate_email_template(campaign_data)

        return jsonify({
            'success': True,
            'campaign_data': campaign_data,
            'email_template': email_template
        })

    except Exception as e:
        return jsonify({'error': f'Error parsing document: {str(e)}'}), 500


# ============================================================================
# API ROUTES - Analytics
# ============================================================================

@app.route('/api/analytics/stats', methods=['GET'])
def get_analytics_stats():
    """Get overall analytics statistics"""
    try:
        db = get_db()
        stats = db.get_campaign_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/campaigns', methods=['GET'])
def get_analytics_campaigns():
    """Get all campaigns with metrics"""
    try:
        db = get_db()
        campaigns = db.get_all_campaigns()
        return jsonify({'campaigns': campaigns})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/campaign/<campaign_id>', methods=['GET'])
def get_campaign_details(campaign_id):
    """Get detailed analytics for specific campaign"""
    try:
        db = get_db()
        stats = db.get_campaign_stats(campaign_id)
        recipients = db.get_recipient_details(campaign_id)
        hourly = db.get_hourly_stats(campaign_id)

        return jsonify({
            'stats': stats,
            'recipients': recipients,
            'hourly_stats': hourly
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/export/<campaign_id>', methods=['GET'])
def export_campaign_data(campaign_id):
    """Export campaign data as JSON (can be converted to CSV on frontend)"""
    try:
        db = get_db()
        data = db.export_campaign_data(campaign_id)

        # Set headers for download
        response = jsonify(data)
        response.headers['Content-Disposition'] = f'attachment; filename=campaign_{campaign_id}_export.json'
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/track/open/<tracking_id>', methods=['GET'])
def track_email_open(tracking_id):
    """Track email open event (pixel tracking)"""
    try:
        # Parse tracking_id format: campaignId_recipientEmail
        parts = tracking_id.split('_', 1)
        if len(parts) == 2:
            campaign_id, email = parts
            db = get_db()
            db.update_email_status(campaign_id, email, 'opened')

        # Return 1x1 transparent pixel
        from flask import send_file
        import io
        from PIL import Image

        img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)

        return send_file(img_io, mimetype='image/png')
    except Exception as e:
        # Still return pixel even on error
        return '', 204


# ============================================================================
# API ROUTES - Email Operations
# ============================================================================

@app.route('/api/emails/fetch', methods=['GET'])
def fetch_emails():
    """Fetch latest emails from Gmail"""
    try:
        from googleapiclient.discovery import build

        max_results = int(request.args.get('max', 20))

        creds = get_gmail_service()
        service = build('gmail', 'v1', credentials=creds)
        messages = list_messages(service, max_results=max_results)

        email_list = []
        for msg in messages:
            full_msg = get_message(service, msg['id'])
            email_list.append({
                'id': msg['id'],
                'thread_id': msg.get('threadId', ''),
                'subject': full_msg.get('subject', 'No Subject'),
                'from': full_msg.get('from', 'Unknown'),
                'snippet': full_msg.get('snippet', ''),
                'date': full_msg.get('date', ''),
                'body': full_msg.get('body', '')
            })

        return jsonify({
            'success': True,
            'emails': email_list,
            'total': len(email_list)
        })

    except Exception as e:
        return jsonify({'error': f'Error fetching emails: {str(e)}'}), 500


@app.route('/api/emails/send', methods=['POST'])
def send_email():
    """Send a single email"""
    try:
        from googleapiclient.discovery import build

        data = request.json
        to_email = data.get('to', '')
        subject = data.get('subject', '')
        body = data.get('body', '')

        if not to_email or not subject or not body:
            return jsonify({'error': 'Missing required fields'}), 400

        creds = get_gmail_service()
        service = build('gmail', 'v1', credentials=creds)
        message = create_message('me', to_email, subject, body)
        sent = send_message(service, 'me', message)

        return jsonify({
            'success': True,
            'message_id': sent.get('id', '')
        })

    except Exception as e:
        return jsonify({'error': f'Error sending email: {str(e)}'}), 500


# ============================================================================
# API ROUTES - Campaign Management
# ============================================================================

def send_campaign_thread(emails_data, interval=120, attachments=None):
    """Background thread for sending campaign emails"""
    global active_campaign

    from googleapiclient.discovery import build

    creds = get_gmail_service()
    service = build('gmail', 'v1', credentials=creds)
    total = len(emails_data)

    for idx, email_data in enumerate(emails_data):
        if active_campaign['status'] == 'paused':
            # Wait until resumed or cancelled
            while active_campaign['status'] == 'paused':
                time.sleep(1)

        if active_campaign['status'] == 'cancelled':
            break

        try:
            active_campaign['current_email'] = email_data['to']

            # Send email with attachments
            message = create_message('me', email_data['to'], email_data['subject'], email_data['body'], attachments)
            sent = send_message(service, 'me', message)

            active_campaign['sent'] += 1
            active_campaign['progress'].append({
                'email': email_data['to'],
                'company': email_data.get('company', ''),
                'status': 'sent',
                'time': datetime.now().isoformat()
            })

            print(f"[{idx+1}/{total}] Sent to: {email_data['to']}")

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()

            active_campaign['failed'] += 1
            active_campaign['progress'].append({
                'email': email_data['to'],
                'company': email_data.get('company', ''),
                'status': 'failed',
                'error': str(e),
                'time': datetime.now().isoformat()
            })

            print(f"[{idx+1}/{total}] Failed: {email_data['to']} - {str(e)}")
            print(f"Error details:\n{error_details}")

            # Log to file as well
            import sys
            sys.stderr.write(f"Campaign email failed: {email_data['to']}\n{error_details}\n")
            sys.stderr.flush()

        # Wait interval before next email (except for last one)
        if idx < total - 1:
            time.sleep(interval)

    # Campaign completed
    active_campaign['status'] = 'completed'

    # Save to history
    campaign_history.append({
        'date': datetime.now().isoformat(),
        'total': active_campaign['total'],
        'sent': active_campaign['sent'],
        'failed': active_campaign['failed'],
        'progress': active_campaign['progress'].copy()
    })


@app.route('/api/campaign/start', methods=['POST'])
def start_campaign():
    """Start email campaign"""
    global active_campaign

    if active_campaign['status'] == 'running':
        return jsonify({'error': 'Campaign already running'}), 400

    try:
        data = request.json
        emails = data.get('emails', [])
        interval = int(data.get('interval', 120))
        attachments = data.get('attachments', [])  # List of attachment file paths

        if not emails:
            return jsonify({'error': 'No emails provided'}), 400

        # Convert attachment filenames to full paths
        attachment_paths = []
        if attachments:
            attachments_folder = os.path.join(app.config.get('MATERIALS_FOLDER', 'uploads/materials'), 'attachments')
            for filename in attachments:
                filepath = os.path.join(attachments_folder, filename)
                if os.path.exists(filepath):
                    attachment_paths.append(filepath)
                    print(f"Added attachment: {filepath}")
                else:
                    print(f"Warning: Attachment not found: {filepath}")

        # Reset campaign state
        active_campaign = {
            'status': 'running',
            'total': len(emails),
            'sent': 0,
            'failed': 0,
            'current_email': '',
            'progress': [],
            'attachments': attachment_paths
        }

        # Start background thread
        thread = threading.Thread(target=send_campaign_thread, args=(emails, interval, attachment_paths), daemon=True)
        thread.start()

        return jsonify({
            'success': True,
            'total': len(emails),
            'message': 'Campaign started'
        })

    except Exception as e:
        return jsonify({'error': f'Error starting campaign: {str(e)}'}), 500


@app.route('/api/campaign/status', methods=['GET'])
def campaign_status():
    """Get current campaign status"""
    return jsonify({
        'success': True,
        **active_campaign
    })


@app.route('/api/campaign/pause', methods=['POST'])
def pause_campaign():
    """Pause running campaign"""
    global active_campaign

    if active_campaign['status'] == 'running':
        active_campaign['status'] = 'paused'
        return jsonify({'success': True, 'message': 'Campaign paused'})

    return jsonify({'error': 'No running campaign to pause'}), 400


@app.route('/api/campaign/resume', methods=['POST'])
def resume_campaign():
    """Resume paused campaign"""
    global active_campaign

    if active_campaign['status'] == 'paused':
        active_campaign['status'] = 'running'
        return jsonify({'success': True, 'message': 'Campaign resumed'})

    return jsonify({'error': 'No paused campaign to resume'}), 400


@app.route('/api/campaign/cancel', methods=['POST'])
def cancel_campaign():
    """Cancel running campaign"""
    global active_campaign

    if active_campaign['status'] in ['running', 'paused']:
        active_campaign['status'] = 'cancelled'
        return jsonify({'success': True, 'message': 'Campaign cancelled'})

    return jsonify({'error': 'No active campaign to cancel'}), 400


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('V2_PORT', 5001))

    print("\n" + "="*60)
    print(" Gmail Campaign Builder V2 - AI-Powered")
    print("="*60)
    print(f" Running on: http://127.0.0.1:{port}")
    print(f" AI Assistant: Groq (Llama 3.3 70B)")
    print(f" Features: Campaign Builder | Inbox | Analytics")
    print("="*60 + "\n")

    app.run(host='127.0.0.1', port=port, debug=True, use_reloader=False)
