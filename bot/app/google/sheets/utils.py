from app.google import sheet_service

def excel_create(name, sheetName=None, rows=1000, columns=20):
    if not sheetName:
        sheetName = name
    
    body = {
        'properties': {'title': name, 'locale': 'en_US'},
        'sheets': [
            {
                'properties': {
                    'sheetType': 'GRID',
                    'sheetId': 0,
                    'title': sheetName,
                    'gridProperties': {
                        'rowCount': rows,
                        'columnCount': columns
                    }
                }
            }
        ]
    }
    
    spreadsheet = sheet_service.spreadsheets().create(body=body).execute()

    return spreadsheet['spreadsheetId']


def excel_batch_update(spreadSheetId, sheetName, values, rangeEnd, rangeStart="A1"):
    return sheet_service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadSheetId,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"{sheetName}!{rangeStart}:{rangeEnd}",
                    "majorDimension": "ROWS",
                    "values": values
                }
            ]
        }).execute()
