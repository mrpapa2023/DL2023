import os
import io
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

# Define the scopes required for the Photos Library API
SCOPES = ['https://www.googleapis.com/auth/contacts.readonly',
          'https://www.googleapis.com/auth/photoslibrary.readonly',
          'https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/drive.readonly',
          'https://www.googleapis.com/auth/youtube.readonly']def get_authenticated_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def create_gphoto_folder(root_dir):
    gphoto_dir = os.path.join(root_dir, 'GPhoto')
    if not os.path.exists(gphoto_dir):
        os.mkdir(gphoto_dir)
    return gphoto_dir

def create_album_folder(album_dir, album_title):
    album_path = os.path.join(album_dir, album_title)
    if not os.path.exists(album_path):
        os.mkdir(album_path)
    return album_path

def download_media(media_item, album_path):
    download_url = media_item['baseUrl'] + "=d"
    file_path = os.path.join(album_path, media_item['filename'])

    response = requests.get(download_url, headers={'Authorization': 'Bearer ' + credentials.token})
    if response.status_code == 200:
        with open(file_path, 'wb') as f:
            f.write(response.content)
    else:
        print(f"Failed to download {file_path}")

if __name__ == "__main__":
    # Authenticate and create the Google Photos service
    credentials = get_authenticated_service()
    photos_service = build("photoslibrary", "v1", credentials=credentials, static_discovery=False)

    # Create GPhoto directory in the root project
    root_project_dir = os.path.dirname(os.path.abspath(__file__))
    gphoto_dir = create_gphoto_folder(root_project_dir)

    # Retrieve all albums
    albums = photos_service.albums().list().execute().get('albums', [])
    for album in albums:
        album_id = album['id']
        album_title = album['title']
        print(f"Downloading media from album: {album_title}")

        # Create album directory inside GPhoto directory
        album_path = create_album_folder(gphoto_dir, album_title)

        # Retrieve all media items in the album
        media_items = photos_service.mediaItems().search(body={'albumId': album_id}).execute().get('mediaItems', [])
        for media_item in media_items:
            download_media(media_item, album_path)

    print("Download complete!")
