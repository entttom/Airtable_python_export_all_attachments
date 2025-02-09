import os
import requests
import json
import imghdr
import re

# API-Schlüssel sicher speichern (empfohlen: als Umgebungsvariable setzen)
API_KEY = os.getenv("AIRTABLE_API_KEY", "your_airtable_api_key_here")
BASE_ID = "your_base_id_here"
TABLE_ID = "your_table_id_here"
FIELD_NAME = "Rechnungen"  # Name des Attachment-Feldes in Airtable
FILENAME_FIELD = "Leistung"  # Feld für die Benennung der Dateien

# Airtable API URL
URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}"

# Sicherer Ordner zum Speichern der Dateien
SAVE_FOLDER = "Backup_Files"
os.makedirs(SAVE_FOLDER, exist_ok=True)

def sanitize_filename(filename):
    """Ersetzt ungültige Zeichen im Dateinamen."""
    return re.sub(r'[<>:"/\\|?*]', "_", filename)  # Ersetze ungültige Zeichen mit "_"

def download_file(url, filename):
    """Lädt eine Datei von einer URL herunter und speichert sie im Backup-Ordner."""
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Fehlermeldung ausgeben, falls der Download fehlschlägt

    # Sicheren Dateinamen erstellen
    safe_filename = sanitize_filename(filename)
    file_extension = ""

    # Prüfen, ob der Server die Dateiendung sendet
    content_type = response.headers.get("Content-Type", "")
    if "image/jpeg" in content_type:
        file_extension = ".jpg"
    elif "image/png" in content_type:
        file_extension = ".png"
    elif "application/pdf" in content_type:
        file_extension = ".pdf"
    
    full_filename = os.path.join(SAVE_FOLDER, f"{safe_filename}{file_extension}")

    # Datei in Blöcken speichern, um Speicherplatz zu sparen
    with open(full_filename, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):  # Speichert die gesamte Datei, nicht nur den ersten Chunk
            file.write(chunk)

    print(f"Heruntergeladen: {full_filename}")

def fetch_attachments():
    """Holt Anhänge aus Airtable und lädt sie in den Backup-Ordner herunter."""
    params = {}
    while True:
        response = requests.get(URL, headers={"Authorization": f"Bearer {API_KEY}"}, params=params)
        response.raise_for_status()
        data = response.json()

        for record in data.get("records", []):
            fields = record.get("fields", {})
            attachments = fields.get(FIELD_NAME)

            if attachments:
                filename = fields.get(FILENAME_FIELD, "file").replace(" ", "_")
                file_url = attachments[0]["url"]
                download_file(file_url, filename)

        # Falls es eine "offset"-Markierung gibt, gibt es weitere Einträge -> paginieren
        if "offset" in data:
            params = {"offset": data["offset"]}
        else:
            break

# Skript starten
fetch_attachments()
