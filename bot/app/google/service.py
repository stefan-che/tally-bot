import os
import httplib2
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()
creds_json = os.getenv("GOOGLE_CREDENTIAL_PATH")


def google_enabled() -> bool:
    """Google export is optional: enabled only when a service-account JSON file is configured."""
    return bool(creds_json) and os.path.isfile(creds_json)


def get_goole_service(api: int = 1):
    scopes = ['https://www.googleapis.com/auth/drive',
              'https://www.googleapis.com/auth/spreadsheets']
    creds_service = ServiceAccountCredentials.from_json_keyfile_name(creds_json, scopes).authorize(httplib2.Http())

    if api == 1:
        return build('sheets', 'v4', http=creds_service)
    return build('drive', 'v3', http=creds_service)
