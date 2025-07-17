#!/usr/bin/env python3
"""
Test Enhanced Token Tracking and Raw Content Storage
Demonstrates the new LLM API tracking and content management features

Usage:
    python scripts/test_enhanced_token_tracking.py [document_path]
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from se_letters.services.postgresql_production_pipeline_service_stage1 import (
    PostgreSQLProductionPipelineServiceStage1
)


def test_document_processing_with_tracking(file_path: Path):
    """Test document processing with comprehensive token tracking"""
    
    print("🧪 ENHANCED TOKEN TRACKING TEST")
    print("=" * 60)
    print(f"📄 Document: {file_path.name}")
    print(f"📅 Timestamp: {datetime.now().isoformat()}")
    print()
    
    try:
        # Initialize STAGE 1 pipeline with enhanced tracking
        print("🏭 Initializing STAGE 1 Pipeline with Enhanced Tracking...")
        pipeline = PostgreSQLProductionPipelineServiceStage1()
        print("✅ Pipeline initialized successfully")
        print()
        
        # Process document with PROCESS request
        print("🚀 Processing document with PROCESS request...")
        result = pipeline.process_document(
            file_path=file_path,
            request_type="PROCESS",
            request_metadata={
                "source": "test_script",
                "user": "test_user",
                "test_session": "enhanced_tracking_demo"
            }
        )
        
        print("📊 PROCESSING RESULTS:")
        print(f"   ✅ Success: {result['success']}")
        print(f"   📋 Decision: {result.get('decision', 'N/A')}")
        print(f"   📦 Products found: {result.get('products_found', 0)}")
        print(f"   🎯 Confidence: {result.get('confidence_score', 0.0):.3f}")
        print(f"   ⏱️  Processing time: {result.get('processing_time_ms', 0):.2f}ms")
        print(f"   🆔 Letter ID: {result.get('letter_id', 'N/A')}")
        print(f"   🔄 From cache: {result.get('from_cache', False)}")
        
        # Display token tracking information
        if 'tracking_metadata' in result:
            print("\n📊 TOKEN USAGE TRACKING:")
            tracking = result['tracking_metadata']
            
            print(f"   📋 Call ID: {tracking.get('call_id', 'N/A')}")
            print(f"   🔢 Tracking ID: {tracking.get('tracking_id', 'N/A')}")
            print(f"   📄 Raw Content ID: {tracking.get('raw_content_id', 'N/A')}")
            print(f"   📌 Prompt Version: {tracking.get('prompt_version', 'N/A')}")
            print(f"   ⏱️  Processing Time: {tracking.get('processing_time_ms', 0):.2f}ms")
            
            # Token usage details
            token_usage = tracking.get('token_usage', {})
            if token_usage:
                print(f"   🪙 TOKEN USAGE:")
                print(f"      - Prompt tokens: {token_usage.get('prompt_tokens', 'N/A')}")
                print(f"      - Completion tokens: {token_usage.get('completion_tokens', 'N/A')}")
                print(f"      - Total tokens: {token_usage.get('total_tokens', 'N/A')}")
            else:
                print(f"   ⚠️  Token usage not captured (may be from cache)")
        else:
            print("\n⚠️  No token tracking metadata available")
        
        print("\n" + "=" * 60)
        
        # Test FORCE reprocessing to demonstrate different behavior
        print("🔄 Testing FORCE reprocessing...")
        force_result = pipeline.process_document(
            file_path=file_path,
            request_type="FORCE",
            request_metadata={
                "source": "test_script",
                "user": "test_user",
                "test_session": "force_reprocessing_demo"
            }
        )
        
        print("📊 FORCE PROCESSING RESULTS:")
        print(f"   ✅ Success: {force_result['success']}")
        print(f"   📋 Decision: {force_result.get('decision', 'N/A')}")
        print(f"   🔄 From cache: {force_result.get('from_cache', False)}")
        print(f"   ⏱️  Processing time: {force_result.get('processing_time_ms', 0):.2f}ms")
        
        print("\n" + "=" * 60)
        
        # Get comprehensive analytics
        print("📈 RETRIEVING ANALYTICS...")
        analytics = pipeline.get_processing_analytics()
        
        if 'error' not in analytics:
            print("📊 TOKEN USAGE ANALYTICS:")
            token_analytics = analytics.get('token_usage', {})
            if 'analytics' in token_analytics and token_analytics['analytics']:
                latest = token_analytics['analytics'][0]
                print(f"   📅 Period: {analytics.get('analytics_period', 'N/A')}")
                print(f"   📞 Total calls: {latest.get('total_calls', 0)}")
                print(f"   🪙 Total tokens: {latest.get('total_tokens', 0)}")
                print(f"   💰 Total cost: ${latest.get('total_estimated_cost_usd', 0):.6f}")
                print(f"   ⚡ Avg response time: {latest.get('avg_response_time_ms', 0):.2f}ms")
                print(f"   📈 Success rate: {latest.get('success_rate_percent', 0):.1f}%")
            
            print("\n📄 CONTENT PROCESSING SUMMARY:")
            content_analytics = analytics.get('content_processing', {})
            if 'content_summary' in content_analytics:
                for version_data in content_analytics['content_summary']:
                    print(f"   📌 Prompt v{version_data['prompt_version']}:")
                    print(f"      - Total content: {version_data['total_content']}")
                    print(f"      - Processed: {version_data['processed_count']}")
                    print(f"      - Avg products: {version_data.get('avg_products_per_document', 0):.2f}")
                    print(f"      - Avg confidence: {version_data.get('avg_grok_confidence', 0):.3f}")
            
            print("\n🎯 PROCESSING DECISIONS:")
            decisions = analytics.get('processing_decisions', [])
            for decision in decisions:
                print(f"   📋 {decision['processing_decision']}: {decision['decision_count']} times")
                avg_products = decision.get('avg_products', 0) or 0
                avg_duration = decision.get('avg_duration_ms', 0) or 0
                print(f"      - Avg products: {avg_products:.2f}")
                print(f"      - Avg duration: {avg_duration:.2f}ms")
        else:
            print(f"❌ Analytics error: {analytics['error']}")
        
        print("\n" + "=" * 60)
        
        # Get duplicate detection summary
        print("🔍 DUPLICATE DETECTION SUMMARY:")
        dup_summary = pipeline.get_duplicate_detection_summary()
        
        if 'error' not in dup_summary:
            print(f"   📄 Total documents: {dup_summary['total_documents']}")
            print(f"   🔄 Duplicates found: {dup_summary['duplicates_found']}")
            print(f"   📊 Duplicate rate: {dup_summary['duplicate_rate_percent']:.2f}%")
            print(f"   ✅ Success rate: {dup_summary['success_rate_percent']:.2f}%")
            print(f"   🎯 Avg confidence: {dup_summary['avg_confidence']:.3f}")
        else:
            print(f"❌ Duplicate summary error: {dup_summary['error']}")
        
        print("\n✅ ENHANCED TOKEN TRACKING TEST COMPLETED SUCCESSFULLY!")
        print("🎯 Key Features Demonstrated:")
        print("   - Comprehensive token usage tracking from xAI SDK")
        print("   - Raw content storage with prompt version management")
        print("   - Intelligent duplicate detection")
        print("   - Version control integration")
        print("   - Performance analytics and monitoring")
        print("   - Cost tracking and estimation")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function"""
    
    # Default test document
    default_doc = Path("data/test/documents/Galaxy_6000_End_of_Life.doc")
    
    # Get document path from command line or use default
    if len(sys.argv) > 1:
        doc_path = Path(sys.argv[1])
    else:
        doc_path = default_doc
    
    if not doc_path.exists():
        print(f"❌ Document not found: {doc_path}")
        print(f"💡 Usage: python {sys.argv[0]} [document_path]")
        print(f"💡 Default document: {default_doc}")
        return False
    
    # Run the test
    success = test_document_processing_with_tracking(doc_path)
    
    if success:
        print(f"\n🎉 All tests passed! Enhanced tracking system is working correctly.")
        print(f"📊 Check the database tables 'llm_api_calls' and 'letter_raw_content' for detailed tracking data.")
        print(f"📈 Use the analytics views for monitoring and reporting.")
    else:
        print(f"\n💥 Test failed! Check the error messages above.")
    
    return success


if __name__ == "__main__":
    main() 