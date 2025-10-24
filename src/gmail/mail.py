from email.mime.text import MIMEText
import base64

def create_message(to, subject, body):
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}

def send_message(service, to, subject, body):
    message = create_message(to, subject, body)
    sent = service.users().messages().send(userId='me', body=message).execute()
    return sent['id']

def read_message(service, msg_id):
    msg_data = service.users().messages().get(userId='me', id=msg_id).execute()
    return msg_data

def list_messages(service, max_results=5):
    results = service.users().messages().list(userId='me', maxResults=max_results).execute()
    return results.get('messages', [])

def get_message_subject(headers):
    return next((h['value'] for h in headers if h['name'] == 'Subject'), "(No Subject)")

def get_message_sender(headers):
    return next((h['value'] for h in headers if h['name'] == 'From'), "(No Sender)")