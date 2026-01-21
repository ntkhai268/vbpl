# -*- coding: utf-8 -*-
"""
VBPL Web Scraper - Detail Crawler Module
Core logic for extracting document attributes, related documents, and files.
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Optional

import config
import utils
import drive_manager


# Mapping of Vietnamese attribute labels to JSON keys
ATTRIBUTE_MAPPING = {
    'Tên văn bản': 'ten_van_ban',
    'Tình trạng hiệu lực': 'tinh_trang_hieu_luc',
    'Số ký hiệu': 'so_ky_hieu',
    'Ngày ban hành': 'ngay_ban_hanh',
    'Loại văn bản': 'loai_van_ban',
    'Ngày có hiệu lực': 'ngay_co_hieu_luc',
    'Nguồn thu thập': 'nguon_thu_thap',
    'Cơ quan ban hành': 'co_quan_ban_hanh',
    'Người ký': 'nguoi_ky',
    'Phạm vi': 'pham_vi',
}


def crawl_attributes(item_id: str) -> Dict[str, str]:
    """
    Extract document attributes from the thuoctinh page.
    
    Args:
        item_id: Document ItemID
        
    Returns:
        Dictionary of attribute key-value pairs
    """
    print(f"📋 Extracting attributes for ID: {item_id}")
    
    url = config.ATTRIBUTES_URL.format(item_id=item_id)
    soup = utils.get_soup(url)
    
    attributes = {}
    
    # === Method 1: Get ten_van_ban from <div class="vbProperties"> -> first <td class="title"> ===
    vb_properties = soup.find('div', class_='vbProperties')
    if vb_properties:
        title_td = vb_properties.find('td', class_='title')
        if title_td:
            attributes['ten_van_ban'] = utils.clean_text(title_td.get_text())
    
    # === Method 2: Parse rows with class="label" ===
    for row in soup.find_all('tr'):
        label_cell = row.find('td', class_='label')
        if not label_cell:
            continue
        
        label_text = utils.clean_text(label_cell.get_text())
        cells = row.find_all('td')
        
        # Handle special row: "Cơ quan ban hành/ Chức danh / Người ký"
        # Structure: [label] [co_quan] [chuc_danh] [nguoi_ky]
        if 'Cơ quan ban hành' in label_text and 'Người ký' in label_text:
            if len(cells) >= 4:
                # Cell 1: co_quan_ban_hanh (may contain <a> tag)
                co_quan_cell = cells[1]
                co_quan_link = co_quan_cell.find('a')
                if co_quan_link:
                    attributes['co_quan_ban_hanh'] = utils.clean_text(co_quan_link.get_text())
                else:
                    attributes['co_quan_ban_hanh'] = utils.clean_text(co_quan_cell.get_text())
                
                # Cell 2: chuc_danh
                chuc_danh = utils.clean_text(cells[2].get_text())
                if chuc_danh:
                    attributes['chuc_danh'] = chuc_danh
                
                # Cell 3: nguoi_ky
                attributes['nguoi_ky'] = utils.clean_text(cells[3].get_text())
            continue
        
        # Handle standard 2-column rows: [label] [value]
        if len(cells) >= 2:
            value = utils.clean_text(cells[1].get_text())
            
            # Match label to attribute mapping
            for vn_label, key in ATTRIBUTE_MAPPING.items():
                if vn_label.lower() in label_text.lower():
                    if key not in attributes or not attributes[key]:
                        attributes[key] = value
                    break
    
    # === Method 3: Fallback - look for any remaining attributes ===
    for label_text, key in ATTRIBUTE_MAPPING.items():
        if key not in attributes or not attributes[key]:
            # Try to find label text anywhere
            label_elem = soup.find(string=re.compile(rf'{re.escape(label_text)}\s*:?', re.IGNORECASE))
            if label_elem:
                parent = label_elem.find_parent('td') or label_elem.find_parent('div')
                if parent:
                    # Get next sibling or following text
                    next_td = parent.find_next_sibling('td')
                    if next_td:
                        attributes[key] = utils.clean_text(next_td.get_text())
    
    # === Method 4: Special extraction for "Hiệu lực:" and "Ngày có hiệu lực:" from list items ===
    # These are often displayed as "- Hiệu lực: value" in list format
    for li in soup.find_all('li'):
        li_text = li.get_text()
        
        # Extract "Hiệu lực:" value
        if 'Hiệu lực:' in li_text and 'Ngày' not in li_text:
            if 'tinh_trang_hieu_luc' not in attributes or not attributes['tinh_trang_hieu_luc']:
                match = re.search(r'Hiệu lực:\s*(.+)', li_text)
                if match:
                    attributes['tinh_trang_hieu_luc'] = utils.clean_text(match.group(1))
        
        # Extract "Ngày có hiệu lực:" value  
        if 'Ngày có hiệu lực:' in li_text:
            if 'ngay_co_hieu_luc' not in attributes or not attributes['ngay_co_hieu_luc']:
                match = re.search(r'Ngày có hiệu lực:\s*(.+)', li_text)
                if match:
                    attributes['ngay_co_hieu_luc'] = utils.clean_text(match.group(1))
    
    return attributes


def vietnamese_to_snake_case(text: str) -> str:
    """
    Convert Vietnamese text to snake_case key.
    Example: "Văn bản căn cứ" -> "van_ban_can_cu"
    """
    # Vietnamese character mapping
    vn_map = {
        'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
        'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
        'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
        'đ': 'd',
        'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
        'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
        'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
        'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
        'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
        'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
        'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
        'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
        'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
    }
    
    result = text.lower().strip()
    for vn_char, ascii_char in vn_map.items():
        result = result.replace(vn_char, ascii_char)
    
    # Replace spaces with underscores, remove non-alphanumeric
    result = re.sub(r'[^a-z0-9]+', '_', result)
    result = result.strip('_')
    
    return result


def crawl_related_docs(item_id: str) -> Dict[str, List[str]]:
    """
    Extract related document IDs from the vanbanlienquan page.
    
    Args:
        item_id: Document ItemID
        
    Returns:
        Dictionary with relationship types as keys and lists of ItemIDs as values.
        Only includes non-empty relationships.
    """
    print(f"🔗 Getting related docs for ID: {item_id}")
    
    url = config.RELATED_DOCS_URL.format(item_id=item_id)
    soup = utils.get_soup(url)
    
    related = {}  # Only add keys with actual data
    
    # Look for label cells that identify the relationship type
    for label_cell in soup.find_all('td', class_='label'):
        label_text = utils.clean_text(label_cell.get_text())
        
        # Convert Vietnamese label to snake_case key
        key = vietnamese_to_snake_case(label_text)
        if not key:
            continue
        
        # Look for links in the same row
        parent_row = label_cell.find_parent('tr')
        if not parent_row:
            continue
        
        ids_found = []
        for link in parent_row.find_all('a'):
            href = link.get('href', '')
            # Only process links that look like document links
            if 'ItemID' in href and ('vbpq' in href.lower() or 'van-ban' in href.lower() or 'vanban' in href.lower()):
                related_id = utils.extract_id_from_url(href)
                # Validate: must be numeric and not the current document
                if related_id and related_id.isdigit() and related_id != item_id:
                    if related_id not in ids_found:
                        ids_found.append(related_id)
        
        # Only add to result if we found IDs
        if ids_found:
            if key not in related:
                related[key] = []
            related[key].extend(ids_found)
    
    return related


def crawl_files(item_id: str, folder_id: str = None) -> Dict[str, Optional[str]]:
    """
    Download document files and upload to Google Drive.
    Only uploads .doc, .docx, .pdf files.
    Extracts .zip/.rar archives to find valid documents inside.
    
    Args:
        item_id: Document ItemID
        folder_id: Google Drive folder ID (defaults to config)
        
    Returns:
        Dictionary with 'doc_url' and 'pdf_url' (Drive links or None)
    """
    print(f"📎 Processing files for ID: {item_id}")
    
    if folder_id is None:
        folder_id = config.DRIVE_FOLDER_ID
    
    url = config.FULL_TEXT_URL.format(item_id=item_id)
    soup = utils.get_soup(url)
    
    result = {
        'doc_url': None,
        'pdf_url': None
    }
    
    # Valid file extensions to upload
    valid_extensions = ['.doc', '.docx', '.pdf']
    # Archive extensions to extract
    archive_extensions = ['.zip', '.rar']
    # Invalid extensions to skip
    invalid_extensions = ['.aspx', '.html', '.htm', '.php', '.js', '.css']
    
    # Find download links
    download_links = []
    
    for link in soup.find_all('a'):
        href = link.get('href', '')
        text = link.get_text(strip=True).lower()
        
        # Skip empty or pure dialog links (not actual downloads)
        if not href or 'ShowDialogDownload' in href:
            continue
        
        # Skip javascript: links that don't have downloadfile
        if href.startswith('javascript:') and 'downloadfile' not in href.lower():
            continue
        
        # Check for downloadfile JavaScript links (with actual file path)
        if 'downloadfile' in href.lower():
            download_links.append(href)
        # Check for direct file links
        elif href.lower().endswith(tuple(valid_extensions + archive_extensions)):
            download_links.append(href)
        # Check link text for file indicators
        elif any(ext in text for ext in ['.doc', '.pdf', 'tải về', 'download']):
            if href:
                download_links.append(href)
    
    def upload_valid_file(local_path: str) -> None:
        """Helper to upload a valid file and update result dict."""
        nonlocal result
        
        file_ext = os.path.splitext(local_path)[1].lower()
        
        # Skip if we already have this file type
        if file_ext in ['.doc', '.docx'] and result['doc_url']:
            print(f"⏭️ Already have doc file, skipping: {os.path.basename(local_path)}")
            utils.delete_file(local_path)
            return
        if file_ext == '.pdf' and result['pdf_url']:
            print(f"⏭️ Already have pdf file, skipping: {os.path.basename(local_path)}")
            utils.delete_file(local_path)
            return
        
        # Upload to Drive
        drive_link = drive_manager.upload_file(local_path, folder_id=folder_id)
        
        if drive_link:
            if file_ext in ['.doc', '.docx']:
                result['doc_url'] = drive_link
            elif file_ext == '.pdf':
                result['pdf_url'] = drive_link
        
        # Clean up local file
        utils.delete_file(local_path)
        print(f"🗑️ Cleaned up local file: {local_path}")
    
    for dl_link in download_links:
        try:
            # Download file locally
            local_path = utils.download_file_from_vbpl(dl_link)
            
            if not local_path or not os.path.exists(local_path):
                continue
            
            file_ext = os.path.splitext(local_path)[1].lower()
            
            # Skip invalid file types (like .aspx)
            if file_ext in invalid_extensions:
                print(f"⏭️ Skipping invalid file type: {os.path.basename(local_path)}")
                utils.delete_file(local_path)
                continue
            
            # Handle archives - extract and get doc/pdf files
            if file_ext in archive_extensions:
                print(f"📦 Found archive: {os.path.basename(local_path)}")
                extracted_files = utils.extract_archive(local_path)
                utils.delete_file(local_path)  # Clean up archive
                
                for extracted_path in extracted_files:
                    upload_valid_file(extracted_path)
                continue
            
            # Only upload valid document types
            if file_ext in valid_extensions:
                upload_valid_file(local_path)
            else:
                print(f"⏭️ Skipping unsupported file type: {os.path.basename(local_path)}")
                utils.delete_file(local_path)
                
        except Exception as e:
            print(f"⚠️ Error processing file {dl_link}: {e}")
    
    return result


def crawl_document(item_id: str, upload_files: bool = True) -> Dict:
    """
    Crawl all information for a single document.
    
    Args:
        item_id: Document ItemID
        upload_files: Whether to download and upload files to Drive
        
    Returns:
        Complete document dictionary matching the JSON schema
    """
    print(f"\n{'='*50}")
    print(f"🔍 Crawling details for ID: {item_id}")
    print(f"{'='*50}")
    
    # Get attributes
    thuoc_tinh = crawl_attributes(item_id)
    
    # Get related documents
    van_ban_lien_quan = crawl_related_docs(item_id)
    
    # Get and upload files
    if upload_files:
        file_links = crawl_files(item_id)
    else:
        file_links = {'doc_url': None, 'pdf_url': None}
    
    # Build final document structure
    document = {
        '_id': item_id,
        'thuoc_tinh': {
            'ten_van_ban': thuoc_tinh.get('ten_van_ban', ''),
            'tinh_trang_hieu_luc': thuoc_tinh.get('tinh_trang_hieu_luc', ''),
            'so_ky_hieu': thuoc_tinh.get('so_ky_hieu', ''),
            'ngay_ban_hanh': thuoc_tinh.get('ngay_ban_hanh', ''),
            'loai_van_ban': thuoc_tinh.get('loai_van_ban', ''),
            'ngay_co_hieu_luc': thuoc_tinh.get('ngay_co_hieu_luc', ''),
            'nguon_thu_thap': thuoc_tinh.get('nguon_thu_thap', ''),
            'co_quan_ban_hanh': thuoc_tinh.get('co_quan_ban_hanh', ''),
            'chuc_danh': thuoc_tinh.get('chuc_danh', ''),
            'nguoi_ky': thuoc_tinh.get('nguoi_ky', ''),
            'pham_vi': thuoc_tinh.get('pham_vi', ''),
        },
        'van_ban_lien_quan': van_ban_lien_quan,  # Only includes non-empty relationships
        'metadata_he_thong': {
            'ngay_crawl': datetime.now().isoformat(),
            'source_url': f"{config.BASE_URL}/TW/Pages/vbpq-van-ban-goc.aspx?ItemID={item_id}",
            'doc_url': file_links.get('doc_url'),
            'pdf_url': file_links.get('pdf_url'),
        }
    }
    
    print(f"✅ Successfully crawled document ID: {item_id}")
    return document


if __name__ == "__main__":
    print("=" * 50)
    print("🔧 Testing Crawler Detail Module")
    print("=" * 50)
    
    # Test with a sample document ID
    test_id = "32801"  # Hiến pháp 2013
    
    print(f"\n📋 Testing with ItemID: {test_id}")
    print("   (File upload disabled for testing)\n")
    
    try:
        # Test without file upload first
        document = crawl_document(test_id, upload_files=False)
        
        print(f"\n📊 Crawled Document Structure:")
        print(f"   _id: {document['_id']}")
        print(f"\n   thuoc_tinh:")
        for key, value in document['thuoc_tinh'].items():
            if value:
                print(f"      {key}: {value[:50]}..." if len(str(value)) > 50 else f"      {key}: {value}")
        
        print(f"\n   van_ban_lien_quan:")
        for key, value in document['van_ban_lien_quan'].items():
            print(f"      {key}: {len(value)} documents")
        
        print(f"\n   metadata_he_thong:")
        for key, value in document['metadata_he_thong'].items():
            print(f"      {key}: {value}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
