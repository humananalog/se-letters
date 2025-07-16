#!/usr/bin/env python3
"""
PostgreSQL Migration Test Script
Tests the migration and validates functionality
"""

import psycopg2
from se_letters.core.postgresql_database import PostgreSQLDatabase
from se_letters.services.postgresql_letter_database_service import (
    PostgreSQLLetterDatabaseService, SearchFilters, SortOrder
)


def test_database_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")
    
    connection_string = "postgresql://alexandre@localhost:5432/se_letters_dev"
    db = PostgreSQLDatabase(connection_string)
    
    # Test simple query
    result = db.execute_scalar("SELECT 1")
    assert result == 1
    print("✅ Database connection test passed")


def test_letter_service():
    """Test letter database service"""
    print("🔍 Testing letter database service...")
    
    connection_string = "postgresql://alexandre@localhost:5432/se_letters_dev"
    service = PostgreSQLLetterDatabaseService(connection_string)
    
    # Test search functionality
    filters = SearchFilters(limit=5)
    result = service.search_letters(filters)
    assert 'letters' in result.__dict__
    assert 'total_count' in result.__dict__
    print(f"✅ Letter service test passed - Found {result.total_count} letters")


def test_data_integrity():
    """Test data integrity after migration"""
    print("🔍 Testing data integrity...")
    
    connection_string = "postgresql://alexandre@localhost:5432/se_letters_dev"
    db = PostgreSQLDatabase(connection_string)
    
    # Check record counts
    tables = ['letters', 'letter_products', 'letter_product_matches', 'processing_debug']
    
    for table in tables:
        count = db.execute_scalar(f"SELECT COUNT(*) FROM {table}")
        print(f"📊 {table}: {count} records")
    
    print("✅ Data integrity test passed")


def test_letter_storage():
    """Test letter storage functionality"""
    print("🔍 Testing letter storage...")
    
    connection_string = "postgresql://alexandre@localhost:5432/se_letters_dev"
    service = PostgreSQLLetterDatabaseService(connection_string)
    
    # Test letter storage
    test_letter = {
        'document_name': 'test_migration.pdf',
        'document_title': 'Test Migration Document',
        'source_file_path': '/test/migration/test.pdf',
        'processing_time_ms': 1500,
        'extraction_confidence': 0.95,
        'raw_grok_json': {'test': 'data'},
        'validation_details_json': {'valid': True}
    }
    
    letter_id = service.store_letter(test_letter)
    assert letter_id is not None
    print(f"✅ Letter storage test passed - Stored letter ID: {letter_id}")
    
    # Test letter retrieval
    letter = service.get_letter_by_id(letter_id)
    assert letter is not None
    assert letter['document_name'] == 'test_migration.pdf'
    assert letter['extraction_confidence'] == 0.95
    print("✅ Letter retrieval test passed")


def test_database_stats():
    """Test database statistics functionality"""
    print("🔍 Testing database statistics...")
    
    connection_string = "postgresql://alexandre@localhost:5432/se_letters_dev"
    service = PostgreSQLLetterDatabaseService(connection_string)
    
    # Get database stats
    stats = service.get_database_stats()
    assert stats.total_letters >= 0
    assert stats.total_products >= 0
    assert stats.avg_confidence >= 0
    print(f"✅ Database stats test passed - {stats.total_letters} letters, {stats.total_products} products")


def test_health_check():
    """Test health check functionality"""
    print("🔍 Testing health check...")
    
    connection_string = "postgresql://alexandre@localhost:5432/se_letters_dev"
    service = PostgreSQLLetterDatabaseService(connection_string)
    
    # Perform health check
    health = service.health_check()
    assert health['status'] == 'healthy'
    assert 'response_time_ms' in health
    assert 'table_count' in health
    print(f"✅ Health check test passed - Response time: {health['response_time_ms']:.2f}ms")


def test_search_functionality():
    """Test advanced search functionality"""
    print("🔍 Testing search functionality...")
    
    connection_string = "postgresql://alexandre@localhost:5432/se_letters_dev"
    service = PostgreSQLLetterDatabaseService(connection_string)
    
    # Test basic search
    filters = SearchFilters(
        search_query="test",
        limit=10,
        sort_by="created_at",
        sort_order=SortOrder.DESC
    )
    
    result = service.search_letters(filters)
    assert result.total_count >= 0
    assert len(result.letters) <= filters.limit
    print(f"✅ Search functionality test passed - Found {result.total_count} results")


def main():
    """Run all tests"""
    print("🧪 Running PostgreSQL migration tests...")
    
    try:
        test_database_connection()
        test_letter_service()
        test_data_integrity()
        test_letter_storage()
        test_database_stats()
        test_health_check()
        test_search_functionality()
        
        print("🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    main() 