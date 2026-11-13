from app.google.service import get_goole_service, google_enabled

# Google Drive/Sheets export is optional: without GOOGLE_CREDENTIAL_PATH the
# services stay None and the export handlers reply that export is not configured.
if google_enabled():
    drive_service = get_goole_service(2)
    sheet_service = get_goole_service(1)
else:
    drive_service = None
    sheet_service = None

__all__ = [
    "drive_service",
    "sheet_service",
    "google_enabled",
]
