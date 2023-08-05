import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Define the API scopes required
SCOPES = ['https://www.googleapis.com/auth/contacts.readonly']

# Load existing credentials if available
creds = None
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)

# If credentials are not valid or not present, generate new ones interactively
if not creds or not creds.valid:
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)

    # Save the credentials for future use
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

# Build the Google Contacts API service
service = build('people', 'v1', credentials=creds)

# Function to retrieve all contacts
def get_all_contacts():
    contacts = []
    page_token = None
    while True:
        results = service.people().connections().list(resourceName='people/me', pageToken=page_token).execute()
        connections = results.get('connections', [])
        contacts.extend(connections)
        page_token = results.get('nextPageToken')
        if not page_token:
            break
    return contacts

# Function to retrieve other contacts
def get_other_contacts():
    query = 'not (resourceName:people/me)'
    contacts = []
    page_token = None
    while True:
        results = service.people().connections().list(resourceName='people/me', pageToken=page_token, query=query).execute()
        connections = results.get('connections', [])
        contacts.extend(connections)
        page_token = results.get('nextPageToken')
        if not page_token:
            break
    return contacts

# Fetch all contacts
all_contacts = get_all_contacts()

# Fetch other contacts
other_contacts = get_other_contacts()

# Now 'all_contacts' contains all the contacts, and 'other_contacts' contains contacts not part of the authenticated user's Contacts directory.

# You can process 'all_contacts' and 'other_contacts' as per your requirements, e.g., save them to files, etc.

# For more details on the 'listDirectoryPeople' method and the 'connections' resource,
# refer to the official API documentation:
# https://developers.google.com/people/api/rest/v1/people.connections/list

