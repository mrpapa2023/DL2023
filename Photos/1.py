import os
import io
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Define the scopes required for the Photos Library API
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']

def get_authenticated_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('photoslibrary', 'v3', credentials=creds)

def download_media(media_item):
    base_url = "https://photoslibrary.googleapis.com/v3/mediaItems/"
    download_url = base_url + media_item['id']

    response = requests.get(download_url, headers={'Authorization': 'Bearer ' + service._http.request.credentials.token})
    if response.status_code == 200:
        with open(media_item['filename'], 'wb') as f:
            f.write(response.content)
    else:
        print(f"Failed to download {media_item['filename']}")

if __name__ == "__main__":
    # Authenticate and create the Google Photos service
    service = get_authenticated_service()

    # Retrieve all albums
    albums = service.albums().list().execute().get('albums', [])
    for album in albums:
        album_id = album['id']
        album_title = album['title']
        print(f"Downloading media from album: {album_title}")

        # Retrieve all media items in the album
        media_items = service.mediaItems().search(body={'albumId': album_id}).execute().get('mediaItems', [])
        for media_item in media_items:
            download_media(media_item)

    # Retrieve all media items that are not in any album (i.e., individual photos not in albums)
    media_items_no_album = service.mediaItems().search(body={'albumId': None}).execute().get('mediaItems', [])
    for media_item in media_items_no_album:
        download_media(media_item)

    print("Download complete!")
