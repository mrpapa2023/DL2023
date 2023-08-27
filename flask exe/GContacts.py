import os
import json
import csv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Set up API and OAuth2 credentials
SCOPES = ['https://www.googleapis.com/auth/contacts.readonly',
          'https://www.googleapis.com/auth/photoslibrary.readonly',
          'https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/drive.readonly',
          'https://www.googleapis.com/auth/youtube.readonly']
API_SERVICE_NAME = 'people'
API_VERSION = 'v1'
CLIENT_SECRET_FILE = 'credentials.json'
TOKEN_JSON_FILE = 'token.json'
CONTACTS_DIRECTORY = 'Gcontacts'

# Load or create token
def get_authenticated_service():
    creds = None
    if os.path.exists(TOKEN_JSON_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_JSON_FILE, SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return build(API_SERVICE_NAME, API_VERSION, credentials=creds)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_JSON_FILE, 'w') as token:
            token.write(creds.to_json())
        return build(API_SERVICE_NAME, API_VERSION, credentials=creds)

# Export contacts to JSON
def export_contacts_to_json(contacts):
    if not os.path.exists(CONTACTS_DIRECTORY):
        os.mkdir(CONTACTS_DIRECTORY)
    
    json_file_path = os.path.join(CONTACTS_DIRECTORY, 'contacts.json')
    
    with open(json_file_path, 'w') as json_file:
        json.dump(contacts, json_file, indent=4)

# Export contacts to CSV
def export_contacts_to_csv(contacts):
    if not os.path.exists(CONTACTS_DIRECTORY):
        os.mkdir(CONTACTS_DIRECTORY)
    
    csv_file_path = os.path.join(CONTACTS_DIRECTORY, 'contacts.csv')
    
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Name', 'Email', 'Phone Number', 'Address', 'Birthday', 'Organization'])

        for contact in contacts:
            names = contact.get('names', [])
            name = names[0]['displayName'] if names else ''
            
            email_addresses = contact.get('emailAddresses', [])
            email = email_addresses[0]['value'] if email_addresses else ''
            
            phone_numbers = contact.get('phoneNumbers', [])
            phone_number = phone_numbers[0]['value'] if phone_numbers else ''
            
            addresses = contact.get('addresses', [])
            address = addresses[0]['formattedValue'] if addresses else ''
            
            birthdays = contact.get('birthdays', [])
            birthday = birthdays[0]['date']['year'] if birthdays else ''
            
            organizations = contact.get('organizations', [])
            organization = organizations[0]['name'] if organizations else ''

            csv_writer.writerow([name, email, phone_number, address, birthday, organization])

# Export contacts
def export_contacts():
    service = get_authenticated_service()
    results = service.people().connections().list(
        resourceName='people/me',
        pageSize=1000,
        personFields='names,emailAddresses,phoneNumbers,addresses,birthdays,organizations'
    ).execute()

    contacts = []

    if 'connections' in results:
        if not os.path.exists(CONTACTS_DIRECTORY):
            os.mkdir(CONTACTS_DIRECTORY)

        for person in results['connections']:
            contacts.append(person)

        export_contacts_to_json(contacts)
        export_contacts_to_csv(contacts)

# Main function
if __name__ == '__main__':
    export_contacts()
