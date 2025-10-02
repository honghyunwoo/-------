import os
import pickle
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from loguru import logger

from app.config import config
from app.utils import utils

# YouTube API Scopes
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRETS_FILE = os.path.join(utils.root_dir(), "client_secret.json")


def get_credentials(user_id: str) -> Optional[Credentials]:
    """
    Retrieves or creates user credentials for YouTube API.
    """
    creds = None
    token_path = os.path.join(utils.storage_dir("tokens"), f"{user_id}_youtube_token.json")

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Failed to refresh YouTube token: {e}")
                return None
        else:
            # This part requires user interaction and is better handled in a web flow.
            # For a local script, this would open a browser window.
            # In a web app, you'd redirect the user to an auth URL.
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
                # The following line is for local execution.
                # In a web server, you would use flow.authorization_url() and handle the redirect.
                creds = flow.run_local_server(port=0)
            except Exception as e:
                logger.error(f"Failed to run OAuth flow: {e}. Ensure 'client_secret.json' is configured.")
                return None

        # Save the credentials for the next run
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return creds


def upload_video(
    user_id: str,
    file_path: str,
    title: str,
    description: str,
    tags: list,
    category_id: str = "22",
    privacy_status: str = "private",
) -> Optional[str]:
    """
    Uploads a video to YouTube.

    Args:
        user_id: The ID of the user performing the upload.
        file_path: Path to the video file.
        title: The title of the video.
        description: The description of the video.
        tags: A list of tags for the video.
        category_id: The category ID for the video.
        privacy_status: 'public', 'private', or 'unlisted'.

    Returns:
        The ID of the uploaded video, or None if it failed.
    """
    credentials = get_credentials(user_id)
    if not credentials:
        logger.error("Could not obtain YouTube API credentials.")
        return None

    try:
        youtube = build("youtube", "v3", credentials=credentials)

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": category_id,
            },
            "status": {"privacyStatus": privacy_status},
        }

        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

        request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"Uploaded {int(status.progress() * 100)}%.")

        logger.success(f"Video uploaded successfully! Video ID: {response.get('id')}")
        return response.get("id")

    except HttpError as e:
        logger.error(f"An HTTP error {e.resp.status} occurred: {e.content}")
        return None
    except Exception as e:
        logger.error(f"An error occurred during YouTube upload: {e}")
        return None