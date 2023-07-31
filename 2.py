from googleapiclient.discovery import build
import csv

# Credentials and service setup
from oauth2client.service_account import ServiceAccountCredentials
SCOPES = ['https://www.googleapis.com/auth/contacts.readonly']
CREDS = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPES)
service = build('contacts', 'v3', credentials=CREDS)

# Get all connections (contacts)
results = service.people().connections().list(resourceName='people/me', pageSize=2000).execute()
connections = results.get('connections', [])

# Open CSV file to write
with open('contacts.csv', 'w', newline='') as csvfile:

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

print('Contacts exported to contacts.csv')