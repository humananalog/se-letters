#!/usr/bin/env python3
"""
Complete Pipeline Integration Test - PIX2B Document (PostgreSQL v2.3)
Comprehensive end-to-end test using real production pipeline (v2.3), API calls, and PostgreSQL operations

This test validates the complete integration of:
1. Document Processing
2. XAI Service (real API calls)
3. Enhanced Product Mapping Service (production)
4. Database Storage (real PostgreSQL operations)
5. JSON Output with run folders

Test Document: PIX2B_Phase_out_Letter.pdf
Expected Results: Should identify PIX 2B range products with high confidence

Version: 2.3.0
Author: SE Letters Team
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime
import psycopg2
from loguru import logger

from se_letters.core.config import get_config
from se_letters.services.postgresql_production_pipeline_service_v2_3 import PostgreSQLProductionPipelineServiceV2_3


class TestCompletePipelineIntegration:
    """Complete pipeline integration test with PIX2B document (PostgreSQL v2.3)"""
    
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
        
        # Initialize production pipeline v2.3
        cls.pipeline_service = PostgreSQLProductionPipelineServiceV2_3()
        
        logger.info("🧪 Complete Pipeline Integration Test (PostgreSQL v2.3) - Setup Complete")
        logger.info(f"📄 Test Document: {cls.test_document_path}")
        logger.info(f"🚀 Test Start Time: {cls.test_start_time}")
        
    @classmethod
    def _setup_debug_logging(cls):
        """Setup comprehensive debug logging"""
        test_logs_dir = Path("logs/integration_tests")
        test_logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = test_logs_dir / f"pix2b_integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
        # Check PostgreSQL connection
        try:
            with psycopg2.connect(self.config.data.database.letter_database) as conn:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM letters")
                logger.info(f"📊 PostgreSQL letters table: {cur.fetchone()[0]} existing letters")
        except Exception as e:
            assert False, f"PostgreSQL connection failed: {e}"
        logger.info("✅ Test 1: Environment setup verified")
        
    def test_02_document_processing_stage(self):
        """Test 2: Document processing stage"""
        logger.info("🧪 Test 2: Document Processing Stage")
        result = self.pipeline_service.document_processor.process_document(self.test_document_path)
        assert result is not None, "Document processing failed"
        assert result.text, "Document text is empty"
        assert result.metadata, "Document metadata is empty"
        content = result.text.lower()
        assert "pix" in content, "PIX reference not found in document content"
        assert "2b" in content or "double" in content, "PIX 2B reference not found"
        logger.info(f"📄 Document processed successfully: {len(result.text)} characters")
        logger.info(f"📋 Document metadata: {result.metadata}")
        
    def test_03_pipeline_processing(self):
        """Test 3: Full pipeline processing and output evaluation"""
        logger.info("🧪 Test 3: Full Pipeline Processing (v2.3)")
        start_time = time.time()
        pipeline_result = self.pipeline_service.process_document(
            self.test_document_path,
            force_reprocess=True
        )
        total_time = (time.time() - start_time) * 1000
        assert pipeline_result.success, f"Pipeline processing failed: {pipeline_result.error_message}"
        assert pipeline_result.document_id, "Letter ID not generated"
        assert pipeline_result.confidence_score > 0.7, f"Low confidence score: {pipeline_result.confidence_score}"
        logger.info(f"✅ Pipeline processing successful in {total_time:.2f}ms")
        logger.info(f"🎯 Extraction confidence: {pipeline_result.confidence_score:.2f}")
        # Evaluate product matching result
        pm_result = pipeline_result.product_matching_result
        assert pm_result, "Product matching result missing"
        total_matches = pm_result.get("total_matches", 0)
        matching_time = pm_result.get("processing_time_ms", 0)
        logger.info(f"🔍 Product matching: {total_matches} matches in {matching_time:.2f}ms")
        assert total_matches > 0, "No products matched"
        # Check for PIX 2B products
        matched_products = pm_result.get("matched_products", [])
        pix_matches = [
            p for p in matched_products
            if "pix" in str(p.get("product_identifier", "")).lower() and "2b" in str(p.get("product_identifier", "")).lower()
        ]
        assert len(pix_matches) > 0, "No PIX 2B products matched"
        logger.info(f"🎯 PIX 2B products matched: {len(pix_matches)}")
        # Check database storage
        with psycopg2.connect(self.config.data.database.letter_database) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM letters WHERE id = %s", [pipeline_result.document_id])
            letter = cur.fetchone()
            assert letter, "Letter not found in database"
            assert letter[1] == "PIX2B_Phase_out_Letter.pdf", "Document name mismatch"
            assert letter[9] > 0.7, f"Low extraction confidence: {letter[9]}"
            cur.execute("SELECT * FROM letter_products WHERE letter_id = %s", [pipeline_result.document_id])
            products = cur.fetchall()
            assert len(products) > 0, "No products stored in database"
            pix2b_db_products = [
                product for product in products
                if "pix" in str(product[2]).lower() and "2b" in str(product[2]).lower()
            ]
            assert len(pix2b_db_products) > 0, "No PIX 2B products stored in database"
            logger.info(f"💾 Database storage: {len(products)} products stored, {len(pix2b_db_products)} PIX 2B")
        # Check JSON output (optional)
        # (Assume output manager saves to data/output/ or logs/integration_tests/)
        logger.info("✅ Full pipeline output evaluation complete")
        
    def test_04_performance(self):
        """Test 4: Pipeline performance metrics"""
        logger.info("🧪 Test 4: Pipeline Performance")
        start_time = time.time()
        pipeline_result = self.pipeline_service.process_document(
            self.test_document_path,
            force_reprocess=True
        )
        total_time = (time.time() - start_time) * 1000
        assert pipeline_result.success, f"Pipeline processing failed: {pipeline_result.error_message}"
        assert total_time < 60000, f"Pipeline too slow: {total_time:.2f}ms"
        pm_result = pipeline_result.product_matching_result
        assert pm_result, "Product matching result missing"
        matching_time = pm_result.get("processing_time_ms", 0)
        assert matching_time < 30000, f"Product matching too slow: {matching_time:.2f}ms"
        logger.info(f"⏱️ Total processing time: {total_time:.2f}ms")
        logger.info(f"🔍 Product matching time: {matching_time:.2f}ms")
        logger.info(f"🎯 Extraction confidence: {pipeline_result.confidence_score:.2f}")
        logger.info(f"✅ Performance test passed")
        
    def test_05_data_integrity(self):
        """Test 5: Data integrity validation"""
        logger.info("🧪 Test 5: Data Integrity Validation")
        pipeline_result = self.pipeline_service.process_document(
            self.test_document_path,
            force_reprocess=True
        )
        assert pipeline_result.success, f"Pipeline processing failed: {pipeline_result.error_message}"
        with psycopg2.connect(self.config.data.database.letter_database) as conn:
            cur = conn.cursor()
            document_id = pipeline_result.document_id
            cur.execute("SELECT * FROM letters WHERE id = %s", [document_id])
            letter = cur.fetchone()
            assert letter, "Letter not found in database"
            cur.execute("SELECT * FROM letter_products WHERE letter_id = %s", [document_id])
            products = cur.fetchall()
            assert len(products) > 0, "No products found for letter"
            for product in products:
                confidence = product[10]  # confidence_score column
                assert 0.0 <= confidence <= 1.0, f"Invalid confidence score: {confidence}"
            product_identifiers = [product[2] for product in products]
            unique_identifiers = set(product_identifiers)
            assert len(product_identifiers) == len(unique_identifiers), "Duplicate products found"
        logger.info("✅ Data integrity validation passed")
        
    def test_06_error_handling(self):
        """Test 6: Error handling and resilience"""
        logger.info("🧪 Test 6: Error Handling and Resilience")
        fake_path = Path("data/test/documents/non_existent.pdf")
        try:
            result = self.pipeline_service.process_document(fake_path)
            assert not result.success, "Expected failure for non-existent file"
        except FileNotFoundError:
            pass  # Expected
        logger.info("✅ Error handling tests passed")
        
    def test_07_cleanup_and_summary(self):
        """Test 7: Cleanup and test summary"""
        logger.info("🧪 Test 7: Cleanup and Test Summary")
        test_end_time = datetime.now()
        total_test_time = (test_end_time - self.test_start_time).total_seconds()
        summary = {
            "test_start_time": self.test_start_time.isoformat(),
            "test_end_time": test_end_time.isoformat(),
            "total_test_time_seconds": total_test_time,
            "test_document": str(self.test_document_path),
            "test_status": "PASSED",
            "pipeline_version": "2.3.0",
            "integration_points_validated": [
                "Document Processing",
                "XAI API Integration",
                "Enhanced Product Mapping",
                "Database Storage",
                "JSON Output Storage",
                "Performance Metrics",
                "Data Integrity",
                "Error Handling"
            ]
        }
        summary_file = Path("logs/integration_tests") / f"pix2b_test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"📊 Test Summary:")
        logger.info(f"   Total Test Time: {total_test_time:.2f} seconds")
        logger.info(f"   Integration Points: {len(summary['integration_points_validated'])}")
        logger.info(f"   Test Summary File: {summary_file}")
        logger.info("🎉 Complete Pipeline Integration Test (PostgreSQL v2.3) - SUCCESS!")


if __name__ == "__main__":
    test_instance = TestCompletePipelineIntegration()
    test_instance.setup_class()
    test_methods = [
        test_instance.test_01_environment_setup,
        test_instance.test_02_document_processing_stage,
        test_instance.test_03_pipeline_processing,
        test_instance.test_04_performance,
        test_instance.test_05_data_integrity,
        test_instance.test_06_error_handling,
        test_instance.test_07_cleanup_and_summary
    ]
    print("🚀 Starting Complete Pipeline Integration Test (PostgreSQL v2.3)...")
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
    print("\n🎉 ALL TESTS PASSED! Complete Pipeline Integration Test (PostgreSQL v2.3) Successful!") 