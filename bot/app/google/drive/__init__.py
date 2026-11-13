from colorama import Fore
from app.google import drive_service

def lookup_folder(folder_name, parent_folder_id):
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder'"
    if parent_folder_id:
        query += f" and '{parent_folder_id}' in parents"

    response = drive_service.files().list(q=query).execute()
    print(f'{Fore.MAGENTA} Response for {folder_name} {parent_folder_id or ""}:: {Fore.GREEN} {response}')
    print(Fore.BLACK)

    if not response.get('files'):
        return None # 'Don't find Folder
    
    # Folder already exists, return the folder ID
    folder_id = response['files'][0]['id']
    
    return folder_id