#!/usr/bin/env python3
"""
Debug Service Storage
Detailed test of service storage with logging
"""

import json
from se_letters.services.postgresql_letter_database_service import PostgreSQLLetterDatabaseService


def test_service_storage_detailed():
    """Test service storage with detailed logging"""
    print("🔍 Testing service storage with detailed logging...")
    
    connection_string = "postgresql://alexandre@localhost:5432/se_letters_dev"
    service = PostgreSQLLetterDatabaseService(connection_string)
    
    try:
        # Test letter storage
        test_letter = {
            'document_name': 'detailed_test.pdf',
            'document_title': 'Detailed Test Document',
            'source_file_path': '/detailed/test.pdf',
            'processing_time_ms': 3000,
            'extraction_confidence': 0.92
        }
        
        print(f"📝 Attempting to store letter: {test_letter['document_name']}")
        
        letter_id = service.store_letter(test_letter)
        print(f"✅ Service returned Letter ID: {letter_id}")
        
        # Immediately check if it was stored
        print(f"🔍 Checking if letter {letter_id} was actually stored...")
        
        # Use direct database query to check
        result = service.db.execute_query("SELECT * FROM letters WHERE id = %s", (letter_id,))
        print(f"📊 Direct query result: {len(result)} rows")
        
        if result:
            print(f"✅ Letter found in database: {result[0]['document_name']}")
        else:
            print("❌ Letter not found in database")
        
        # Test service retrieval
        print(f"🔍 Testing service retrieval for letter {letter_id}...")
        letter = service.get_letter_by_id(letter_id)
        
        if letter:
            print(f"✅ Service retrieval test passed - Found: {letter['document_name']}")
        else:
            print("❌ Service retrieval test failed - Letter not found")
            
    except Exception as e:
        print(f"❌ Service storage test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def main():
    """Run detailed debug test"""
    print("🐛 Running detailed PostgreSQL service storage debug test...")
    
    try:
        test_service_storage_detailed()
        
        print("🎉 Detailed debug test completed!")
        
    except Exception as e:
        print(f"❌ Detailed debug test failed: {e}")
        raise


if __name__ == "__main__":
    main() 