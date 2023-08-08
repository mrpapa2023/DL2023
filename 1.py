import os
import pickle
import google.auth
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Set up API credentials
SCOPES = ['https://www.googleapis.com/auth/contacts.readonly']
CREDS_FILENAME = 'credentials.json'  # Update this to your credentials file
TOKEN_FILENAME = 'token.pickle'      # Update this to your token file (will be created)

def authenticate():
    creds = None

    if os.path.exists(TOKEN_FILENAME):
        with open(TOKEN_FILENAME, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDS_FILENAME, SCOPES)
        creds = flow.run_local_server(port=0)

        with open(TOKEN_FILENAME, 'wb') as token:
            pickle.dump(creds, token)

    return creds

def export_contacts():
    creds = authenticate()
    service = build('people', 'v1', credentials=creds)

    results = service.people().connections().list(
        resourceName='people/me',
        pageSize=1000,  # Change this to the desired page size
        personFields='names,emailAddresses').execute()

    contacts = results.get('connections', [])
    if not contacts:
        print('No contacts found.')
    else:
        for contact in contacts:
            names = contact.get('names', [])
            email_addresses = contact.get('emailAddresses', [])
            if names and email_addresses:
                name = names[0].get('displayName', 'No Name')
                email = email_addresses[0].get('value', 'No Email')
                print(f'Name: {name}, Email: {email}')

if __name__ == '__main__':
    export_contacts()
