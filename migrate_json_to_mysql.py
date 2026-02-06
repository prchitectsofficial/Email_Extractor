"""
Migration script to move data from extraction_history.json to MySQL database
Run this script once to migrate your existing JSON data to MySQL
"""

import json
import os
from pathlib import Path
from history_manager import HistoryManager
from datetime import datetime

def migrate_json_to_mysql():
    """Migrate data from JSON file to MySQL database"""
    
    # Path to JSON file
    script_dir = Path(__file__).parent
    json_file = script_dir / "extraction_history.json"
    
    # Check if JSON file exists
    if not json_file.exists():
        print("No extraction_history.json file found. Nothing to migrate.")
        return
    
    # Initialize MySQL history manager
    print("Connecting to MySQL database...")
    try:
        history_manager = HistoryManager(
            host='localhost',
            database='email_extractor',
            user='root',
            password='admin',
            port=3306
        )
        print("✓ Connected to MySQL database")
    except Exception as e:
        print(f"✗ Error connecting to MySQL: {e}")
        print("Please make sure MySQL is running and credentials are correct.")
        return
    
    # Load JSON data
    print(f"\nLoading data from {json_file}...")
    try:
        with open(json_file, 'r') as f:
            json_data = json.load(f)
        
        if not json_data or len(json_data) == 0:
            print("JSON file is empty. Nothing to migrate.")
            return
        
        print(f"✓ Found {len(json_data)} extraction(s) in JSON file")
    except Exception as e:
        print(f"✗ Error reading JSON file: {e}")
        return
    
    # Check if data already exists in MySQL
    existing_history = history_manager.load_history()
    if existing_history:
        print(f"\n⚠ Warning: Found {len(existing_history)} existing extraction(s) in MySQL database.")
        response = input("Do you want to continue? This will add JSON data to existing MySQL data. (y/n): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            return
    
    # Migrate each entry
    print("\nStarting migration...")
    migrated = 0
    failed = 0
    
    for idx, entry in enumerate(json_data, 1):
        try:
            # Extract data from JSON entry
            urls = entry.get('urls_processed', [])
            results = entry.get('results', [])
            processing_time = entry.get('processing_time', 0)
            input_method = entry.get('input_method', 'text')
            name = entry.get('name')
            
            # If no name, generate one
            if not name:
                name = f"Extraction {idx}"
            
            print(f"Migrating {idx}/{len(json_data)}: {name}...", end=" ")
            
            # Save to MySQL
            history_manager.save_extraction(
                urls=urls,
                results=results,
                processing_time=processing_time,
                input_method=input_method,
                name=name
            )
            
            migrated += 1
            print("✓")
            
        except Exception as e:
            failed += 1
            print(f"✗ Error: {e}")
    
    # Summary
    print(f"\n{'='*50}")
    print("Migration Summary:")
    print(f"  Total entries: {len(json_data)}")
    print(f"  Successfully migrated: {migrated}")
    print(f"  Failed: {failed}")
    print(f"{'='*50}")
    
    if migrated > 0:
        print("\n✓ Migration completed successfully!")
        print("Your data is now stored in MySQL database.")
        
        # Ask if user wants to backup/rename JSON file
        response = input("\nDo you want to backup the JSON file? (y/n): ")
        if response.lower() == 'y':
            backup_file = json_file.with_suffix('.json.backup')
            json_file.rename(backup_file)
            print(f"✓ JSON file backed up to: {backup_file}")
    
    # Close connection
    history_manager.close()

if __name__ == "__main__":
    print("="*50)
    print("JSON to MySQL Migration Script")
    print("="*50)
    print()
    migrate_json_to_mysql()
