# -*- coding: utf-8 -*-
"""
VBPL Web Scraper - Utility Module
Common helper functions for requests, parsing, and file downloads.
"""

import os
import re
import time
import requests
import urllib3
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup

import config

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_soup(url: str, max_retries: int = 3) -> BeautifulSoup:
    """
    Fetch a URL and return BeautifulSoup object.
    Includes retry logic and proper headers.
    
    Args:
        url: The URL to fetch
        max_retries: Number of retry attempts
        
    Returns:
        BeautifulSoup object of the page
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(
                url,
                headers=config.REQUEST_HEADERS,
                timeout=config.REQUEST_TIMEOUT,
                verify=False  # VBPL has SSL issues
            )
            response.raise_for_status()
            response.encoding = 'utf-8'
            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as e:
            print(f"⚠️ Attempt {attempt + 1}/{max_retries} failed for {url}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                raise
    return None


def extract_id_from_url(url: str) -> str:
    """
    Extract ItemID from a VBPL URL.
    
    Args:
        url: URL containing ItemID parameter
        
    Returns:
        ItemID as string, or None if not found
    """
    if not url:
        return None
    
    # Handle relative URLs
    if url.startswith('/'):
        url = config.BASE_URL + url
    
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    
    # Try different parameter names
    for param_name in ['ItemID', 'itemid', 'ITEMID', 'itemID']:
        if param_name in params:
            return params[param_name][0]
    
    return None


def clean_text(text: str) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: Raw text string
        
    Returns:
        Cleaned text with normalized whitespace
    """
    if not text:
        return ""
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def parse_js_download_link(js_string: str) -> tuple:
    """
    Parse javascript:downloadfile(...) link to extract filename and path.
    
    Args:
        js_string: JavaScript download link string
        
    Returns:
        Tuple of (filename, download_path) or (None, None) if parsing fails
    """
    pattern = r"downloadfile\s*\(\s*'([^']+)'\s*,\s*'([^']+)'\s*\)"
    match = re.search(pattern, js_string, re.IGNORECASE)
    
    if match:
        filename = match.group(1)
        relative_path = match.group(2)
        return filename, relative_path
    
    return None, None


def download_file_from_vbpl(url_or_js_string: str, save_folder: str = None) -> str:
    """
    Download file from VBPL, handling both direct links and JavaScript links.
    
    Args:
        url_or_js_string: Direct URL or javascript:downloadfile(...) string
        save_folder: Folder to save downloaded file (defaults to config.TEMP_FOLDER)
        
    Returns:
        Local file path if successful, None otherwise
    """
    if save_folder is None:
        save_folder = config.TEMP_FOLDER
    
    os.makedirs(save_folder, exist_ok=True)
    
    # Check if it's a JavaScript download link
    if 'downloadfile' in url_or_js_string.lower():
        filename, relative_path = parse_js_download_link(url_or_js_string)
        if not filename or not relative_path:
            print(f"❌ Cannot parse JS link: {url_or_js_string}")
            return None
        download_url = config.BASE_URL + relative_path
    else:
        # Direct link
        download_url = url_or_js_string
        if download_url.startswith('/'):
            download_url = config.BASE_URL + download_url
        # Extract filename from URL
        filename = os.path.basename(urlparse(download_url).path)
    
    save_path = os.path.join(save_folder, filename)
    
    print(f"⬇️ Downloading: {filename}...")
    
    try:
        response = requests.get(
            download_url,
            headers=config.REQUEST_HEADERS,
            timeout=config.REQUEST_TIMEOUT,
            verify=False,
            stream=True
        )
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Saved to: {save_path}")
        return save_path
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None


