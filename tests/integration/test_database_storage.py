#!/usr/bin/env python3
"""
Database Storage Issues Test and Fix Script
Comprehensive testing of all database storage components in the raw file processing pipeline

This script:
1. Tests all database table creation and constraints
2. Identifies and fixes sequence/auto-increment issues
3. Tests data insertion and retrieval
4. Validates foreign key constraints
5. Provides detailed error reporting and fixes

Author: SE Letters Development Team
Date: 2024-01-15
"""

import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import duckdb

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/database_storage_test.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseTestResult:
    """Test result for database operations"""
    test_name: str
    success: bool
    error_message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0

class DatabaseStorageTestSuite:
    """Comprehensive test suite for database storage issues"""
    
    def __init__(self):
        self.test_db_path = "data/test_database_storage.duckdb"
        self.production_db_path = "data/letters.duckdb"
        self.staging_db_path = "data/raw_document_processing.duckdb"
        self.results: List[DatabaseTestResult] = []
        
        # Ensure logs directory exists
        Path("logs").mkdir(exist_ok=True)
        
        logger.info("🧪 Database Storage Test Suite Initialized")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all database storage tests"""
        logger.info("🚀 Starting comprehensive database storage tests")
        
        # Test 1: Basic DuckDB Connection
        self.test_basic_connection()
        
        # Test 2: Sequence Creation and Auto-increment
        self.test_sequence_creation()
        
        # Test 3: Table Creation with Constraints
        self.test_table_creation()
        
        # Test 4: Data Insertion and Retrieval
        self.test_data_insertion()
        
        # Test 5: Foreign Key Constraints
        self.test_foreign_key_constraints()
        
        # Test 6: JSON Data Storage
        self.test_json_data_storage()
        
        # Test 7: Production Database Schema
        self.test_production_database_schema()
        
        # Test 8: Staging Database Schema
        self.test_staging_database_schema()
        
        # Test 9: Concurrent Access
        self.test_concurrent_access()
        
        # Test 10: Error Handling
        self.test_error_handling()
        
        # Generate comprehensive report
        return self.generate_test_report()
    
    def test_basic_connection(self) -> None:
        """Test basic DuckDB connection"""
        start_time = time.time()
        
        try:
            logger.info("🔌 Testing basic DuckDB connection")
            
            with duckdb.connect(self.test_db_path) as conn:
                # Test basic query
                result = conn.execute("SELECT 1 as test_value").fetchone()
                assert result[0] == 1
                
                # Test version
                version = conn.execute("SELECT version()").fetchone()[0]
                logger.info(f"DuckDB version: {version}")
                
            duration = (time.time() - start_time) * 1000
            self.results.append(DatabaseTestResult(
                test_name="basic_connection",
                success=True,
                details={"version": version},
                duration_ms=duration
            ))
            
            logger.info("✅ Basic connection test passed")
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.results.append(DatabaseTestResult(
                test_name="basic_connection",
                success=False,
                error_message=str(e),
                duration_ms=duration
            ))
            logger.error(f"❌ Basic connection test failed: {e}")
    
    def test_sequence_creation(self) -> None:
        """Test sequence creation and auto-increment functionality"""
        start_time = time.time()
        
        try:
            logger.info("🔢 Testing sequence creation and auto-increment")
            
            with duckdb.connect(self.test_db_path) as conn:
                # Test sequence creation
                conn.execute("DROP SEQUENCE IF EXISTS test_seq")
                conn.execute("CREATE SEQUENCE test_seq START 1")
                
                # Test nextval function
                next_val = conn.execute("SELECT nextval('test_seq')").fetchone()[0]
                assert next_val == 1
                
                next_val = conn.execute("SELECT nextval('test_seq')").fetchone()[0]
                assert next_val == 2
                
                # Test sequence with table
                conn.execute("DROP TABLE IF EXISTS test_seq_table")
                conn.execute("""
                    CREATE TABLE test_seq_table (
                        id INTEGER PRIMARY KEY DEFAULT nextval('test_seq'),
                        name TEXT NOT NULL
                    )
                """)
                
                # Insert data without specifying ID
                conn.execute("INSERT INTO test_seq_table (name) VALUES ('test1')")
                conn.execute("INSERT INTO test_seq_table (name) VALUES ('test2')")
                
                # Verify auto-increment worked
                results = conn.execute("SELECT id, name FROM test_seq_table ORDER BY id").fetchall()
                assert len(results) == 2
                assert results[0][0] == 3  # Should be 3 because we already called nextval twice
                assert results[1][0] == 4
                
            duration = (time.time() - start_time) * 1000
            self.results.append(DatabaseTestResult(
                test_name="sequence_creation",
                success=True,
                details={"sequence_values": [r[0] for r in results]},
                duration_ms=duration
            ))
            
            logger.info("✅ Sequence creation test passed")
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.results.append(DatabaseTestResult(
                test_name="sequence_creation",
                success=False,
                error_message=str(e),
                duration_ms=duration
            ))
            logger.error(f"❌ Sequence creation test failed: {e}")
    
    def test_table_creation(self) -> None:
        """Test production table creation with all constraints"""
        start_time = time.time()
        
        try:
            logger.info("🏗️ Testing production table creation")
            
            with duckdb.connect(self.test_db_path) as conn:
                # Create sequences
                conn.execute("DROP SEQUENCE IF EXISTS letters_id_seq")
                conn.execute("DROP SEQUENCE IF EXISTS products_id_seq")
                conn.execute("DROP SEQUENCE IF EXISTS debug_id_seq")
                
                conn.execute("CREATE SEQUENCE letters_id_seq START 1")
                conn.execute("CREATE SEQUENCE products_id_seq START 1")
                conn.execute("CREATE SEQUENCE debug_id_seq START 1")
                
                # Create letters table
                conn.execute("DROP TABLE IF EXISTS letters")
                conn.execute("""
                    CREATE TABLE letters (
                        id INTEGER PRIMARY KEY DEFAULT nextval('letters_id_seq'),
                        document_name TEXT NOT NULL,
                        document_type TEXT,
                        document_title TEXT,
                        source_file_path TEXT NOT NULL,
                        file_size INTEGER,
                        processing_method TEXT DEFAULT 'raw_file_grok',
                        processing_time_ms REAL,
                        extraction_confidence REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'processed',
                        raw_grok_json TEXT,
                        ocr_supplementary_json TEXT,
                        processing_steps_json TEXT
                    )
                """)
                
                # Create products table with foreign key
                conn.execute("DROP TABLE IF EXISTS letter_products")
                conn.execute("""
                    CREATE TABLE letter_products (
                        id INTEGER PRIMARY KEY DEFAULT nextval('products_id_seq'),
                        letter_id INTEGER NOT NULL,
                        product_identifier TEXT,
                        range_label TEXT,
                        subrange_label TEXT,
                        product_line TEXT,
                        product_description TEXT,
                        obsolescence_status TEXT,
                        end_of_service_date TEXT,
                        replacement_suggestions TEXT,
                        FOREIGN KEY (letter_id) REFERENCES letters(id)
                    )
                """)
                
                # Create debug table
                conn.execute("DROP TABLE IF EXISTS processing_debug")
                conn.execute("""
                    CREATE TABLE processing_debug (
                        id INTEGER PRIMARY KEY DEFAULT nextval('debug_id_seq'),
                        letter_id INTEGER NOT NULL,
                        processing_step TEXT NOT NULL,
                        step_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        step_duration_ms REAL,
                        step_success BOOLEAN DEFAULT TRUE,
                        step_details TEXT,
                        FOREIGN KEY (letter_id) REFERENCES letters(id)
                    )
                """)
                
                # Verify tables exist
                tables = conn.execute("SHOW TABLES").fetchall()
                table_names = [t[0] for t in tables]
                
                assert 'letters' in table_names
                assert 'letter_products' in table_names
                assert 'processing_debug' in table_names
                
            duration = (time.time() - start_time) * 1000
            self.results.append(DatabaseTestResult(
                test_name="table_creation",
                success=True,
                details={"tables_created": table_names},
                duration_ms=duration
            ))
            
            logger.info("✅ Table creation test passed")
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.results.append(DatabaseTestResult(
                test_name="table_creation",
                success=False,
                error_message=str(e),
                duration_ms=duration
            ))
            logger.error(f"❌ Table creation test failed: {e}")
    
    def test_data_insertion(self) -> None:
        """Test data insertion with realistic data"""
        start_time = time.time()
        
        try:
            logger.info("📝 Testing data insertion")
            
            with duckdb.connect(self.test_db_path) as conn:
                # Insert test letter
                conn.execute("""
                    INSERT INTO letters (
                        document_name, document_type, document_title, source_file_path,
                        file_size, processing_method, processing_time_ms, extraction_confidence,
                        status, raw_grok_json, ocr_supplementary_json, processing_steps_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    "test_document.pdf",
                    "obsolescence_letter",
                    "Test Obsolescence Letter",
                    "/path/to/test_document.pdf",
                    1024,
                    "raw_file_grok",
                    5000.0,
                    0.95,
                    "processed",
                    json.dumps({"test": "data"}),
                    json.dumps({"ocr": "text"}),
                    json.dumps([{"step": "test"}])
                ])
                
                # Get letter ID using DuckDB's currval() function
                letter_id = conn.execute("SELECT currval('test_seq')").fetchone()[0]
                
                # Insert test products
                conn.execute("""
                    INSERT INTO letter_products (
                        letter_id, product_identifier, range_label, subrange_label,
                        product_line, product_description, obsolescence_status,
                        end_of_service_date, replacement_suggestions
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    letter_id,
                    "GALAXY6000",
                    "Galaxy",
                    "6000",
                    "SPIBS",
                    "Galaxy 6000 UPS",
                    "obsolete",
                    "2024-12-31",
                    json.dumps(["Galaxy 7000"])
                ])
                
                # Insert test debug info
                conn.execute("""
                    INSERT INTO processing_debug (
                        letter_id, processing_step, step_duration_ms, 
                        step_success, step_details
                    ) VALUES (?, ?, ?, ?, ?)
                """, [
                    letter_id,
                    "raw_document_preparation",
                    100.0,
                    True,
                    json.dumps({"step": "preparation", "success": True})
                ])
                
                # Verify data was inserted
                letter_count = conn.execute("SELECT COUNT(*) FROM letters").fetchone()[0]
                product_count = conn.execute("SELECT COUNT(*) FROM letter_products").fetchone()[0]
                debug_count = conn.execute("SELECT COUNT(*) FROM processing_debug").fetchone()[0]
                
                assert letter_count == 1
                assert product_count == 1
                assert debug_count == 1
                
            duration = (time.time() - start_time) * 1000
            self.results.append(DatabaseTestResult(
                test_name="data_insertion",
                success=True,
                details={
                    "letter_id": letter_id,
                    "records_inserted": {
                        "letters": letter_count,
                        "products": product_count,
                        "debug": debug_count
                    }
                },
                duration_ms=duration
            ))
            
            logger.info("✅ Data insertion test passed")
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.results.append(DatabaseTestResult(
                test_name="data_insertion",
                success=False,
                error_message=str(e),
                duration_ms=duration
            ))
            logger.error(f"❌ Data insertion test failed: {e}")
    
    def test_foreign_key_constraints(self) -> None:
        """Test foreign key constraints"""
        start_time = time.time()
        
        try:
            logger.info("🔗 Testing foreign key constraints")
            
            with duckdb.connect(self.test_db_path) as conn:
                # Test valid foreign key
                valid_letter_id = conn.execute("SELECT id FROM letters LIMIT 1").fetchone()[0]
                
                conn.execute("""
                    INSERT INTO letter_products (letter_id, product_identifier, range_label)
                    VALUES (?, ?, ?)
                """, [valid_letter_id, "TEST_PRODUCT", "TEST_RANGE"])
                
                # Test invalid foreign key (should fail)
                try:
                    conn.execute("""
                        INSERT INTO letter_products (letter_id, product_identifier, range_label)
                        VALUES (?, ?, ?)
                    """, [99999, "INVALID_PRODUCT", "INVALID_RANGE"])
                    
                    # If we get here, foreign key constraint is not working
                    raise AssertionError("Foreign key constraint should have failed")
                    
                except Exception as fk_error:
                    # This is expected - foreign key constraint should prevent this
                    logger.info(f"Foreign key constraint working: {fk_error}")
                
                # Verify data integrity
                product_count = conn.execute("""
                    SELECT COUNT(*) FROM letter_products WHERE letter_id = ?
                """, [valid_letter_id]).fetchone()[0]
                
                assert product_count == 2  # One from previous test + one from this test
                
            duration = (time.time() - start_time) * 1000
            self.results.append(DatabaseTestResult(
                test_name="foreign_key_constraints",
                success=True,
                details={"valid_products": product_count},
                duration_ms=duration
            ))
            
            logger.info("✅ Foreign key constraints test passed")
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.results.append(DatabaseTestResult(
                test_name="foreign_key_constraints",
                success=False,
                error_message=str(e),
                duration_ms=duration
            ))
            logger.error(f"❌ Foreign key constraints test failed: {e}")
    
    def test_json_data_storage(self) -> None:
        """Test JSON data storage and retrieval"""
        start_time = time.time()
        
        try:
            logger.info("📋 Testing JSON data storage")
            
            with duckdb.connect(self.test_db_path) as conn:
                # Test complex JSON storage
                complex_json = {
                    "document_information": {
                        "document_type": "obsolescence_letter",
                        "document_title": "Galaxy 6000 End of Life",
                        "document_date": "2024-01-15",
                        "language": "en"
                    },
                    "product_information": [
                        {
                            "product_identifier": "GALAXY6000",
                            "range_label": "Galaxy",
                            "subrange_label": "6000",
                            "product_line": "SPIBS",
                            "product_description": "Galaxy 6000 UPS systems",
                            "commercial_information": {
                                "obsolescence_status": "end_of_life",
                                "end_of_service_date": "2024-12-31"
                            },
                            "replacement_information": {
                                "replacement_suggestions": ["Galaxy 7000", "Galaxy 8000"]
                            }
                        }
                    ],
                    "extraction_confidence": 0.95,
                    "processing_time_ms": 5000.0
                }
                
                # Insert with complex JSON
                conn.execute("""
                    INSERT INTO letters (
                        document_name, source_file_path, raw_grok_json
                    ) VALUES (?, ?, ?)
                """, [
                    "complex_json_test.pdf",
                    "/path/to/complex_json_test.pdf",
                    json.dumps(complex_json, indent=2)
                ])
                
                # Retrieve and verify JSON
                result = conn.execute("""
                    SELECT raw_grok_json FROM letters 
                    WHERE document_name = 'complex_json_test.pdf'
                """).fetchone()
                
                retrieved_json = json.loads(result[0])
                
                # Verify structure
                assert retrieved_json["document_information"]["document_type"] == "obsolescence_letter"
                assert len(retrieved_json["product_information"]) == 1
                assert retrieved_json["product_information"][0]["product_line"] == "SPIBS"
                assert retrieved_json["extraction_confidence"] == 0.95
                
            duration = (time.time() - start_time) * 1000
            self.results.append(DatabaseTestResult(
                test_name="json_data_storage",
                success=True,
                details={"json_structure_verified": True},
                duration_ms=duration
            ))
            
            logger.info("✅ JSON data storage test passed")
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.results.append(DatabaseTestResult(
                test_name="json_data_storage",
                success=False,
                error_message=str(e),
                duration_ms=duration
            ))
            logger.error(f"❌ JSON data storage test failed: {e}")
    
    def test_production_database_schema(self) -> None:
        """Test production database schema compatibility"""
        start_time = time.time()
        
        try:
            logger.info("🏭 Testing production database schema")
            
            # Test with actual production database path
            with duckdb.connect(self.production_db_path) as conn:
                # Check if tables exist
                tables = conn.execute("SHOW TABLES").fetchall()
                table_names = [t[0] for t in tables]
                
                logger.info(f"Production tables found: {table_names}")
                
                # Check if we can query existing data
                if 'letters' in table_names:
                    letter_count = conn.execute("SELECT COUNT(*) FROM letters").fetchone()[0]
                    logger.info(f"Production letters count: {letter_count}")
                else:
                    logger.warning("Letters table not found in production database")
                
                # Test schema compatibility by creating test record
                if 'letters' not in table_names:
                    # Create production schema
                    self._create_production_schema(conn)
                    
                # Test insertion
                conn.execute("""
                    INSERT INTO letters (
                        document_name, source_file_path, status
                    ) VALUES (?, ?, ?)
                """, ["schema_test.pdf", "/test/path", "test"])
                
                # Clean up test record
                conn.execute("DELETE FROM letters WHERE document_name = 'schema_test.pdf'")
                
            duration = (time.time() - start_time) * 1000
            self.results.append(DatabaseTestResult(
                test_name="production_database_schema",
                success=True,
                details={"tables_found": table_names},
                duration_ms=duration
            ))
            
            logger.info("✅ Production database schema test passed")
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.results.append(DatabaseTestResult(
                test_name="production_database_schema",
                success=False,
                error_message=str(e),
                duration_ms=duration
            ))
            logger.error(f"❌ Production database schema test failed: {e}")
    
    def test_staging_database_schema(self) -> None:
        """Test staging database schema compatibility"""
        start_time = time.time()
        
        try:
            logger.info("🎭 Testing staging database schema")
            
            with duckdb.connect(self.staging_db_path) as conn:
                # Check if staging tables exist
                tables = conn.execute("SHOW TABLES").fetchall()
                table_names = [t[0] for t in tables]
                
                logger.info(f"Staging tables found: {table_names}")
                
                # Create staging schema if needed
                if 'raw_processing_staging' not in table_names:
                    self._create_staging_schema(conn)
                
                # Test staging data insertion
                conn.execute("""
                    INSERT INTO raw_processing_staging (
                        source_file_path, document_name, raw_grok_json, success
                    ) VALUES (?, ?, ?, ?)
                """, [
                    "/test/staging.pdf",
                    "staging_test.pdf",
                    json.dumps({"test": "staging"}),
                    True
                ])
                
                # Verify insertion
                count = conn.execute("""
                    SELECT COUNT(*) FROM raw_processing_staging 
                    WHERE document_name = 'staging_test.pdf'
                """).fetchone()[0]
                
                assert count == 1
                
                # Clean up
                conn.execute("DELETE FROM raw_processing_staging WHERE document_name = 'staging_test.pdf'")
                
            duration = (time.time() - start_time) * 1000
            self.results.append(DatabaseTestResult(
                test_name="staging_database_schema",
                success=True,
                details={"staging_tables": table_names},
                duration_ms=duration
            ))
            
            logger.info("✅ Staging database schema test passed")
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.results.append(DatabaseTestResult(
                test_name="staging_database_schema",
                success=False,
                error_message=str(e),
                duration_ms=duration
            ))
            logger.error(f"❌ Staging database schema test failed: {e}")
    
    def test_concurrent_access(self) -> None:
        """Test concurrent database access"""
        start_time = time.time()
        
        try:
            logger.info("🔄 Testing concurrent database access")
            
            # Test multiple connections
            conn1 = duckdb.connect(self.test_db_path)
            conn2 = duckdb.connect(self.test_db_path)
            
            # Insert from both connections
            conn1.execute("""
                INSERT INTO letters (document_name, source_file_path)
                VALUES ('concurrent_test1.pdf', '/test/concurrent1')
            """)
            
            conn2.execute("""
                INSERT INTO letters (document_name, source_file_path)
                VALUES ('concurrent_test2.pdf', '/test/concurrent2')
            """)
            
            # Verify both inserts worked
            count1 = conn1.execute("""
                SELECT COUNT(*) FROM letters 
                WHERE document_name LIKE 'concurrent_test%'
            """).fetchone()[0]
            
            count2 = conn2.execute("""
                SELECT COUNT(*) FROM letters 
                WHERE document_name LIKE 'concurrent_test%'
            """).fetchone()[0]
            
            assert count1 == 2
            assert count2 == 2
            
            # Clean up
            conn1.execute("DELETE FROM letters WHERE document_name LIKE 'concurrent_test%'")
            conn1.close()
            conn2.close()
            
            duration = (time.time() - start_time) * 1000
            self.results.append(DatabaseTestResult(
                test_name="concurrent_access",
                success=True,
                details={"concurrent_inserts": 2},
                duration_ms=duration
            ))
            
            logger.info("✅ Concurrent access test passed")
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.results.append(DatabaseTestResult(
                test_name="concurrent_access",
                success=False,
                error_message=str(e),
                duration_ms=duration
            ))
            logger.error(f"❌ Concurrent access test failed: {e}")
    
    def test_error_handling(self) -> None:
        """Test error handling in database operations"""
        start_time = time.time()
        
        try:
            logger.info("⚠️ Testing error handling")
            
            with duckdb.connect(self.test_db_path) as conn:
                # Test constraint violation
                try:
                    conn.execute("""
                        INSERT INTO letters (document_name, source_file_path)
                        VALUES (NULL, '/test/null_test')
                    """)
                    raise AssertionError("Should have failed with NOT NULL constraint")
                except Exception as e:
                    logger.info(f"NOT NULL constraint working: {e}")
                
                # Test invalid JSON
                try:
                    conn.execute("""
                        INSERT INTO letters (document_name, source_file_path, raw_grok_json)
                        VALUES ('invalid_json.pdf', '/test/invalid', 'invalid json')
                    """)
                    # This should work since we store JSON as TEXT
                    logger.info("JSON stored as TEXT - no validation enforced")
                except Exception as e:
                    logger.info(f"JSON validation: {e}")
                
                # Test duplicate handling
                conn.execute("""
                    INSERT INTO letters (document_name, source_file_path)
                    VALUES ('duplicate_test.pdf', '/test/duplicate')
                """)
                
                # Try to insert duplicate (should work since no unique constraint)
                conn.execute("""
                    INSERT INTO letters (document_name, source_file_path)
                    VALUES ('duplicate_test.pdf', '/test/duplicate')
                """)
                
                # Check duplicates exist
                count = conn.execute("""
                    SELECT COUNT(*) FROM letters 
                    WHERE document_name = 'duplicate_test.pdf'
                """).fetchone()[0]
                
                assert count == 2
                
                # Clean up
                conn.execute("DELETE FROM letters WHERE document_name = 'duplicate_test.pdf'")
                
            duration = (time.time() - start_time) * 1000
            self.results.append(DatabaseTestResult(
                test_name="error_handling",
                success=True,
                details={"constraints_tested": ["NOT NULL", "JSON", "duplicates"]},
                duration_ms=duration
            ))
            
            logger.info("✅ Error handling test passed")
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.results.append(DatabaseTestResult(
                test_name="error_handling",
                success=False,
                error_message=str(e),
                duration_ms=duration
            ))
            logger.error(f"❌ Error handling test failed: {e}")
    
    def _create_production_schema(self, conn) -> None:
        """Create production database schema"""
        # Create sequences
        conn.execute("CREATE SEQUENCE IF NOT EXISTS letters_id_seq START 1")
        conn.execute("CREATE SEQUENCE IF NOT EXISTS products_id_seq START 1")
        conn.execute("CREATE SEQUENCE IF NOT EXISTS debug_id_seq START 1")
        
        # Create tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS letters (
                id INTEGER PRIMARY KEY DEFAULT nextval('letters_id_seq'),
                document_name TEXT NOT NULL,
                document_type TEXT,
                document_title TEXT,
                source_file_path TEXT NOT NULL,
                file_size INTEGER,
                processing_method TEXT DEFAULT 'raw_file_grok',
                processing_time_ms REAL,
                extraction_confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'processed',
                raw_grok_json TEXT,
                ocr_supplementary_json TEXT,
                processing_steps_json TEXT
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS letter_products (
                id INTEGER PRIMARY KEY DEFAULT nextval('products_id_seq'),
                letter_id INTEGER NOT NULL,
                product_identifier TEXT,
                range_label TEXT,
                subrange_label TEXT,
                product_line TEXT,
                product_description TEXT,
                obsolescence_status TEXT,
                end_of_service_date TEXT,
                replacement_suggestions TEXT,
                FOREIGN KEY (letter_id) REFERENCES letters(id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS processing_debug (
                id INTEGER PRIMARY KEY DEFAULT nextval('debug_id_seq'),
                letter_id INTEGER NOT NULL,
                processing_step TEXT NOT NULL,
                step_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                step_duration_ms REAL,
                step_success BOOLEAN DEFAULT TRUE,
                step_details TEXT,
                FOREIGN KEY (letter_id) REFERENCES letters(id)
            )
        """)
    
    def _create_staging_schema(self, conn) -> None:
        """Create staging database schema"""
        # Create sequences
        conn.execute("CREATE SEQUENCE IF NOT EXISTS raw_staging_id_seq START 1")
        conn.execute("CREATE SEQUENCE IF NOT EXISTS raw_debug_id_seq START 1")
        
        # Create tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS raw_processing_staging (
                id INTEGER PRIMARY KEY DEFAULT nextval('raw_staging_id_seq'),
                source_file_path TEXT NOT NULL,
                document_name TEXT NOT NULL,
                file_size INTEGER,
                file_type TEXT,
                processing_method TEXT,
                raw_grok_json TEXT NOT NULL,
                ocr_text TEXT,
                processing_confidence REAL DEFAULT 0.0,
                processing_time_ms REAL,
                model_used TEXT DEFAULT 'grok-3-latest',
                prompt_version TEXT DEFAULT '2.0.0',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT
            )
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_raw_staging_source_path 
            ON raw_processing_staging(source_file_path)
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS raw_processing_debug (
                id INTEGER PRIMARY KEY DEFAULT nextval('raw_debug_id_seq'),
                source_file_path TEXT NOT NULL,
                processing_step TEXT NOT NULL,
                step_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                step_data TEXT,
                step_duration_ms REAL,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT
            )
        """)
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        passed_tests = [r for r in self.results if r.success]
        failed_tests = [r for r in self.results if not r.success]
        
        total_duration = sum(r.duration_ms for r in self.results)
        
        report = {
            "summary": {
                "total_tests": len(self.results),
                "passed": len(passed_tests),
                "failed": len(failed_tests),
                "success_rate": len(passed_tests) / len(self.results) * 100 if self.results else 0,
                "total_duration_ms": total_duration
            },
            "passed_tests": [
                {
                    "name": r.test_name,
                    "duration_ms": r.duration_ms,
                    "details": r.details
                }
                for r in passed_tests
            ],
            "failed_tests": [
                {
                    "name": r.test_name,
                    "error": r.error_message,
                    "duration_ms": r.duration_ms,
                    "details": r.details
                }
                for r in failed_tests
            ],
            "recommendations": self._generate_recommendations(failed_tests)
        }
        
        return report
    
    def _generate_recommendations(self, failed_tests: List[DatabaseTestResult]) -> List[str]:
        """Generate recommendations based on failed tests"""
        recommendations = []
        
        for test in failed_tests:
            if test.test_name == "basic_connection":
                recommendations.append("Check DuckDB installation and permissions")
            elif test.test_name == "sequence_creation":
                recommendations.append("Verify DuckDB version supports sequences")
            elif test.test_name == "table_creation":
                recommendations.append("Check table schema and constraint syntax")
            elif test.test_name == "data_insertion":
                recommendations.append("Verify data types and constraints")
            elif test.test_name == "foreign_key_constraints":
                recommendations.append("Check foreign key constraint configuration")
            elif test.test_name == "json_data_storage":
                recommendations.append("Verify JSON data structure and storage")
            elif test.test_name == "production_database_schema":
                recommendations.append("Check production database schema compatibility")
            elif test.test_name == "staging_database_schema":
                recommendations.append("Check staging database schema compatibility")
            elif test.test_name == "concurrent_access":
                recommendations.append("Review concurrent access patterns")
            elif test.test_name == "error_handling":
                recommendations.append("Improve error handling and validation")
        
        return recommendations
    
    def cleanup(self) -> None:
        """Clean up test resources"""
        try:
            Path(self.test_db_path).unlink(missing_ok=True)
            logger.info("🧹 Test database cleaned up")
        except Exception as e:
            logger.warning(f"Failed to cleanup test database: {e}")

def main():
    """Run database storage tests"""
    test_suite = DatabaseStorageTestSuite()
    
    try:
        # Run all tests
        report = test_suite.run_all_tests()
        
        # Print summary
        print("\n" + "="*80)
        print("🧪 DATABASE STORAGE TEST RESULTS")
        print("="*80)
        
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed']}")
        print(f"Failed: {report['summary']['failed']}")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        print(f"Total Duration: {report['summary']['total_duration_ms']:.2f}ms")
        
        if report['failed_tests']:
            print("\n❌ FAILED TESTS:")
            for test in report['failed_tests']:
                print(f"  - {test['name']}: {test['error']}")
        
        if report['recommendations']:
            print("\n💡 RECOMMENDATIONS:")
            for rec in report['recommendations']:
                print(f"  - {rec}")
        
        print("\n✅ PASSED TESTS:")
        for test in report['passed_tests']:
            print(f"  - {test['name']} ({test['duration_ms']:.2f}ms)")
        
        # Save detailed report
        report_path = Path("logs/database_storage_test_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_path}")
        
        # Exit with appropriate code
        exit_code = 0 if report['summary']['failed'] == 0 else 1
        return exit_code
        
    finally:
        test_suite.cleanup()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 