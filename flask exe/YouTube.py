import os
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Define the scopes required for the YouTube Data API
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

def get_authenticated_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def download_video(video_url, folder_path, video_title):
    response = requests.get(video_url)
    if response.status_code == 200:
        video_path = os.path.join(folder_path, f"{video_title}.mp4")
        with open(video_path, 'wb') as f:
            f.write(response.content)
    else:
        print(f"Failed to download {video_title}")

if __name__ == "__main__":
    # Authenticate and create the YouTube service
    credentials = get_authenticated_service()
    youtube_service = build("youtube", "v3", credentials=credentials)

    # Define the folder to store YouTube content
    youtube_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'YouTube')
    if not os.path.exists(youtube_folder):
        os.mkdir(youtube_folder)

    # Retrieve playlists
    playlists_response = youtube_service.playlists().list(
        part="snippet",
        mine=True
    ).execute()

    playlists = playlists_response.get('items', [])
    for playlist in playlists:
        playlist_title = playlist['snippet']['title']
        print(f"Processing playlist: {playlist_title}")

        # Create a folder for the playlist
        playlist_folder = os.path.join(youtube_folder, playlist_title)
        if not os.path.exists(playlist_folder):
            os.mkdir(playlist_folder)

        playlist_id = playlist['id']
        playlist_items_response = youtube_service.playlistItems().list(
            part="snippet",
            playlistId=playlist_id
        ).execute()

        playlist_items = playlist_items_response.get('items', [])
        for item in playlist_items:
            video_id = item['snippet']['resourceId']['videoId']
            video_title = item['snippet']['title']
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            # Fetch video privacy status
            video_response = youtube_service.videos().list(
                part="status",
                id=video_id
            ).execute()
            privacy_status = video_response['items'][0]['status']['privacyStatus']

            # Create subfolders for different privacy statuses
            privacy_folder = os.path.join(playlist_folder, privacy_status)
            if not os.path.exists(privacy_folder):
                os.mkdir(privacy_folder)

            # Download video into the privacy subfolder
            download_video(video_url, privacy_folder, video_title)

    print("Download complete!")
