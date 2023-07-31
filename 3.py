import os
import csv
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Google Contacts API Scope
SCOPES = ['https://www.googleapis.com/auth/contacts.readonly']

def get_authenticated_service():
    creds = None
    
    # Check if token.json file exists and contains valid credentials
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If no valid credentials found, prompt the user to log in
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        
        # Save the credentials to a file for future use
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    # Build the service using the obtained credentials
    service = build('people', 'v1', credentials=creds)
    return service

def export_contacts_to_csv(service, filename='contacts.csv'):
    # Get all connections (contacts)
    results = service.people().connections().list(resourceName='people/me', pageSize=2000).execute()
    connections = results.get('connections', [])

    # Open CSV file to write
    with open(filename, 'w', newline='') as csvfile:
        # CSV writer
        writer = csv.writer(csvfile)

        # Write header row
        writer.writerow(['Name', 'Email'])

        # Write contacts to rows
        for person in connections:
            names = person.get('names', [])
            if names:
                name = names[0].get('displayName')
            else:
                name = ''

            email = person.get('emailAddresses', [{'value': ''}])[0].get('value')

            writer.writerow([name, email])

    print('Contacts exported to', filename)

if __name__ == "__main__":
    # Authenticate and get the service
    service = get_authenticated_service()
    
    # Export contacts to CSV
    export_contacts_to_csv(service, filename='contacts.csv')
