import os
from colorama import Fore
from app.google import drive_service
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

from .utils import lookup_folder, create_folder, grant_permission

load_dotenv()
root_folder_id = {}

def lookup_or_create_folder(folder_name, parent_folder_id=None, grant_write_permission=False, grant_read_permission=False):
    global root_folder_id
    if folder_name in root_folder_id:
        return root_folder_id[folder_name]
    
    try:  
        folder_id = lookup_folder(folder_name, parent_folder_id)
        
        if not folder_id:
            folder_id = create_folder(folder_name, parent_folder_id)
            
            if grant_write_permission:
                emailAddress = os.getenv("GOOGLE_SHARE_EMAIL")
                if emailAddress:
                    grant_permission(folder_id, emailAddress)
            elif grant_read_permission:
                pass
        
        root_folder_id[folder_name] = folder_id

        return folder_id

    except HttpError as e:
        print(f"An error occurred: {e}")
        return None
