import os
import base64
import email
import email.header
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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
        if decoded_title[1]:
            email_title = decoded_title_str.decode(decoded_title[1])
        else:
            email_title = decoded_title_str

        # Remove any invalid characters from the email title to create a valid file name
        email_title = ''.join(c for c in email_title if c.isalnum() or c in (' ', '-', '_'))

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

def main():
    # Step 1: Create a directory called "Gmail"
    create_gmail_directory("Gmail")

    # Step 2: Authenticate with Gmail API
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)

    # Step 3: Get the list of Gmail labels
    labels = get_gmail_labels(service)

    # Step 4: Iterate through each label and store emails in corresponding folders
    for label in labels:
        label_id = label['id']
        label_name = label['name']
        label_name = label_name.replace('/', '-')  # Replace '/' with '-' to avoid nested directories

        label_directory = os.path.join("Gmail", label_name)
        create_gmail_directory(label_directory)

        # Get emails for the label and save them as .eml files
        try:
            results = service.users().messages().list(userId='me', labelIds=[label_id]).execute()
            messages = results.get('messages', [])
            for message in messages:
                save_email_as_eml(service, message['id'], label_directory)
        except HttpError as error:
            print(f'An error occurred while fetching emails for label {label_name}: {error}')

if __name__ == '__main__':
    main()
