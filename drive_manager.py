# -*- coding: utf-8 -*-
"""
VBPL Web Scraper - Google Drive Manager Module
Handles Google Drive authentication and file uploads.
Supports both Service Account and OAuth2 credentials.
"""

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import config

# Google Drive API scope
SCOPES = ['https://www.googleapis.com/auth/drive.file']


def authenticate():
    """
    Authenticate with Google Drive API.
    Automatically detects credential type (Service Account or OAuth2).
    
    Returns:
        Google Drive service object
    """
    creds = None
    
    # Check credential type
    if os.path.exists(config.CREDENTIALS_FILE):
        with open(config.CREDENTIALS_FILE, 'r') as f:
            cred_data = json.load(f)
        
        # Service Account credentials
        if cred_data.get('type') == 'service_account':
            print("🔐 Using Service Account authentication...")
            creds = service_account.Credentials.from_service_account_file(
                config.CREDENTIALS_FILE,
                scopes=SCOPES
            )
            service = build('drive', 'v3', credentials=creds)
            print("✅ Google Drive authenticated (Service Account)!")
            return service
    
    # OAuth2 flow (for installed/web app credentials)
    if os.path.exists(config.TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(config.TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("🔐 Starting OAuth2 authentication flow...")
            if not os.path.exists(config.CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"❌ Credentials file not found: {config.CREDENTIALS_FILE}\n"
                    "Please download credentials.json from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                config.CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        with open(config.TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            print(f"✅ Token saved to: {config.TOKEN_FILE}")
    
    service = build('drive', 'v3', credentials=creds)
    print("✅ Google Drive authenticated (OAuth2)!")
    return service


def upload_file(file_path: str, file_name: str = None, folder_id: str = None) -> str:
    """
    Upload a file to Google Drive and make it publicly viewable.
    
    Args:
        file_path: Local path to the file
        file_name: Name for the file on Drive (defaults to original name)
        folder_id: Drive folder ID (defaults to config.DRIVE_FOLDER_ID)
        
    Returns:
        webViewLink (public viewable URL) or None if failed
    """
    if folder_id is None:
        folder_id = config.DRIVE_FOLDER_ID
    
    if file_name is None:
        file_name = os.path.basename(file_path)
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None
    
    print(f"☁️ Uploading {file_name}...")
    
    try:
        service = authenticate()
        
        # File metadata
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        # Determine MIME type
        mime_type = 'application/octet-stream'
        if file_path.lower().endswith('.pdf'):
            mime_type = 'application/pdf'
        elif file_path.lower().endswith('.doc'):
            mime_type = 'application/msword'
        elif file_path.lower().endswith('.docx'):
            mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        
        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        
        # Upload file
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        file_id = file.get('id')
        
        # Set public permissions (anyone with link can view)
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        service.permissions().create(
            fileId=file_id,
            body=permission
        ).execute()
        
        web_link = file.get('webViewLink')
        print(f"✅ Upload success: {web_link}")
        
        return web_link
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return None


if __name__ == "__main__":
    print("=" * 50)
    print("🔧 Testing Drive Manager Module")
    print("=" * 50)
    
    # Test authentication
    print("\n📋 Testing authentication...")
    try:
        service = authenticate()
        print("   ✅ Authentication successful!")
        
        # List some files to verify
        results = service.files().list(
            pageSize=5,
            fields="files(id, name)"
        ).execute()
        files = results.get('files', [])
        
        print(f"\n📁 Recent files in Drive:")
        for f in files:
            print(f"   - {f['name']}")
            
    except FileNotFoundError as e:
        print(f"   ⚠️ {e}")
    except Exception as e:
        print(f"   ❌ Authentication failed: {e}")
    
    # Test upload with a sample file
    print("\n📋 Testing file upload...")
    test_file = os.path.join(config.TEMP_FOLDER, "test_upload.txt")
    
    # Create a test file
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("This is a test upload from VBPL Scraper.")
    
    try:
        link = upload_file(test_file, "vbpl_test_upload.txt")
        if link:
            print(f"   ✅ Test file uploaded: {link}")
        else:
            print("   ⚠️ Upload returned None")
    except Exception as e:
        print(f"   ❌ Upload test failed: {e}")
    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)
