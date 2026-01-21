# -*- coding: utf-8 -*-
"""
VBPL Web Scraper - List Crawler Module
Handles pagination and extracts document IDs from category pages.
"""

import re
from typing import List, Set

import config
import utils


def get_total_pages(soup) -> int:
    """
    Parse the paging div to find total number of pages.
    
    Args:
        soup: BeautifulSoup object of the page
        
    Returns:
        Total number of pages (default 1 if not found)
    """
    paging_div = soup.find('div', class_='paging')
    
    if not paging_div:
        return 1
    
    # Find all page links
    page_links = paging_div.find_all('a')
    max_page = 1
    
    for link in page_links:
        href = link.get('href', '')
        text = link.get_text(strip=True)
        
        # Try to get page number from href parameter
        page_match = re.search(r'Page=(\d+)', href, re.IGNORECASE)
        if page_match:
            page_num = int(page_match.group(1))
            max_page = max(max_page, page_num)
        
        # Also try to parse numeric text (like "1", "2", "3"...)
        if text.isdigit():
            max_page = max(max_page, int(text))
    
    return max_page


def extract_item_ids_from_page(soup) -> List[str]:
    """
    Extract ItemIDs from document links on a category page.
    
    Args:
        soup: BeautifulSoup object of the page
        
    Returns:
        List of ItemID strings found on the page
    """
    item_ids = []
    
    # Find all title paragraphs containing document links
    title_elements = soup.find_all('p', class_='title')
    
    for title_p in title_elements:
        link = title_p.find('a')
        if link:
            href = link.get('href', '')
            item_id = utils.extract_id_from_url(href)
            if item_id:
                item_ids.append(item_id)
    
    return item_ids


def crawl_category(category_url: str, max_pages: int = None) -> List[str]:
    """
    Crawl a category URL to extract all document IDs across all pages.
    
    Args:
        category_url: Base category URL (e.g., https://vbpl.vn/TW/Pages/vanban.aspx?idLoaiVanBan=16&dvid=13)
        max_pages: Optional limit on number of pages to crawl (for testing)
        
    Returns:
        List of unique ItemIDs found
    """
    print(f"🔍 Starting category crawl: {category_url}")
    
    all_item_ids: Set[str] = set()
    
    # Get first page to determine total pages
    soup = utils.get_soup(category_url)
    total_pages = get_total_pages(soup)
    
    if max_pages:
        total_pages = min(total_pages, max_pages)
    
    print(f"📊 Total pages to process: {total_pages}")
    
    # Process first page
    ids_on_page = extract_item_ids_from_page(soup)
    all_item_ids.update(ids_on_page)
    print(f"📄 Processing Page 1/{total_pages}... Found {len(ids_on_page)} documents")
    
    # Process remaining pages
    for page_num in range(2, total_pages + 1):
        # Construct page URL
        if '?' in category_url:
            page_url = f"{category_url}&Page={page_num}"
        else:
            page_url = f"{category_url}?Page={page_num}"
        
        try:
            soup = utils.get_soup(page_url)
            ids_on_page = extract_item_ids_from_page(soup)
            all_item_ids.update(ids_on_page)
            print(f"📄 Processing Page {page_num}/{total_pages}... Found {len(ids_on_page)} documents")
        except Exception as e:
            print(f"⚠️ Error on page {page_num}: {e}")
            continue
    
    unique_ids = list(all_item_ids)
    print(f"✅ Total unique documents found: {len(unique_ids)}")
    
    return unique_ids


if __name__ == "__main__":
    print("=" * 50)
    print("🔧 Testing Crawler List Module")
    print("=" * 50)
    
    # Test with a sample category URL (Hiến pháp - id=16)
    test_url = "https://vbpl.vn/TW/Pages/vanban.aspx?idLoaiVanBan=16&dvid=13"
    
    print(f"\n📋 Testing with URL: {test_url}")
    print("   (Limited to 2 pages for testing)\n")
    
    try:
        # Limit to 2 pages for testing
        item_ids = crawl_category(test_url, max_pages=2)
        
        print(f"\n📊 Results:")
        print(f"   Found {len(item_ids)} unique document IDs")
        
        if item_ids:
            print(f"\n   Sample IDs (first 5):")
            for item_id in item_ids[:5]:
                print(f"   - {item_id}")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
