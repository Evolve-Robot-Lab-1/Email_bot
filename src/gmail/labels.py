from googleapiclient.discovery import build

def list_labels(service):
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])
    return labels

def create_label(service, label_name):
    label_object = {
        'name': label_name,
        'labelListVisibility': 'labelShow',
        'messageListVisibility': 'show'
    }
    label = service.users().labels().create(userId='me', body=label_object).execute()
    return label

def delete_label(service, label_id):
    service.users().labels().delete(userId='me', id=label_id).execute()