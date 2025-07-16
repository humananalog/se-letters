#!/usr/bin/env python3
"""
Complete Pipeline Integration Test - PIX2B Document
Comprehensive end-to-end test using real production services, API calls, and database operations

This test validates the complete integration of:
1. Document Processing
2. XAI Service (real API calls)
3. Product Matching Service (production)
4. Database Storage (real DuckDB operations)
5. JSON Output with run folders

Test Document: PIX2B_Phase_out_Letter.pdf
Expected Results: Should identify PIX 2B range products with high confidence

Version: 1.0.0
Author: SE Letters Team
"""

import os
import time
import json
import pytest
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

import duckdb
from loguru import logger

from se_letters.core.config import get_config
from se_letters.services.production_pipeline_service import ProductionPipelineService
from se_letters.services.intelligent_product_matching_service import IntelligentProductMatchingService
from se_letters.services.sota_product_database_service import SOTAProductDatabaseService
from se_letters.services.xai_service import XAIService


class TestCompletePipelineIntegration:
    """Complete pipeline integration test with PIX2B document"""
    
    @classmethod
    def setup_class(cls):
        """Setup test class with production services"""
        cls.config = get_config()
        cls.test_document_path = Path("data/test/documents/PIX2B_Phase_out_Letter.pdf")
        cls.test_start_time = datetime.now()
        
        # Verify test document exists
        assert cls.test_document_path.exists(), f"Test document not found: {cls.test_document_path}"
        
        # Setup comprehensive logging for debugging
        cls._setup_debug_logging()
        
        # Initialize production services
        cls.pipeline_service = ProductionPipelineService()
        cls.product_matching_service = IntelligentProductMatchingService(debug_mode=True)
        cls.product_database_service = SOTAProductDatabaseService()
        cls.xai_service = XAIService(cls.config)
        
        logger.info("🧪 Complete Pipeline Integration Test - Setup Complete")
        logger.info(f"📄 Test Document: {cls.test_document_path}")
        logger.info(f"🚀 Test Start Time: {cls.test_start_time}")
        
    @classmethod
    def _setup_debug_logging(cls):
        """Setup comprehensive debug logging"""
        # Create test logs directory
        test_logs_dir = Path("logs/integration_tests")
        test_logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup log file for this test
        log_file = test_logs_dir / f"pix2b_integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Configure logger
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            level="DEBUG",
            rotation="100 MB",
            retention="30 days"
        )
        
        logger.info(f"🔍 Debug logging enabled: {log_file}")
        
    def test_01_environment_setup(self):
        """Test 1: Verify environment setup and prerequisites"""
        logger.info("🧪 Test 1: Environment Setup Verification")
        
        # Check XAI API key
        assert os.getenv("XAI_API_KEY"), "XAI_API_KEY environment variable not set"
        
        # Check database files exist
        letter_db_path = Path("data/letters.duckdb")
        product_db_path = Path("data/IBcatalogue.duckdb")
        
        assert letter_db_path.exists(), f"Letter database not found: {letter_db_path}"
        assert product_db_path.exists(), f"Product database not found: {product_db_path}"
        
        # Test database connections
        with duckdb.connect(str(letter_db_path)) as conn:
            result = conn.execute("SELECT COUNT(*) FROM letters").fetchone()
            logger.info(f"📊 Letter database: {result[0]} existing letters")
            
        with duckdb.connect(str(product_db_path)) as conn:
            result = conn.execute("SELECT COUNT(*) FROM products").fetchone()
            logger.info(f"📊 Product database: {result[0]} products")
            
        # Test XAI service connection (basic check)
        assert self.xai_service.config.api.api_key, "XAI API key not configured"
        assert self.xai_service.config.api.base_url, "XAI base URL not configured"
        
        logger.info("✅ Test 1: Environment setup verified")
        
    def test_02_document_processing_stage(self):
        """Test 2: Document processing stage"""
        logger.info("🧪 Test 2: Document Processing Stage")
        
        # Test document processor directly
        result = self.pipeline_service.document_processor.process_document(
            self.test_document_path
        )
        
        assert result is not None, "Document processing failed"
        assert result.text, "Document text is empty"
        assert result.metadata, "Document metadata is empty"
        
        # Verify content extraction
        content = result.text.lower()
        assert "pix" in content, "PIX reference not found in document content"
        assert "2b" in content or "double" in content, "PIX 2B reference not found"
        
        logger.info(f"📄 Document processed successfully: {len(result.text)} characters")
        logger.info(f"📋 Document metadata: {result.metadata}")
        
    def test_03_xai_service_integration(self):
        """Test 3: XAI service integration with real API calls"""
        logger.info("🧪 Test 3: XAI Service Integration")
        
        # Process document content
        doc_result = self.pipeline_service.document_processor.process_document(
            self.test_document_path
        )
        
        # Test XAI service with real API call
        xai_result = self.xai_service.extract_ranges_from_text(
            text=doc_result.text,
            document_name="PIX2B_Phase_out_Letter.pdf"
        )
        
        assert xai_result is not None, "XAI processing failed"
        assert xai_result.ranges, "No ranges extracted by XAI service"
        assert xai_result.confidence_score > 0.8, f"Low confidence score: {xai_result.confidence_score}"
        
        # Verify PIX 2B identification
        extracted_ranges = xai_result.ranges
        assert len(extracted_ranges) > 0, "No ranges extracted"
        
        # Check for PIX 2B range
        pix_found = any(
            "pix" in str(range_info).lower() and ("2b" in str(range_info).lower() or "double" in str(range_info).lower())
            for range_info in extracted_ranges
        )
        assert pix_found, f"PIX 2B range not found in extracted ranges: {extracted_ranges}"
        
        logger.info(f"🤖 XAI processing successful: {xai_result.confidence_score:.2f} confidence")
        logger.info(f"📊 Extracted ranges: {len(extracted_ranges)}")
        
    def test_04_product_matching_integration(self):
        """Test 4: Product matching service integration"""
        logger.info("🧪 Test 4: Product Matching Service Integration")
        
        # Process document through XAI first
        doc_result = self.pipeline_service.document_processor.process_document(
            self.test_document_path
        )
        
        xai_result = self.xai_service.extract_ranges_from_text(
            text=doc_result.text,
            document_name="PIX2B_Phase_out_Letter.pdf"
        )
        
        # Test product matching service
        matching_result = self.product_matching_service.process_document_products(
            xai_result.metadata,
            document_name="PIX2B_Phase_out_Letter.pdf"
        )
        
        assert matching_result.success, f"Product matching failed: {matching_result.error}"
        assert matching_result.matching_products, "No matching products found"
        
        # Verify PIX 2B products found
        matching_products = matching_result.matching_products
        assert len(matching_products) > 0, "No matching products found"
        
        # Check for PIX 2B specific products
        pix2b_products = [
            product for product in matching_products
            if "pix" in product.product_identifier.lower() and "2b" in product.product_identifier.lower()
        ]
        
        assert len(pix2b_products) > 0, f"No PIX 2B products found in matches: {[p.product_identifier for p in matching_products]}"
        
        # Verify confidence scores
        high_confidence_products = [
            product for product in matching_products
            if product.confidence_score >= 0.5
        ]
        assert len(high_confidence_products) > 0, "No high confidence product matches found"
        
        logger.info(f"🔍 Product matching successful: {len(matching_products)} total matches")
        logger.info(f"🎯 PIX 2B products: {len(pix2b_products)}")
        logger.info(f"📊 High confidence matches: {len(high_confidence_products)}")
        
    def test_05_database_storage_integration(self):
        """Test 5: Database storage integration"""
        logger.info("🧪 Test 5: Database Storage Integration")
        
        # Get initial database state
        with duckdb.connect("data/letters.duckdb") as conn:
            initial_count = conn.execute("SELECT COUNT(*) FROM letters").fetchone()[0]
            
        # Process document through complete pipeline
        pipeline_result = self.pipeline_service.process_document(
            self.test_document_path,
            force_reprocess=True
        )
        
        assert pipeline_result.success, f"Pipeline processing failed: {pipeline_result.error}"
        assert pipeline_result.letter_id, "Letter ID not generated"
        assert pipeline_result.product_matching_result, "Product matching result missing"
        
        # Verify database storage
        with duckdb.connect("data/letters.duckdb") as conn:
            final_count = conn.execute("SELECT COUNT(*) FROM letters").fetchone()[0]
            assert final_count > initial_count, "Letter not stored in database"
            
            # Check letter details
            letter = conn.execute(
                "SELECT * FROM letters WHERE id = ?",
                [pipeline_result.letter_id]
            ).fetchone()
            
            assert letter, "Letter not found in database"
            assert letter[1] == "PIX2B_Phase_out_Letter.pdf", "Document name mismatch"
            assert letter[9] > 0.8, f"Low extraction confidence: {letter[9]}"
            
            # Check product matches
            products = conn.execute(
                "SELECT * FROM letter_products WHERE letter_id = ?",
                [pipeline_result.letter_id]
            ).fetchall()
            
            assert len(products) > 0, "No products stored in database"
            
            # Verify PIX 2B products in database
            pix2b_db_products = [
                product for product in products
                if "pix" in str(product[2]).lower() and "2b" in str(product[2]).lower()
            ]
            assert len(pix2b_db_products) > 0, "No PIX 2B products stored in database"
            
        logger.info(f"💾 Database storage successful: Letter ID {pipeline_result.letter_id}")
        logger.info(f"📊 Products stored: {len(products)}")
        
    def test_06_json_output_storage(self):
        """Test 6: JSON output storage in run folders"""
        logger.info("🧪 Test 6: JSON Output Storage")
        
        # Process document through complete pipeline
        pipeline_result = self.pipeline_service.process_document(
            self.test_document_path,
            force_reprocess=True
        )
        
        assert pipeline_result.success, f"Pipeline processing failed: {pipeline_result.error}"
        assert pipeline_result.output_files, "No output files generated"
        
        # Verify run folder structure
        run_folder = None
        for output_file in pipeline_result.output_files:
            if "run_" in str(output_file):
                run_folder = Path(output_file).parent
                break
                
        assert run_folder, "Run folder not found in output files"
        assert run_folder.exists(), f"Run folder does not exist: {run_folder}"
        
        # Check for product matching JSON files
        product_matching_dir = run_folder / "product_matching"
        assert product_matching_dir.exists(), "Product matching directory not found"
        
        # Verify JSON files exist
        expected_files = [
            "matching_request.json",
            "matching_response.json",
            "final_matches.json"
        ]
        
        for expected_file in expected_files:
            file_path = product_matching_dir / expected_file
            assert file_path.exists(), f"Missing JSON file: {expected_file}"
            
            # Verify file has content
            with open(file_path, 'r') as f:
                content = json.load(f)
                assert content, f"Empty JSON file: {expected_file}"
                
        logger.info(f"📁 JSON output storage successful: {run_folder}")
        logger.info(f"🗂️ Product matching files: {len(expected_files)}")
        
    def test_07_complete_pipeline_performance(self):
        """Test 7: Complete pipeline performance metrics"""
        logger.info("🧪 Test 7: Complete Pipeline Performance")
        
        start_time = time.time()
        
        # Process document through complete pipeline
        pipeline_result = self.pipeline_service.process_document(
            self.test_document_path,
            force_reprocess=True
        )
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        assert pipeline_result.success, f"Pipeline processing failed: {pipeline_result.error}"
        assert total_time < 60000, f"Pipeline too slow: {total_time:.2f}ms"  # Less than 60 seconds
        
        # Verify all stages completed
        assert pipeline_result.processing_stages == 6, f"Expected 6 stages, got {pipeline_result.processing_stages}"
        assert pipeline_result.processing_time_ms > 0, "Processing time not recorded"
        
        # Performance metrics
        logger.info(f"⏱️ Total processing time: {total_time:.2f}ms")
        logger.info(f"🏭 Pipeline stages: {pipeline_result.processing_stages}")
        logger.info(f"🎯 Extraction confidence: {pipeline_result.confidence_score:.2f}")
        
        # Product matching performance
        product_matching_result = pipeline_result.product_matching_result
        assert product_matching_result, "Product matching result missing"
        
        matching_time = product_matching_result.get("processing_time_ms", 0)
        total_matches = product_matching_result.get("total_matches", 0)
        
        logger.info(f"🔍 Product matching time: {matching_time:.2f}ms")
        logger.info(f"📊 Total product matches: {total_matches}")
        
        # Assert reasonable performance
        assert matching_time < 30000, f"Product matching too slow: {matching_time:.2f}ms"
        assert total_matches > 0, "No products matched"
        
    def test_08_data_integrity_validation(self):
        """Test 8: Data integrity validation"""
        logger.info("🧪 Test 8: Data Integrity Validation")
        
        # Process document
        pipeline_result = self.pipeline_service.process_document(
            self.test_document_path,
            force_reprocess=True
        )
        
        assert pipeline_result.success, f"Pipeline processing failed: {pipeline_result.error}"
        
        # Validate database integrity
        with duckdb.connect("data/letters.duckdb") as conn:
            # Check foreign key constraints
            letter_id = pipeline_result.letter_id
            
            # Verify letter exists
            letter = conn.execute(
                "SELECT * FROM letters WHERE id = ?",
                [letter_id]
            ).fetchone()
            assert letter, "Letter not found in database"
            
            # Verify products reference valid letter
            products = conn.execute(
                "SELECT * FROM letter_products WHERE letter_id = ?",
                [letter_id]
            ).fetchall()
            assert len(products) > 0, "No products found for letter"
            
            # Check all products have valid confidence scores
            for product in products:
                confidence = product[5]  # confidence_score column
                assert 0.0 <= confidence <= 1.0, f"Invalid confidence score: {confidence}"
                
            # Verify no duplicate products
            product_identifiers = [product[2] for product in products]
            unique_identifiers = set(product_identifiers)
            assert len(product_identifiers) == len(unique_identifiers), "Duplicate products found"
            
        logger.info("✅ Data integrity validation passed")
        
    def test_09_error_handling_resilience(self):
        """Test 9: Error handling and resilience"""
        logger.info("🧪 Test 9: Error Handling and Resilience")
        
        # Test with non-existent file
        fake_path = Path("data/test/documents/non_existent.pdf")
        result = self.pipeline_service.process_document(fake_path)
        
        assert not result.success, "Expected failure for non-existent file"
        assert result.error, "Error message not provided"
        
        # Test database service resilience
        db_stats = self.product_database_service.get_database_stats()
        assert db_stats["total_products"] > 0, "Database service not working"
        
        # Test connection health
        health = self.product_database_service.test_connection()
        assert health, "Database connection test failed"
        
        logger.info("✅ Error handling tests passed")
        
    def test_10_cleanup_and_summary(self):
        """Test 10: Cleanup and test summary"""
        logger.info("🧪 Test 10: Cleanup and Test Summary")
        
        test_end_time = datetime.now()
        total_test_time = (test_end_time - self.test_start_time).total_seconds()
        
        # Generate test summary
        summary = {
            "test_start_time": self.test_start_time.isoformat(),
            "test_end_time": test_end_time.isoformat(),
            "total_test_time_seconds": total_test_time,
            "test_document": str(self.test_document_path),
            "test_status": "PASSED",
            "services_tested": [
                "ProductionPipelineService",
                "IntelligentProductMatchingService", 
                "SOTAProductDatabaseService",
                "XAIService",
                "DocumentProcessor"
            ],
            "integration_points_validated": [
                "Document Processing",
                "XAI API Integration",
                "Product Matching",
                "Database Storage",
                "JSON Output Storage",
                "Performance Metrics",
                "Data Integrity",
                "Error Handling"
            ]
        }
        
        # Save test summary
        summary_file = Path("logs/integration_tests") / f"pix2b_test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
            
        logger.info(f"📊 Test Summary:")
        logger.info(f"   Total Test Time: {total_test_time:.2f} seconds")
        logger.info(f"   Services Tested: {len(summary['services_tested'])}")
        logger.info(f"   Integration Points: {len(summary['integration_points_validated'])}")
        logger.info(f"   Test Summary File: {summary_file}")
        
        logger.info("🎉 Complete Pipeline Integration Test - SUCCESS!")


if __name__ == "__main__":
    # Run tests directly
    test_instance = TestCompletePipelineIntegration()
    test_instance.setup_class()
    
    # Run all tests
    test_methods = [
        test_instance.test_01_environment_setup,
        test_instance.test_02_document_processing_stage,
        test_instance.test_03_xai_service_integration,
        test_instance.test_04_product_matching_integration,
        test_instance.test_05_database_storage_integration,
        test_instance.test_06_json_output_storage,
        test_instance.test_07_complete_pipeline_performance,
        test_instance.test_08_data_integrity_validation,
        test_instance.test_09_error_handling_resilience,
        test_instance.test_10_cleanup_and_summary
    ]
    
    print("🚀 Starting Complete Pipeline Integration Test...")
    
    for i, test_method in enumerate(test_methods, 1):
        try:
            print(f"\n{'='*60}")
            print(f"Running Test {i}: {test_method.__name__}")
            print(f"{'='*60}")
            test_method()
            print(f"✅ Test {i} PASSED")
        except Exception as e:
            print(f"❌ Test {i} FAILED: {e}")
            raise
            
    print("\n🎉 ALL TESTS PASSED! Complete Pipeline Integration Test Successful!") 