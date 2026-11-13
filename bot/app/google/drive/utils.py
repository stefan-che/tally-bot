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
        return None  # 'Don't find Folder

    # Folder already exists, return the folder ID
    folder_id = response['files'][0]['id']

    return folder_id


def create_folder(folder_name, parent_folder_id):
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }

    if parent_folder_id:
        file_metadata['parents'] = [parent_folder_id]

    folder = drive_service.files().create(body=file_metadata).execute()
    print(f'{Fore.MAGENTA} NEW FOLDER:: {Fore.GREEN} {folder}')

    folder_id = folder['id']
    return folder_id


def add_parent_folder(fileId, parentFolderId):
    drive_service.files().update(
        fileId=fileId,
        addParents=parentFolderId,
    ).execute()


def grant_permission(fileId, email):
    permission = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': email
    }

    request = drive_service.permissions().create(fileId=fileId, body=permission)
    response = request.execute()
    print(f'{Fore.MAGENTA} Response:: {Fore.GREEN} {response}')


def grant_permission_to_all(fileId):
    drive_service.permissions().create(
        fileId=fileId,
        # read access for anyone
        body={'type': 'anyone', 'role': 'writer'},
        fields='id'
    ).execute()
