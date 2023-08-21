import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.credentials import Credentials
from googleapiclient.discovery import build

# Set up API and OAuth2 credentials
SCOPES = ['https://www.googleapis.com/auth/contacts.readonly']
API_SERVICE_NAME = 'people'
API_VERSION = 'v1'
CLIENT_SECRET_FILE = 'credentials.json'
TOKEN_JSON_FILE = 'token.json'

# Load or create token
def get_authenticated_service():
    if os.path.exists(TOKEN_JSON_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_JSON_FILE, SCOPES)
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_JSON_FILE, 'w') as token:
                token.write(creds.to_json())
        return build(API_SERVICE_NAME, API_VERSION, credentials=creds)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_JSON_FILE, 'w') as token:
            token.write(creds.to_json())
        return build(API_SERVICE_NAME, API_VERSION, credentials=creds)

# Export contacts
def export_contacts(user_id='people/me'):
    service = get_authenticated_service()
    results = service.people().connections().list(
        resourceName=user_id,
        pageSize=1000,
        personFields='names,emailAddresses,phoneNumbers'
    ).execute()

    if 'connections' in results:
        for person in results['connections']:
            name = person.get('names', [{}])[0].get('displayName', '')
            email = person.get('emailAddresses', [{}])[0].get('value', '')
            phone = person.get('phoneNumbers', [{}])[0].get('value', '')

            print('Name:', name)
            print('Email:', email)
            print('Phone:', phone)
            print('-' * 30)
            print(person)

# Main function
if __name__ == '__main__':
    # Use 'people/me' for authenticated user's contacts
    # Use 'people/{user_id}' for other users' contacts
    user_id = 'people/other_user_id'
    export_contacts(user_id)