def delete_file(file_path: str) -> bool:
    """
    Delete a local file.
    
    Args:
        file_path: Path to file to delete
        
    Returns:
        True if deleted, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        print(f"⚠️ Could not delete {file_path}: {e}")
    return False


def extract_archive(archive_path: str, extract_to: str = None) -> list:
    """
    Extract .zip or .rar archive recursively until no more archives remain.
    Only returns paths to .doc, .docx, .pdf files.
    
    Args:
        archive_path: Path to the archive file
        extract_to: Folder to extract to (defaults to config.TEMP_FOLDER)
        
    Returns:
        List of extracted file paths (only .doc, .docx, .pdf)
    """
    import zipfile
    import shutil
    
    if extract_to is None:
        extract_to = config.TEMP_FOLDER
    
    os.makedirs(extract_to, exist_ok=True)
    
    valid_extensions = ['.doc', '.docx', '.pdf']
    archive_extensions = ['.zip', '.rar']
    result_files = []
    
    file_ext = os.path.splitext(archive_path)[1].lower()
    
    if file_ext == '.zip':
        try:
            print(f"📦 Extracting ZIP: {os.path.basename(archive_path)}...")
            with zipfile.ZipFile(archive_path, 'r') as zf:
                zf.extractall(extract_to)
                
                for name in zf.namelist():
                    extracted_path = os.path.join(extract_to, name)
                    if os.path.isfile(extracted_path):
                        ext = os.path.splitext(name)[1].lower()
                        
                        # If it's another archive, extract recursively
                        if ext in archive_extensions:
                            nested_files = extract_archive(extracted_path, extract_to)
                            result_files.extend(nested_files)
                            delete_file(extracted_path)
                        # If it's a valid document, add to results
                        elif ext in valid_extensions:
                            result_files.append(extracted_path)
                            print(f"   ✅ Found: {name}")
                        # Otherwise, delete unwanted file
                        else:
                            delete_file(extracted_path)
                            
        except zipfile.BadZipFile:
            print(f"❌ Invalid ZIP file: {archive_path}")
        except Exception as e:
            print(f"❌ Error extracting ZIP: {e}")
            
    elif file_ext == '.rar':
        try:
            # Try using rarfile if available
            import rarfile
            print(f"📦 Extracting RAR: {os.path.basename(archive_path)}...")
            with rarfile.RarFile(archive_path, 'r') as rf:
                rf.extractall(extract_to)
                
                for name in rf.namelist():
                    extracted_path = os.path.join(extract_to, name)
                    if os.path.isfile(extracted_path):
                        ext = os.path.splitext(name)[1].lower()
                        
                        if ext in archive_extensions:
                            nested_files = extract_archive(extracted_path, extract_to)
                            result_files.extend(nested_files)
                            delete_file(extracted_path)
                        elif ext in valid_extensions:
                            result_files.append(extracted_path)
                            print(f"   ✅ Found: {name}")
                        else:
                            delete_file(extracted_path)
                            
        except ImportError:
            print(f"⚠️ rarfile module not installed. Cannot extract RAR files.")
            print(f"   Install with: pip install rarfile")
        except Exception as e:
            print(f"❌ Error extracting RAR: {e}")
    
    return result_files


if __name__ == "__main__":
    print("=" * 50)
    print("🔧 Testing Utils Module")
    print("=" * 50)
    
    # Test extract_id_from_url
    test_urls = [
        "https://vbpl.vn/TW/Pages/vbpq-van-ban-goc.aspx?ItemID=32801",
        "/TW/Pages/vbpq-thuoctinh.aspx?ItemID=123002&dvid=13",
        "https://vbpl.vn/TW/Pages/vanban.aspx?idLoaiVanBan=16&dvid=13",
    ]
    
    print("\n📋 Testing extract_id_from_url:")
    for url in test_urls:
        item_id = extract_id_from_url(url)
        print(f"   URL: {url[:50]}...")
        print(f"   ItemID: {item_id}")
    
    # Test parse_js_download_link
    js_link = "javascript:downloadfile('42.2017.QH14.docx','/Laws/Files/VanBanGoc/42.2017.QH14.docx')"
    print(f"\n📋 Testing parse_js_download_link:")
    print(f"   Input: {js_link}")
    filename, path = parse_js_download_link(js_link)
    print(f"   Filename: {filename}")
    print(f"   Path: {path}")
    
    # Test clean_text
    dirty_text = "  Hiến   pháp   năm   2013  "
    print(f"\n📋 Testing clean_text:")
    print(f"   Input: '{dirty_text}'")
    print(f"   Output: '{clean_text(dirty_text)}'")
    
    # Test get_soup (optional - requires network)
    print(f"\n📋 Testing get_soup (fetching sample page)...")
    try:
        soup = get_soup("https://vbpl.vn/TW/Pages/vbpq-thuoctinh.aspx?ItemID=32801")
        title = soup.find('title')
        print(f"   Page title: {title.text if title else 'N/A'}")
        print("   ✅ get_soup works!")
    except Exception as e:
        print(f"   ⚠️ Network test failed: {e}")
