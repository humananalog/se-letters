#!/usr/bin/env python3
"""
Test script for Enhanced SOTA Grok Service with Unified Schema
Demonstrates the improved metadata extraction and DuckDB integration
"""

import sys
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from se_letters.services.sota_grok_service import EnhancedSOTAGrokService


def test_enhanced_service():
    """Test the enhanced SOTA Grok service with unified schema"""
    logger.info("🧪 Testing Enhanced SOTA Grok Service with Unified Schema")
    
    # Initialize service
    service = EnhancedSOTAGrokService()
    
    # Test document content
    test_content = """
    PIX2B Circuit Breaker End of Life Notice
    Document Number: SE-2024-PIX2B-EOL-001
    Language: English
    
    This notice announces the end of life for PIX2B medium voltage switchgear products.
    
    Affected Products:
    - PIX2B-12kV switchgear panels (Part: PIX2B-12-001)
    - PIX2B-24kV distribution equipment (Part: PIX2B-24-002)
    
    Technical Specifications:
    - Voltage: Up to 24kV
    - Current: 2500A
    - Power: 40kA
    - Frequency: 50Hz
    
    Commercial Information:
    - Last Order Date: 2024-12-31
    - End of Service: 2029-12-31
    - Obsolescence Status: End of Commercialization
    
    Replacement Information:
    - PIX3B series with enhanced features
    - Migration path: Direct replacement with PIX3B
    
    Business Impact:
    - Affected Countries: France, Germany, UK
    - Customer Segments: Industrial, Commercial
    - Affected Ranges: PIX2B, PIX2B-MV
    
    Contact Information:
    - Support: support@schneider-electric.com
    - Migration guidance: Contact technical support for migration planning
    
    Spare parts availability: 10 years after end of service
    """
    
    try:
        # Extract unified metadata
        result = service.extract_unified_metadata(
            test_content, 
            "PIX2B_Test_Enhanced.pdf",
            "data/test/documents/PIX2B_Test_Enhanced.pdf"
        )
        
        print("=" * 80)
        print("🎯 ENHANCED SOTA GROK SERVICE TEST RESULTS")
        print("=" * 80)
        
        # Document Information
        print("📄 Document Information:")
        print(f"  Type: {result.document_information.document_type}")
        print(f"  Language: {result.document_information.language}")
        print(f"  Document Number: {result.document_information.document_number}")
        print(f"  Total Products: {result.document_information.total_products}")
        print(f"  Has Tables: {result.document_information.has_tables}")
        print(f"  Has Technical Specs: "
              f"{result.document_information.has_technical_specs}")
        print(f"  Complexity: {result.document_information.extraction_complexity}")
        
        # Product Information
        print(f"\n🔧 Product Information ({len(result.product_information)} products):")
        for i, product in enumerate(result.product_information, 1):
            print(f"  Product {i}:")
            print(f"    Identifier: {product.product_identifier}")
            print(f"    Range: {product.range_label}")
            print(f"    Subrange: {product.subrange_label}")
            print(f"    Product Line: {product.product_line}")
            print(f"    Description: {product.product_description}")
            
            # Technical Specifications
            tech = product.technical_specifications
            print(f"    Technical Specs:")
            print(f"      Voltage: {tech.voltage_level}")
            print(f"      Current: {tech.current_rating}")
            print(f"      Power: {tech.power_rating}")
            print(f"      Frequency: {tech.frequency}")
            
            # Commercial Information
            comm = product.commercial_information
            print(f"    Commercial Info:")
            print(f"      Part Number: {comm.part_number}")
            print(f"      Status: {comm.obsolescence_status}")
            print(f"      Last Order: {comm.last_order_date}")
            print(f"      End of Service: {comm.end_of_service_date}")
            
            # Replacement Information
            repl = product.replacement_information
            print(f"    Replacement Info:")
            print(f"      Suggestions: {repl.replacement_suggestions}")
            print(f"      Migration Path: {repl.migration_path}")
        
        # Business Information
        print(f"\n🏢 Business Information:")
        print(f"  Affected Ranges: {result.business_information.affected_ranges}")
        print(f"  Affected Countries: {result.business_information.affected_countries}")
        print(f"  Customer Segments: {result.business_information.customer_segments}")
        print(f"  Business Impact: {result.business_information.business_impact}")
        
        # Lifecycle Information
        print(f"\n📅 Lifecycle Information:")
        print(f"  Announcement Date: {result.lifecycle_information.announcement_date}")
        print(f"  Effective Date: {result.lifecycle_information.effective_date}")
        key_dates = result.lifecycle_information.key_dates
        print(f"  Key Dates:")
        print(f"    Last Order: {key_dates.last_order_date}")
        print(f"    End of Service: {key_dates.end_of_service_date}")
        print(f"    Spare Parts: {key_dates.spare_parts_availability_duration}")
        
        # Contact Information
        print(f"\n📞 Contact Information:")
        print(f"  Contact Details: {result.contact_information.contact_details}")
        print(f"  Migration Guidance: {result.contact_information.migration_guidance}")
        
        # Extraction Metrics
        print(f"\n📊 Extraction Metrics:")
        print(f"  Confidence: {result.extraction_confidence:.2f}")
        print(f"  Timestamp: {result.processing_timestamp}")
        
        # Test staging table retrieval
        print(f"\n🗄️ Staging Table Records:")
        records = service.get_staging_records(limit=5)
        for record in records:
            print(f"  Record ID: {record['id']}")
            print(f"  Document: {record['document_name']}")
            print(f"  Confidence: {record['confidence_score']:.2f}")
            print(f"  Products: {record['product_count']}")
            print(f"  Created: {record['created_at']}")
            print()
        
        # Performance metrics
        print(f"\n📈 Service Performance Metrics:")
        metrics = service.get_performance_metrics()
        print(f"  Service: {metrics['service_type']}")
        print(f"  Version: {metrics['version']}")
        print(f"  Schema Version: {metrics['schema_version']}")
        print(f"  Features: {metrics['features']}")
        print(f"  Supported Product Lines: {metrics['supported_product_lines']}")
        
        db_stats = metrics.get('database_stats', {})
        print(f"  Database Stats:")
        print(f"    Total Documents: {db_stats.get('total_documents', 0)}")
        print(f"    Avg Confidence: {db_stats.get('avg_confidence', 0.0):.2f}")
        print(f"    Avg Products/Doc: {db_stats.get('avg_products_per_doc', 0.0):.1f}")
        print(f"    Unique Documents: {db_stats.get('unique_documents', 0)}")
        
        print("\n✅ Enhanced SOTA Grok Service test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        print(f"❌ Test failed: {e}")
        
    finally:
        service.close()


def test_batch_processing():
    """Test batch processing with multiple documents"""
    logger.info("🔄 Testing batch processing")
    
    service = EnhancedSOTAGrokService()
    
    # Test documents
    test_documents = [
        {
            'name': 'TeSys_D_EOL.pdf',
            'file_path': 'data/test/TeSys_D_EOL.pdf',
            'content': """
            TeSys D Contactor End of Life Notice
            
            The TeSys D contactor range is being discontinued.
            Affected products:
            - LC1D09 (9A contactor, 690V AC)
            - LC1D12 (12A contactor, 690V AC)
            
            Last order date: 2024-06-30
            Replacement: TeSys F series
            """
        },
        {
            'name': 'SEPAM_2040_Notice.pdf',
            'file_path': 'data/test/SEPAM_2040_Notice.pdf',
            'content': """
            SEPAM 2040 Protection Relay Withdrawal Notice
            
            SEPAM 2040 digital protection relay is being withdrawn.
            Technical specs:
            - Voltage: Up to 15kV
            - Protection functions: Overcurrent, earth fault
            
            End of service: 2025-12-31
            Replacement: SEPAM 2000 series
            """
        }
    ]
    
    try:
        results = service.batch_extract(test_documents)
        
        print(f"\n🔄 Batch Processing Results:")
        print(f"  Processed: {len(results)} documents")
        
        for i, result in enumerate(results, 1):
            doc_name = test_documents[i-1]['name']
            print(f"  Document {i} ({doc_name}):")
            print(f"    Products: {len(result.product_information)}")
            print(f"    Confidence: {result.extraction_confidence:.2f}")
            
            if result.product_information:
                product = result.product_information[0]
                print(f"    First Product: {product.product_identifier} ({product.product_line})")
        
        print("✅ Batch processing test completed!")
        
    except Exception as e:
        logger.error(f"❌ Batch processing test failed: {e}")
        print(f"❌ Batch processing test failed: {e}")
        
    finally:
        service.close()


if __name__ == "__main__":
    print("🚀 Enhanced SOTA Grok Service Test Suite")
    print("=" * 80)
    
    # Test single document extraction
    test_enhanced_service()
    
    print("\n" + "=" * 80)
    
    # Test batch processing
    test_batch_processing()
    
    print("\n🎉 All tests completed!") 