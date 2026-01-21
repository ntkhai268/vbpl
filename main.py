# -*- coding: utf-8 -*-
"""
VBPL Web Scraper - Main Orchestrator
Combines all modules to crawl legal documents from vbpl.vn.
"""

import os
import json
import argparse
from datetime import datetime
from typing import List

import config
import crawler_list
import crawler_detail


def save_document(document: dict, output_folder: str = None) -> str:
    """
    Save a document to a JSON file.
    
    Args:
        document: Document dictionary to save
        output_folder: Folder to save to (defaults to config.DATA_FOLDER)
        
    Returns:
        Path to saved file
    """
    if output_folder is None:
        output_folder = config.DATA_FOLDER
    
    os.makedirs(output_folder, exist_ok=True)
    
    item_id = document.get('_id', 'unknown')
    file_path = os.path.join(output_folder, f"{item_id}.json")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(document, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Saved: {file_path}")
    return file_path


import concurrent.futures

def crawl_category_and_save(category_url: str, max_items: int = None, upload_files: bool = True, max_workers: int = 5) -> List[str]:
    """
    Crawl all documents from a category and save to JSON files.
    Uses multi-threading for faster processing.
    
    Args:
        category_url: Category URL to crawl
        max_items: Maximum number of documents to process (for testing)
        upload_files: Whether to upload files to Google Drive
        max_workers: Number of concurrent threads
        
    Returns:
        List of saved file paths
    """
    print("\n" + "=" * 60)
    print("🚀 VBPL Web Scraper - Starting")
    print("=" * 60)
    print(f"📌 Category URL: {category_url}")
    print(f"📁 Output Folder: {config.DATA_FOLDER}")
    print(f"☁️ Upload Files: {upload_files}")
    print(f"⚡ Max Workers: {max_workers}")
    if max_items:
        print(f"🔢 Max Items: {max_items}")
    print("=" * 60 + "\n")
    
    # Step 1: Get all document IDs from category
    print("📋 Step 1: Extracting document IDs from category pages...")
    item_ids = crawler_list.crawl_category(category_url)
    
    if max_items:
        item_ids = item_ids[:max_items]
    
    total_items = len(item_ids)
    print(f"\n📊 Found {total_items} documents to process\n")
    
    # Step 2: Crawl documents in parallel
    saved_files = []
    success_count = 0
    error_count = 0
    
    def process_item(item_id):
        try:
            # Crawl document details
            document = crawler_detail.crawl_document(item_id, upload_files=upload_files)
            # Save to JSON
            file_path = save_document(document)
            return True, file_path
        except Exception as e:
            print(f"❌ Error processing ID {item_id}: {e}")
            return False, item_id
    
    print(f"🔄 Processing {total_items} items with {max_workers} threads...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Map item_ids to the processing function
        future_to_id = {executor.submit(process_item, item_id): item_id for item_id in item_ids}
        
        for index, future in enumerate(concurrent.futures.as_completed(future_to_id), 1):
            item_id = future_to_id[future]
            try:
                success, result = future.result()
                if success:
                    saved_files.append(result)
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                print(f"❌ Unhandled exception for ID {item_id}: {e}")
                error_count += 1
                
            # Progress update (simple count)
            if index % 1 == 0:
                print(f"   [Progress: {index}/{total_items}]")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 CRAWL SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully processed: {success_count}/{total_items}")
    print(f"❌ Errors: {error_count}/{total_items}")
    print(f"📁 Output folder: {config.DATA_FOLDER}")
    print("=" * 60)
    
    return saved_files


def crawl_single_document(item_id: str, upload_files: bool = True) -> str:
    """
    Crawl a single document by ItemID.
    
    Args:
        item_id: Document ItemID
        upload_files: Whether to upload files to Google Drive
        
    Returns:
        Path to saved JSON file
    """
    print(f"\n🔍 Crawling single document: {item_id}")
    
    document = crawler_detail.crawl_document(item_id, upload_files=upload_files)
    file_path = save_document(document)
    
    return file_path


def main():
    """Main entry point with CLI arguments."""
    parser = argparse.ArgumentParser(
        description='VBPL Web Scraper - Crawl legal documents from vbpl.vn'
    )
    
    parser.add_argument(
        '--category', '-c',
        type=str,
        help='Category URL to crawl'
    )
    
    parser.add_argument(
        '--id', '-i',
        type=str,
        help='Single ItemID to crawl'
    )
    
    parser.add_argument(
        '--max', '-m',
        type=int,
        default=None,
        help='Maximum number of items to process (for testing)'
    )
    
    parser.add_argument(
        '--workers', '-w',
        type=int,
        default=5,
        help='Number of concurrent threads (default: 5)'
    )
    
    parser.add_argument(
        '--no-upload',
        action='store_true',
        help='Skip file upload to Google Drive'
    )
    
    args = parser.parse_args()
    
    upload_files = not args.no_upload
    
    if args.id:
        # Crawl single document
        crawl_single_document(args.id, upload_files=upload_files)
    elif args.category:
        # Crawl entire category with multi-threading
        crawl_category_and_save(
            args.category, 
            max_items=args.max, 
            upload_files=upload_files,
            max_workers=args.workers
        )
    else:
        # Default: show help and run with sample
        parser.print_help()
        print("\n" + "=" * 60)
        print("🧪 Running sample crawl (1 document, no upload)...")
        print("=" * 60)
        crawl_single_document("32801", upload_files=False)


if __name__ == "__main__":
    main()
