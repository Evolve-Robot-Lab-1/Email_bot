def format_email(subject, body, to):
    return {
        'subject': subject,
        'body': body,
        'to': to
    }

def log_message(message):
    print(f"[LOG] {message}")

def handle_error(error):
    print(f"[ERROR] {error}")