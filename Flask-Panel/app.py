import os
import threading
import time
import base64
import email
import email.header
from flask import Flask, render_template, jsonify
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

app = Flask(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def create_gmail_directory(directory_name):
    if not os.path.exists(directory_name):
        os.makedirs(directory_name)

def get_gmail_labels(service):
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])
    return labels

def get_full_email_content(service, message_id):
    try:
        message = service.users().messages().get(userId='me', id=message_id, format='raw').execute()
        msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
        return msg_str
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

def save_email_as_eml(service, message_id, directory_name):
    msg_str = get_full_email_content(service, message_id)
    if msg_str:
        msg = email.message_from_bytes(msg_str)

        # Get the email title (subject) and decode it
        email_title = msg['Subject']
        decoded_title = email.header.decode_header(email_title)[0]
        decoded_title_str = decoded_title[0]

        # Convert to string if it's not already
        if not isinstance(decoded_title_str, str):
            decoded_title_str = decoded_title_str.decode()

        # Remove any invalid characters from the email title to create a valid file name
        email_title = ''.join(c for c in decoded_title_str if c.isalnum() or c in (' ', '-', '_'))

        # Save the email as a .eml file with the title as the file name
        eml_filename = os.path.join(directory_name, f"{email_title}.eml")
        with open(eml_filename, 'wb') as eml_file:
            eml_file.write(msg_str)

        # Save attachments if any
        if 'parts' in msg:
            for part in msg.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                filename = part.get_filename()
                if filename:
                    attachment = part.get_payload(decode=True)
                    with open(os.path.join(directory_name, filename), 'wb') as attachment_file:
                        attachment_file.write(attachment)

def get_gmail_messages(service, label_id):
    messages = []
    page_token = None
    while True:
        try:
            results = service.users().messages().list(userId='me', labelIds=[label_id], pageToken=page_token).execute()
            messages.extend(results.get('messages', []))
            page_token = results.get('nextPageToken')
            if not page_token:
                break
        except HttpError as error:
            print(f'An error occurred while fetching messages: {error}')
            break
    return messages

def download_gmail():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)

    create_gmail_directory("Gmail")

    labels = get_gmail_labels(service)

    for label in labels:
        label_id = label['id']
        label_name = label['name']
        label_name = label_name.replace('/', '-')

        label_directory = os.path.join("Gmail", label_name)
        create_gmail_directory(label_directory)

        messages = get_gmail_messages(service, label_id)
        total_messages = len(messages)
        progress = 0

        for message in messages:
            save_email_as_eml(service, message['id'], label_directory)
            progress += 1
            status = {
                "message": f"Downloading emails - {progress}/{total_messages} completed.",
                "progress": (progress / total_messages) * 100,
                "is_running": True,
                "downloaded_files": []  # Add an empty list for the downloaded files
            }
            with app.app_context():
                app.config['STATUS'] = status
            time.sleep(0.1)

        status = {
            "message": "Download completed!",
            "progress": 100,
            "is_running": False,
            "downloaded_files": os.listdir(label_directory)  # Update the downloaded files list
        }
        with app.app_context():
            app.config['STATUS'] = status

@app.route('/')
def index():
    status = app.config.get('STATUS', {
        "message": "Waiting for user action...",
        "progress": 0,
        "is_running": False,
        "downloaded_files": []  # Add an empty list for the downloaded files
    })
    return render_template('index.html', status=status)

@app.route('/start')
def start_download():
    status = app.config.get('STATUS', {
        "message": "Waiting for user action...",
        "progress": 0,
        "is_running": False,
        "downloaded_files": []  # Add an empty list for the downloaded files
    })
    if not status["is_running"]:
        threading.Thread(target=download_gmail).start()
    return jsonify({"message": "Download started!"})

@app.route('/status')
def get_status():
    status = app.config.get('STATUS', {
        "message": "Waiting for user action...",
        "progress": 0,
        "is_running": False,
        "downloaded_files": []  # Add an empty list for the downloaded files
    })
    return jsonify(status)

if __name__ == '__main__':
    app.config['STATUS'] = {
        "message": "Waiting for user action...",
        "progress": 0,
        "is_running": False,
        "downloaded_files": []  # Add an empty list for the downloaded files
    }
    app.run(debug=True)
