#!/usr/bin/env python3
"""
Production Pipeline Service Tests
Comprehensive unit tests with full logging validation

Version: 2.1.0
Last Updated: 2025-01-27
"""

import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from dataclasses import asdict

from se_letters.services.production_pipeline_service import (
    ProductionPipelineService,
    ProcessingStatus,
    DocumentCheckResult,
    ContentValidationResult,
    ProcessingResult
)


class TestProductionPipelineService:
    """Test suite for ProductionPipelineService"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        import tempfile
        import os
        
        # Create a temporary directory and file path
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.duckdb")
        
        yield db_path
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def sample_document(self):
        """Create sample document for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
            f.write("Sample Schneider Electric TeSys D contactor obsolescence notice")
            doc_path = Path(f.name)
        
        yield doc_path
        
        # Cleanup
        doc_path.unlink(missing_ok=True)
    
    @pytest.fixture
    def pipeline_service(self, temp_db):
        """Create pipeline service instance"""
        with patch('se_letters.services.production_pipeline_service.get_config') as mock_config:
            mock_config.return_value = Mock()
            mock_config.return_value.api.xai.model = "grok-beta"
            
            with patch('se_letters.services.production_pipeline_service.XAIService'):
                with patch('se_letters.services.production_pipeline_service.DocumentProcessor'):
                    service = ProductionPipelineService(db_path=temp_db)
                    return service
    
    def test_initialization(self, pipeline_service):
        """Test service initialization"""
        assert pipeline_service is not None
        assert pipeline_service.db_path.endswith('.duckdb')
        assert hasattr(pipeline_service, 'xai_service')
        assert hasattr(pipeline_service, 'document_processor')
    
    def test_database_initialization(self, temp_db):
        """Test database schema initialization"""
        import duckdb
        
        with patch('se_letters.services.production_pipeline_service.get_config') as mock_config:
            mock_config.return_value = Mock()
            mock_config.return_value.api.xai.model = "grok-beta"
            
            with patch('se_letters.services.production_pipeline_service.XAIService'):
                with patch('se_letters.services.production_pipeline_service.DocumentProcessor'):
                    service = ProductionPipelineService(db_path=temp_db)
        
        # Verify database schema
        with duckdb.connect(temp_db) as conn:
            tables = conn.execute("SHOW TABLES").fetchall()
            table_names = [t[0] for t in tables]
            
            assert 'letters' in table_names
            assert 'letter_products' in table_names
            assert 'processing_debug' in table_names
            
            # Check sequences
            sequences = conn.execute("SELECT sequence_name FROM information_schema.sequences").fetchall()
            sequence_names = [s[0] for s in sequences]
            
            assert 'letters_id_seq' in sequence_names
            assert 'products_id_seq' in sequence_names
            assert 'debug_id_seq' in sequence_names
    
    def test_calculate_file_hash(self, pipeline_service, sample_document):
        """Test file hash calculation"""
        file_hash = pipeline_service._calculate_file_hash(sample_document)
        
        assert file_hash is not None
        assert len(file_hash) == 64  # SHA-256 hash length
        assert isinstance(file_hash, str)
        
        # Test consistency
        file_hash2 = pipeline_service._calculate_file_hash(sample_document)
        assert file_hash == file_hash2
    
    def test_check_document_exists_new_document(self, pipeline_service, sample_document):
        """Test document existence check for new document"""
        result = pipeline_service._check_document_exists(sample_document)
        
        assert isinstance(result, DocumentCheckResult)
        assert result.exists is False
        assert result.document_id is None
        assert result.file_hash is not None
        assert result.content_compliant is False
    
    def test_check_document_exists_existing_document(self, pipeline_service, sample_document):
        """Test document existence check for existing document"""
        import duckdb
        
        # Insert existing document
        file_hash = pipeline_service._calculate_file_hash(sample_document)
        
        with duckdb.connect(pipeline_service.db_path) as conn:
            conn.execute("""
                INSERT INTO letters (
                    document_name, source_file_path, file_hash, status, validation_details_json
                ) VALUES (?, ?, ?, ?, ?)
            """, [
                sample_document.name,
                str(sample_document),
                file_hash,
                'processed',
                json.dumps({"is_compliant": True})
            ])
        
        result = pipeline_service._check_document_exists(sample_document)
        
        assert result.exists is True
        assert result.document_id is not None
        assert result.file_hash == file_hash
        assert result.content_compliant is True
    
    def test_validate_content_compliance_success(self, pipeline_service, sample_document):
        """Test successful content validation"""
        # Mock document processor
        pipeline_service.document_processor.extract_text.return_value = (
            "TeSys D contactor LC1D09 obsolescence notice with technical specifications"
        )
        
        # Mock XAI service response
        mock_response = json.dumps({
            "is_compliant": True,
            "confidence_score": 0.95,
            "product_ranges": ["TeSys D"],
            "technical_specs": {"voltage": "24V", "current": "9A"},
            "validation_errors": [],
            "extracted_metadata": {"document_type": "obsolescence_notice"}
        })
        
        pipeline_service.xai_service.generate_completion.return_value = mock_response
        
        result = pipeline_service._validate_content_compliance(sample_document)
        
        assert isinstance(result, ContentValidationResult)
        assert result.is_compliant is True
        assert result.confidence_score == 0.95
        assert "TeSys D" in result.product_ranges
        assert "voltage" in result.technical_specs
        assert len(result.validation_errors) == 0
    
    def test_validate_content_compliance_failure(self, pipeline_service, sample_document):
        """Test content validation failure"""
        # Mock empty document content
        pipeline_service.document_processor.extract_text.return_value = ""
        
        result = pipeline_service._validate_content_compliance(sample_document)
        
        assert isinstance(result, ContentValidationResult)
        assert result.is_compliant is False
        assert result.confidence_score == 0.0
        assert len(result.product_ranges) == 0
        assert len(result.validation_errors) > 0
    
    def test_process_with_grok_success(self, pipeline_service, sample_document):
        """Test successful Grok processing"""
        # Create validation result
        validation_result = ContentValidationResult(
            is_compliant=True,
            confidence_score=0.95,
            product_ranges=["TeSys D"],
            technical_specs={"voltage": "24V"},
            validation_errors=[],
            extracted_metadata={}
        )
        
        # Mock document processor
        pipeline_service.document_processor.extract_text.return_value = (
            "TeSys D contactor LC1D09 obsolescence notice"
        )
        
        # Mock Grok response
        mock_grok_response = json.dumps({
            "document_information": {
                "document_type": "obsolescence_notice",
                "document_title": "TeSys D End of Life",
                "document_date": "2024-01-01",
                "language": "en"
            },
            "products": [
                {
                    "product_identifier": "LC1D09",
                    "range_label": "TeSys D",
                    "subrange_label": "Contactors",
                    "product_line": "DPIBS",
                    "product_description": "TeSys D contactor 9A",
                    "obsolescence_status": "end_of_life",
                    "end_of_service_date": "2024-12-31",
                    "replacement_suggestions": "TeSys F series"
                }
            ],
            "technical_specifications": {
                "voltage_levels": ["24V", "230V"],
                "current_ratings": ["9A"],
                "power_ratings": ["2.2kW"],
                "frequencies": ["50Hz", "60Hz"]
            },
            "business_information": {
                "customer_impact": "High",
                "migration_timeline": "6 months",
                "support_contacts": "support@schneider-electric.com"
            },
            "extraction_metadata": {
                "confidence_score": 0.95,
                "processing_method": "grok_production",
                "extraction_timestamp": "2024-01-01T00:00:00Z"
            }
        })
        
        pipeline_service.xai_service.generate_completion.return_value = mock_grok_response
        
        result = pipeline_service._process_with_grok(sample_document, validation_result)
        
        assert result is not None
        assert isinstance(result, dict)
        assert "document_information" in result
        assert "products" in result
        assert len(result["products"]) == 1
        assert result["products"][0]["product_identifier"] == "LC1D09"
    
    def test_process_with_grok_failure(self, pipeline_service, sample_document):
        """Test Grok processing failure"""
        validation_result = ContentValidationResult(
            is_compliant=True,
            confidence_score=0.95,
            product_ranges=["TeSys D"],
            technical_specs={},
            validation_errors=[],
            extracted_metadata={}
        )
        
        # Mock empty response
        pipeline_service.xai_service.generate_completion.return_value = ""
        
        result = pipeline_service._process_with_grok(sample_document, validation_result)
        
        assert result is None
    
    def test_ingest_into_database_success(self, pipeline_service, sample_document):
        """Test successful database ingestion"""
        validation_result = ContentValidationResult(
            is_compliant=True,
            confidence_score=0.95,
            product_ranges=["TeSys D"],
            technical_specs={"voltage": "24V"},
            validation_errors=[],
            extracted_metadata={}
        )
        
        grok_data = {
            "document_information": {
                "document_type": "obsolescence_notice",
                "document_title": "TeSys D End of Life"
            },
            "products": [
                {
                    "product_identifier": "LC1D09",
                    "range_label": "TeSys D",
                    "subrange_label": "Contactors",
                    "product_line": "DPIBS",
                    "product_description": "TeSys D contactor 9A",
                    "obsolescence_status": "end_of_life",
                    "end_of_service_date": "2024-12-31",
                    "replacement_suggestions": "TeSys F series"
                }
            ]
        }
        
        result = pipeline_service._ingest_into_database(sample_document, validation_result, grok_data)
        
        assert result["success"] is True
        assert "document_id" in result
        assert result["products_inserted"] == 1
        assert "file_hash" in result
        
        # Verify database content
        import duckdb
        with duckdb.connect(pipeline_service.db_path) as conn:
            letter_count = conn.execute("SELECT COUNT(*) FROM letters").fetchone()[0]
            product_count = conn.execute("SELECT COUNT(*) FROM letter_products").fetchone()[0]
            
            assert letter_count == 1
            assert product_count == 1
    
    def test_complete_pipeline_success(self, pipeline_service, sample_document):
        """Test complete pipeline processing success"""
        # Mock document processor
        pipeline_service.document_processor.extract_text.return_value = (
            "TeSys D contactor LC1D09 obsolescence notice with technical specifications"
        )
        
        # Mock validation response
        validation_response = json.dumps({
            "is_compliant": True,
            "confidence_score": 0.95,
            "product_ranges": ["TeSys D"],
            "technical_specs": {"voltage": "24V"},
            "validation_errors": [],
            "extracted_metadata": {}
        })
        
        # Mock Grok response
        grok_response = json.dumps({
            "document_information": {
                "document_type": "obsolescence_notice",
                "document_title": "TeSys D End of Life"
            },
            "products": [
                {
                    "product_identifier": "LC1D09",
                    "range_label": "TeSys D",
                    "subrange_label": "Contactors",
                    "product_line": "DPIBS",
                    "product_description": "TeSys D contactor 9A",
                    "obsolescence_status": "end_of_life",
                    "end_of_service_date": "2024-12-31",
                    "replacement_suggestions": "TeSys F series"
                }
            ]
        })
        
        # Configure mock responses
        pipeline_service.xai_service.generate_completion.side_effect = [
            validation_response,  # First call for validation
            grok_response         # Second call for Grok processing
        ]
        
        result = pipeline_service.process_document(sample_document)
        
        assert isinstance(result, ProcessingResult)
        assert result.success is True
        assert result.status == ProcessingStatus.COMPLETED
        assert result.document_id is not None
        assert result.processing_time_ms > 0
        assert result.confidence_score == 0.95
        assert result.validation_result is not None
        assert result.grok_metadata is not None
        assert result.ingestion_details is not None
    
    def test_complete_pipeline_duplicate_document(self, pipeline_service, sample_document):
        """Test pipeline with duplicate document"""
        import duckdb
        
        # Insert existing compliant document
        file_hash = pipeline_service._calculate_file_hash(sample_document)
        
        with duckdb.connect(pipeline_service.db_path) as conn:
            conn.execute("""
                INSERT INTO letters (
                    document_name, source_file_path, file_hash, status, validation_details_json
                ) VALUES (?, ?, ?, ?, ?)
            """, [
                sample_document.name,
                str(sample_document),
                file_hash,
                'processed',
                json.dumps({"is_compliant": True})
            ])
        
        result = pipeline_service.process_document(sample_document)
        
        assert isinstance(result, ProcessingResult)
        assert result.success is True
        assert result.status == ProcessingStatus.SKIPPED
        assert result.document_id is not None
    
    def test_complete_pipeline_validation_failure(self, pipeline_service, sample_document):
        """Test pipeline with validation failure"""
        # Mock empty document content
        pipeline_service.document_processor.extract_text.return_value = ""
        
        result = pipeline_service.process_document(sample_document)
        
        assert isinstance(result, ProcessingResult)
        assert result.success is False
        assert result.status == ProcessingStatus.FAILED
        assert "Content validation failed" in result.error_message
        assert result.validation_result is not None
        assert result.validation_result.is_compliant is False
    
    def test_complete_pipeline_grok_failure(self, pipeline_service, sample_document):
        """Test pipeline with Grok processing failure"""
        # Mock document processor
        pipeline_service.document_processor.extract_text.return_value = (
            "TeSys D contactor LC1D09 obsolescence notice"
        )
        
        # Mock validation success
        validation_response = json.dumps({
            "is_compliant": True,
            "confidence_score": 0.95,
            "product_ranges": ["TeSys D"],
            "technical_specs": {"voltage": "24V"},
            "validation_errors": [],
            "extracted_metadata": {}
        })
        
        # Configure mock responses (validation success, Grok failure)
        pipeline_service.xai_service.generate_completion.side_effect = [
            validation_response,  # First call for validation
            ""                    # Second call for Grok processing (empty response)
        ]
        
        result = pipeline_service.process_document(sample_document)
        
        assert isinstance(result, ProcessingResult)
        assert result.success is False
        assert result.status == ProcessingStatus.FAILED
        assert "Grok processing failed" in result.error_message
        assert result.validation_result is not None
        assert result.grok_metadata is None
    
    def test_get_processing_statistics(self, pipeline_service, sample_document):
        """Test processing statistics retrieval"""
        # Insert test data
        import duckdb
        
        with duckdb.connect(pipeline_service.db_path) as conn:
            # Insert letter
            conn.execute("""
                INSERT INTO letters (
                    document_name, source_file_path, file_hash, status, 
                    extraction_confidence, processing_time_ms
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, [
                sample_document.name,
                str(sample_document),
                "test_hash",
                'processed',
                0.95,
                1500.0
            ])
            
            letter_id = conn.execute("SELECT currval('letters_id_seq')").fetchone()[0]
            
            # Insert products
            conn.execute("""
                INSERT INTO letter_products (letter_id, range_label) VALUES (?, ?)
            """, [letter_id, "TeSys D"])
            
            conn.execute("""
                INSERT INTO letter_products (letter_id, range_label) VALUES (?, ?)
            """, [letter_id, "TeSys F"])
        
        stats = pipeline_service.get_processing_statistics()
        
        assert isinstance(stats, dict)
        assert stats["total_documents"] == 1
        assert stats["processed_count"] == 1
        assert stats["failed_count"] == 0
        assert stats["avg_confidence"] == 0.95
        assert stats["avg_processing_time"] == 1500.0
        assert stats["total_products"] == 2
        assert stats["unique_ranges"] == 2
    
    def test_logging_integration(self, pipeline_service, sample_document, caplog):
        """Test logging integration throughout pipeline"""
        import logging
        
        # Set log level to capture all messages
        caplog.set_level(logging.INFO)
        
        # Mock document processor
        pipeline_service.document_processor.extract_text.return_value = (
            "TeSys D contactor LC1D09 obsolescence notice"
        )
        
        # Mock validation response
        validation_response = json.dumps({
            "is_compliant": True,
            "confidence_score": 0.95,
            "product_ranges": ["TeSys D"],
            "technical_specs": {"voltage": "24V"},
            "validation_errors": [],
            "extracted_metadata": {}
        })
        
        # Mock Grok response
        grok_response = json.dumps({
            "document_information": {"document_type": "obsolescence_notice"},
            "products": [{"product_identifier": "LC1D09", "range_label": "TeSys D"}]
        })
        
        # Configure mock responses
        pipeline_service.xai_service.generate_completion.side_effect = [
            validation_response,
            grok_response
        ]
        
        result = pipeline_service.process_document(sample_document)
        
        # Verify logging messages
        log_messages = [record.message for record in caplog.records]
        
        assert any("Starting production pipeline" in msg for msg in log_messages)
        assert any("Step 1: Checking document existence" in msg for msg in log_messages)
        assert any("Step 2: Validating content compliance" in msg for msg in log_messages)
        assert any("Step 3: Processing with Grok" in msg for msg in log_messages)
        assert any("Step 4: Ingesting into database" in msg for msg in log_messages)
        assert any("Production pipeline completed successfully" in msg for msg in log_messages)
        
        assert result.success is True


class TestProductionPipelineIntegration:
    """Integration tests for production pipeline"""
    
    @pytest.fixture
    def integration_service(self):
        """Create service for integration testing"""
        import tempfile
        import os
        import shutil
        
        # Create a temporary directory and file path
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "integration_test.duckdb")
        
        with patch('se_letters.services.production_pipeline_service.get_config') as mock_config:
            mock_config.return_value = Mock()
            mock_config.return_value.api.xai.model = "grok-beta"
            
            with patch('se_letters.services.production_pipeline_service.XAIService') as mock_xai:
                with patch('se_letters.services.production_pipeline_service.DocumentProcessor') as mock_doc:
                    service = ProductionPipelineService(db_path=db_path)
                    
                    # Setup realistic mocks
                    mock_xai.return_value.generate_completion.return_value = json.dumps({
                        "is_compliant": True,
                        "confidence_score": 0.95,
                        "product_ranges": ["TeSys D"],
                        "technical_specs": {"voltage": "24V"},
                        "validation_errors": [],
                        "extracted_metadata": {}
                    })
                    
                    mock_doc.return_value.extract_text.return_value = (
                        "TeSys D contactor LC1D09 obsolescence notice"
                    )
                    
                    yield service
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_end_to_end_processing(self, integration_service):
        """Test complete end-to-end processing"""
        # Create test document
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
            f.write("TeSys D contactor LC1D09 obsolescence notice")
            doc_path = Path(f.name)
        
        try:
            # Configure XAI service responses
            integration_service.xai_service.generate_completion.side_effect = [
                # Validation response
                json.dumps({
                    "is_compliant": True,
                    "confidence_score": 0.95,
                    "product_ranges": ["TeSys D"],
                    "technical_specs": {"voltage": "24V"},
                    "validation_errors": [],
                    "extracted_metadata": {}
                }),
                # Grok response
                json.dumps({
                    "document_information": {
                        "document_type": "obsolescence_notice",
                        "document_title": "TeSys D End of Life"
                    },
                    "products": [
                        {
                            "product_identifier": "LC1D09",
                            "range_label": "TeSys D",
                            "subrange_label": "Contactors",
                            "product_line": "DPIBS",
                            "product_description": "TeSys D contactor 9A",
                            "obsolescence_status": "end_of_life",
                            "end_of_service_date": "2024-12-31",
                            "replacement_suggestions": "TeSys F series"
                        }
                    ]
                })
            ]
            
            # Process document
            result = integration_service.process_document(doc_path)
            
            # Verify results
            assert result.success is True
            assert result.status == ProcessingStatus.COMPLETED
            assert result.document_id is not None
            assert result.confidence_score == 0.95
            
            # Verify database state
            import duckdb
            with duckdb.connect(integration_service.db_path) as conn:
                letter_count = conn.execute("SELECT COUNT(*) FROM letters").fetchone()[0]
                product_count = conn.execute("SELECT COUNT(*) FROM letter_products").fetchone()[0]
                
                assert letter_count == 1
                assert product_count == 1
                
                # Verify letter data
                letter_data = conn.execute("""
                    SELECT document_name, status, extraction_confidence, raw_grok_json
                    FROM letters WHERE id = ?
                """, [result.document_id]).fetchone()
                
                assert letter_data[0] == doc_path.name
                assert letter_data[1] == 'processed'
                assert letter_data[2] == 0.95
                assert letter_data[3] is not None
                
                # Verify product data
                product_data = conn.execute("""
                    SELECT product_identifier, range_label, product_line
                    FROM letter_products WHERE letter_id = ?
                """, [result.document_id]).fetchone()
                
                assert product_data[0] == "LC1D09"
                assert product_data[1] == "TeSys D"
                assert product_data[2] == "DPIBS"
            
            # Test duplicate processing
            result2 = integration_service.process_document(doc_path)
            assert result2.success is True
            assert result2.status == ProcessingStatus.SKIPPED
            
            # Verify no duplicate in database
            with duckdb.connect(integration_service.db_path) as conn:
                letter_count = conn.execute("SELECT COUNT(*) FROM letters").fetchone()[0]
                assert letter_count == 1  # Still only one record
            
        finally:
            # Cleanup
            doc_path.unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 