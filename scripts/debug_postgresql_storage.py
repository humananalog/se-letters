#!/usr/bin/env python3
"""
Debug PostgreSQL Storage
Simple test to debug storage issues
"""

import psycopg2
from se_letters.core.postgresql_database import PostgreSQLDatabase
from se_letters.services.postgresql_letter_database_service import PostgreSQLLetterDatabaseService


def test_direct_storage():
    """Test direct PostgreSQL storage"""
    print("🔍 Testing direct PostgreSQL storage...")
    
    connection_string = "postgresql://alexandre@localhost:5432/se_letters_dev"
    
    # Test direct connection
    conn = psycopg2.connect(connection_string)
    cursor = conn.cursor()
    
    try:
        # Insert test data
        cursor.execute("""
            INSERT INTO letters (
                document_name, document_title, source_file_path, 
                processing_time_ms, extraction_confidence
            ) VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, ('debug_test.pdf', 'Debug Test', '/debug/test.pdf', 1000, 0.9))
        
        letter_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"✅ Direct storage test passed - Letter ID: {letter_id}")
        
        # Verify storage
        cursor.execute("SELECT * FROM letters WHERE id = %s", (letter_id,))
        result = cursor.fetchone()
        if result:
            print(f"✅ Verification passed - Found letter: {result[1]}")
        else:
            print("❌ Verification failed - Letter not found")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Direct storage test failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def test_service_storage():
    """Test service storage"""
    print("🔍 Testing service storage...")
    
    connection_string = "postgresql://alexandre@localhost:5432/se_letters_dev"
    service = PostgreSQLLetterDatabaseService(connection_string)
    
    try:
        # Test letter storage
        test_letter = {
            'document_name': 'service_test.pdf',
            'document_title': 'Service Test Document',
            'source_file_path': '/service/test.pdf',
            'processing_time_ms': 2000,
            'extraction_confidence': 0.85
        }
        
        letter_id = service.store_letter(test_letter)
        print(f"✅ Service storage test passed - Letter ID: {letter_id}")
        
        # Test letter retrieval
        letter = service.get_letter_by_id(letter_id)
        if letter:
            print(f"✅ Service retrieval test passed - Found: {letter['document_name']}")
        else:
            print("❌ Service retrieval test failed - Letter not found")
            
    except Exception as e:
        print(f"❌ Service storage test failed: {e}")
        raise


def main():
    """Run debug tests"""
    print("🐛 Running PostgreSQL storage debug tests...")
    
    try:
        test_direct_storage()
        test_service_storage()
        
        print("🎉 Debug tests completed!")
        
    except Exception as e:
        print(f"❌ Debug test failed: {e}")
        raise


if __name__ == "__main__":
    main() 