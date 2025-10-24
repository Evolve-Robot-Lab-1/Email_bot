from __future__ import print_function
import os.path
import base64
import json
import csv
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

CLIENT_ID = "1046060946765-59q4aaftde0asof388414dmm5j1kj4de.apps.googleusercontent.com"
CLIENT_SECRET = "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"

SCOPES = ['https://mail.google.com/']

def gmail_authenticate():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Require a Desktop client secrets file to avoid redirect_uri_mismatch with wrong client type
            if not os.path.exists("credentials.json"):
                raise RuntimeError(
                    "Missing credentials.json. Create a Desktop OAuth client in Google Cloud Console, "
                    "download the JSON, and place it next to this script as 'credentials.json'."
                )
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            # Use ephemeral port so redirect_uri is http://localhost:<random>/
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def read_emails(service, max_results=5):
    results = service.users().messages().list(userId='me', maxResults=max_results).execute()
    messages = results.get('messages', [])
    if not messages:
        print("No new messages found.")
        return
    print("\n📩 Latest Emails:")
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        headers = msg_data['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "(No Subject)")
        sender = next((h['value'] for h in headers if h['name'] == 'From'), "(No Sender)")
        snippet = msg_data.get('snippet', '')
        print(f"\nFrom: {sender}\nSubject: {subject}\nSnippet: {snippet}\nMessage ID: {msg['id']}\n")

def send_email(service):
    csv_file = input("Enter CSV file path (e.g., recipients.csv): ")
    
    # Check if CSV file exists
    if not os.path.exists(csv_file):
        print(f"❌ Error: CSV file '{csv_file}' not found!")
        return
    
    # Ask user which column contains email addresses
    print("\nCSV Column Options:")
    print("1. First column (simple format)")
    print("2. Third column (Company, Website, Email, Phone, Details format)")
    print("3. Specify custom column number")
    
    column_choice = input("Choose column option (1-3): ")
    
    # Determine email column index
    if column_choice == '1':
        email_column = 0
    elif column_choice == '2':
        email_column = 2  # Third column (index 2)
    elif column_choice == '3':
        try:
            email_column = int(input("Enter column number (starting from 1): ")) - 1
            if email_column < 0:
                print("❌ Invalid column number!")
                return
        except ValueError:
            print("❌ Please enter a valid number!")
            return
    else:
        print("❌ Invalid choice!")
        return
    
    # Read emails from CSV file
    recipients = []
    try:
        with open(csv_file, 'r', newline='', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            first_row = True
            
            for row in csv_reader:
                # Skip header row if it exists
                if first_row and row and any(header in str(row[0]).lower() for header in ['company', 'name', 'email']):
                    first_row = False
                    continue
                first_row = False
                
                if row and len(row) > email_column and row[email_column].strip():
                    email = row[email_column].strip()
                    # Basic email validation
                    if '@' in email and '.' in email.split('@')[1]:
                        recipients.append(email)
                    else:
                        print(f"⚠️ Warning: Invalid email format '{email}' - skipping")
        
        if not recipients:
            print("❌ No valid email addresses found in CSV file!")
            return
            
        print(f"📧 Found {len(recipients)} valid email addresses")
        
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return
    
    # Get email content
    subject = input("Enter subject: ")
    body = input("Enter message body: ")
    
    # Send email to all recipients
    success_count = 0
    failed_count = 0
    
    for recipient in recipients:
        try:
            message = MIMEText(body)
            message['to'] = recipient
            message['subject'] = subject
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            message_body = {'raw': raw_message}
            
            sent = service.users().messages().send(userId='me', body=message_body).execute()
            print(f"✅ Email sent to {recipient} - Message ID: {sent['id']}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Failed to send email to {recipient}: {e}")
            failed_count += 1
    
    print(f"\n📊 Summary: {success_count} emails sent successfully, {failed_count} failed")

def reply_email(service):
    msg_id = input("Enter the message ID to reply to: ")
    reply_text = input("Enter your reply message: ")

    original = service.users().messages().get(userId='me', id=msg_id).execute()
    headers = original['payload']['headers']
    sender = next((h['value'] for h in headers if h['name'] == 'From'), None)
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "Re: (No Subject)")

    message = MIMEText(reply_text)
    message['to'] = sender
    message['subject'] = f"Re: {subject}"
    message['In-Reply-To'] = msg_id

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {'raw': raw, 'threadId': original['threadId']}
    sent = service.users().messages().send(userId='me', body=body).execute()
    print(f"\n📨 Reply sent successfully! Message ID: {sent['id']}")

def manage_labels(service):
    print("\nLabel Options:")
    print("1. List labels")
    print("2. Create new label")
    print("3. Delete label")
    choice = input("Choose an option (1-3): ")

    if choice == '1':
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        if not labels:
            print("No labels found.")
        else:
            print("\nAvailable Labels:")
            for label in labels:
                print(f"- {label['name']} (ID: {label['id']})")

    elif choice == '2':
        name = input("Enter new label name: ")
        label_object = {'name': name}
        label = service.users().labels().create(userId='me', body=label_object).execute()
        print(f"✅ Label created: {label['name']} (ID: {label['id']})")

    elif choice == '3':
        label_id = input("Enter label ID to delete: ")
        service.users().labels().delete(userId='me', id=label_id).execute()
        print("🗑️ Label deleted successfully!")
    else:
        print("Invalid choice.")

def delete_email(service):
    msg_id = input("Enter the Message ID to delete: ")
    service.users().messages().delete(userId='me', id=msg_id).execute()
    print("🗑️ Email deleted successfully!")

if __name__ == '__main__':
    # Launch the web UI instead of terminal menu
    try:
        from web_app import create_app
        import threading
        import webbrowser

        url = 'http://127.0.0.1:5000'
        print(f"Starting web UI at {url} ...")

        def _open():
            try:
                webbrowser.open(url)
            except Exception:
                pass

        threading.Timer(1.0, _open).start()
        create_app().run(host='127.0.0.1', port=5000, debug=True)
    except Exception as e:
        # Fallback: keep CLI behavior only if web UI fails to start
        print(f"Web UI failed to start ({e}). Falling back to terminal menu.\n")
        service = gmail_authenticate()
        print("\n--- 📧 Gmail Full Integration ---")
        print("Select a functionality:")
        print("1️⃣ Read Emails")
        print("2️⃣ Send Email (from CSV file)")
        print("3️⃣ Reply to an Email")
        print("4️⃣ Manage Labels")
        print("5️⃣ Delete an Email")
        choice = input("\nEnter your choice (1-5): ")
        if choice == '1':
            read_emails(service)
        elif choice == '2':
            send_email(service)
        elif choice == '3':
            reply_email(service)
        elif choice == '4':
            manage_labels(service)
        elif choice == '5':
            delete_email(service)
        else:
            print("Invalid option. Please restart and choose between 1–5.")