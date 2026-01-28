# -*- coding: utf-8 -*-
"""
VBPL Web Scraper - Configuration Module
Centralized configuration for the scraping system.
"""

import os

# === Google Drive Configuration ===
DRIVE_FOLDER_ID = "1lOkT2QV0gTTMx5VLdCFof7Z5ToX3Fr4x"
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")

# === Base URLs ===
BASE_URL = "https://vbpl.vn"
ATTRIBUTES_URL = BASE_URL + "/TW/Pages/vbpq-thuoctinh.aspx?ItemID={item_id}"
RELATED_DOCS_URL = BASE_URL + "/TW/Pages/vbpq-vanbanlienquan.aspx?ItemID={item_id}"
FULL_TEXT_URL = BASE_URL + "/TW/Pages/vbpq-toanvan.aspx?ItemID={item_id}"

# === Local Folders ===
PROJECT_DIR = os.path.dirname(__file__)
TEMP_FOLDER = os.path.join(PROJECT_DIR, "temp")
DATA_FOLDER = os.path.join(PROJECT_DIR, "data")

# === Request Settings ===
REQUEST_TIMEOUT = 30
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

# === Ensure directories exist ===
os.makedirs(TEMP_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)


if __name__ == "__main__":
    print("=" * 50)
    print("🔧 VBPL Scraper Configuration")
    print("=" * 50)
    print(f"📁 Drive Folder ID: {DRIVE_FOLDER_ID}")
    print(f"🔑 Credentials File: {CREDENTIALS_FILE}")
    print(f"   Exists: {os.path.exists(CREDENTIALS_FILE)}")
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"📂 Temp Folder: {TEMP_FOLDER}")
    print(f"📂 Data Folder: {DATA_FOLDER}")
    print("=" * 50)
    
    # Test URL formatting
    test_id = "32801"
    print(f"\n📋 Sample URLs for ItemID={test_id}:")
    print(f"   Attributes: {ATTRIBUTES_URL.format(item_id=test_id)}")
    print(f"   Related: {RELATED_DOCS_URL.format(item_id=test_id)}")
    print(f"   Full Text: {FULL_TEXT_URL.format(item_id=test_id)}")
