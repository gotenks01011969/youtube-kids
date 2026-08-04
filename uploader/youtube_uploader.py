import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from utils.secrets import YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def retry_upload(fn, retries=3, base_delay=10):
    for attempt in range(1, retries + 1):
        try:
            return fn()
        except Exception as e:
            if attempt == retries:
                raise
            delay = base_delay * (2 ** (attempt - 1))
            print(f"⚠️ Retry {attempt}/{retries} in {delay}s")
            time.sleep(delay)


def upload_to_youtube(video_path: str, title: str, metadata: dict, privacy_status="private"):
    
    description = metadata["description"]
    tags = metadata["tags"]

    creds = Credentials(
        None,
        refresh_token=YOUTUBE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=YOUTUBE_CLIENT_ID,
        client_secret=YOUTUBE_CLIENT_SECRET,
        scopes=SCOPES,
    )

    youtube = build("youtube", "v3", credentials=creds)

    def _upload():
        request_body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "27",
            },
            "status": {
                "privacyStatus": privacy_status,
                "madeForKids": True,
                "selfDeclaredMadeForKids": True,
            }
        }

        media = MediaFileUpload(
            video_path,
            chunksize=-1,
            resumable=True,
            mimetype="video/mp4"
        )

        print(f"📤 Uploading: {title}")

        upload_request = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = upload_request.next_chunk()
            if status:
                print(f"⬆️ {int(status.progress() * 100)}%")

        print(f"✅ Uploaded! Video ID: {response['id']}")
        return response["id"]

    return retry_upload(_upload)
