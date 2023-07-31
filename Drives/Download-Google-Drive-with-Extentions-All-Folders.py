import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# Define the necessary scopes and other variables
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
creds = None
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
if not creds or not creds.valid:
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

# Build the Google Drive API service
service = build('drive', 'v3', credentials=creds)

# Function to download a regular file
def download_regular_file(file_id, file_name):
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(file_name, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}%")

# Function to download a Google Docs Editors file as Microsoft Office format
def download_google_docs_file(file_id, file_name, mime_type):
    export_mime_types = {
        'application/vnd.google-apps.document': ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', '.docx'),
        'application/vnd.google-apps.spreadsheet': ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '.xlsx'),
        'application/vnd.google-apps.presentation': ('application/vnd.openxmlformats-officedocument.presentationml.presentation', '.pptx')
    }

    export_mime_type, file_extension = export_mime_types.get(mime_type)
    if not export_mime_type:
        raise ValueError(f"Export not supported for Google Docs MIME type: {mime_type}")

    request = service.files().export_media(fileId=file_id, mimeType=export_mime_type)
    file_name_with_extension = f"{file_name}{file_extension}"
    fh = io.FileIO(file_name_with_extension, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}%")

# Function to download all files and folders
def download_all_files_and_folders():
    parent_folder_name = "GDrive"
    if not os.path.exists(parent_folder_name):
        os.makedirs(parent_folder_name)

    results = service.files().list(
        q="trashed=false",  # Exclude trashed files
        fields="files(id, name, mimeType, parents)").execute()
    files = results.get('files', [])
    if not files:
        print('No files found.')
    else:
        for file in files:
            file_name = os.path.join(parent_folder_name, file['name'])
            if 'parents' in file:
                parent_id = file['parents'][0]
                if file['mimeType'] == 'application/vnd.google-apps.folder':
                    # If it's a folder, create a corresponding local folder
                    if not os.path.exists(file_name):
                        os.makedirs(file_name)
                    # Recursively download all files in the folder
                    download_all_files_and_folders_in_folder(parent_id, file_name)
                else:
                    # Check if it's a Google Docs Editors file
                    if file['mimeType'] in ['application/vnd.google-apps.document', 'application/vnd.google-apps.spreadsheet', 'application/vnd.google-apps.presentation']:
                        # If it's a Google Docs Editors file, use the export method
                        download_google_docs_file(file['id'], file_name, file['mimeType'])
                    else:
                        # If it's a regular file, download it
                        download_regular_file(file['id'], file_name)

# Function to download all files and folders in a given folder
def download_all_files_and_folders_in_folder(folder_id, parent_folder_name):
    results = service.files().list(
        q=f"trashed=false and '{folder_id}' in parents",
        fields="files(id, name, mimeType)").execute()
    files = results.get('files', [])
    if files:
        for file in files:
            file_name = os.path.join(parent_folder_name, file['name'])
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                # If it's a folder, create a corresponding local folder
                if not os.path.exists(file_name):
                    os.makedirs(file_name)
                # Recursively download all files in the folder
                download_all_files_and_folders_in_folder(file['id'], file_name)
            else:
                # Check if it's a Google Docs Editors file
                if file['mimeType'] in ['application/vnd.google-apps.document', 'application/vnd.google-apps.spreadsheet', 'application/vnd.google-apps.presentation']:
                    # If it's a Google Docs Editors file, use the export method
                    download_google_docs_file(file['id'], file_name, file['mimeType'])
                else:
                    # If it's a regular file, download it
                    download_regular_file(file['id'], file_name)

# Call the main function to download all files and folders
download_all_files_and_folders()
