import os
import base64
import email
import email.header
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly','https://www.googleapis.com/auth/drive.readonly']

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

        # Print the email number and title
        # print(f"Downloading email {message_id}: {email_title}")

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
    total_messages = 0  # Initialize a counter for total messages
    messages = []
    page_token = None
    while True:
        try:
            results = service.users().messages().list(userId='me', labelIds=[label_id], pageToken=page_token).execute()
            messages.extend(results.get('messages', []))
            total_messages += len(results.get('messages', []))  # Increment the counter
            page_token = results.get('nextPageToken')
            if not page_token:
                break
        except HttpError as error:
            print(f'An error occurred while fetching messages: {error}')
            break
    return total_messages, messages

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
    total_emails = 0  # Initialize a counter for total emails

    for label in labels:
        label_id = label['id']
        label_name = label['name']
        label_name = label_name.replace('/', '-')  # Replace '/' with '-' to avoid nested directories

        label_directory = os.path.join("Gmail", label_name)
        create_gmail_directory(label_directory)

        # Get emails for the label and save them as .eml files
        total_label_emails, messages = get_gmail_messages(service, label_id)
        total_emails += total_label_emails  # Update the total count

        for index, message in enumerate(messages, start=1):
            save_email_as_eml(service, message['id'], label_directory)
            print(f"Downloaded {index}/{len(messages)} emails in '{label_name}' label.")

    print(f"Total number of emails downloaded: {total_emails}")  # Print the total count

if __name__ == '__main__':
    main()
    print("Gmail Downloaded, execution completed.")
