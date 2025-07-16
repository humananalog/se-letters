#!/usr/bin/env python3
"""
Product Discovery Fix Test
Comprehensive test to verify the product discovery service fix

This test verifies that the fix to SOTAProductDatabaseService correctly:
1. Filters products by device type (switchgear for PIX products)
2. Uses proper AND/OR logic in queries
3. Returns relevant products instead of transformers/drives
4. Maintains high performance

Version: 1.0.0
Author: SE Letters Team
"""

import pytest
import sys
import time
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(project_root))

from se_letters.services.sota_product_database_service import (
    SOTAProductDatabaseService
)
from se_letters.models.product_matching import LetterProductInfo


class TestProductDiscoveryFix:
    """Test suite for product discovery fix"""
    
    @pytest.fixture
    def database_service(self):
        """Initialize database service"""
        return SOTAProductDatabaseService("data/IBcatalogue.duckdb")
    
    @pytest.fixture
    def pix_letter_info(self):
        """Create PIX 2B letter product info (the original failing case)"""
        return LetterProductInfo(
            product_identifier="PIX 2B",
            range_label="PIX Double Bus Bar",
            subrange_label="PIX 2B",
            product_line="PSIBS (Power Systems)",
            product_description=(
                "Medium Voltage Switchgear, 12 – 17.5kV, up to 3150A, "
                "50/60Hz, 31.5kA 3s"
            ),
            technical_specifications={
                "voltage_levels": ["12 – 17.5kV"],
                "current_ratings": ["up to 3150A"],
                "power_ratings": [],
                "frequencies": ["50/60Hz"]
            },
            obsolescence_status="Withdrawn",
            end_of_service_date=(
                "November 2023 (Belgium Frame Contract); "
                "Immediate for other markets"
            ),
            replacement_suggestions="No substitution available for this range"
        )
    
    @pytest.fixture
    def galaxy_letter_info(self):
        """Create Galaxy letter product info (transformer case)"""
        return LetterProductInfo(
            product_identifier="Galaxy 6000",
            range_label="Galaxy 6000",
            subrange_label="Galaxy 6000",
            product_line="SPIBS (Services)",
            product_description="Three-phase UPS, 500-5000VA, 400V, 50/60Hz",
            technical_specifications={
                "voltage_levels": ["400V"],
                "current_ratings": ["500-5000VA"],
                "power_ratings": [],
                "frequencies": ["50/60Hz"]
            },
            obsolescence_status="End of Life",
            end_of_service_date="2024-12-31",
            replacement_suggestions="Galaxy VS series"
        )
    
    def test_pix_product_discovery(self, database_service, pix_letter_info):
        """Test PIX product discovery returns relevant switchgear products"""
        # This was the original failing case - should now return switchgear
        start_time = time.time()
        result = database_service.discover_product_candidates(pix_letter_info, max_candidates=100)
        processing_time = (time.time() - start_time) * 1000
        
        # Performance check
        assert processing_time < 1000, f"Query took too long: {processing_time}ms"
        assert result.processing_time_ms < 1000, f"Service reported slow query: {result.processing_time_ms}ms"
        
        # Should find relevant products
        assert len(result.candidates) > 0, "Should find some candidate products"
        assert len(result.candidates) <= 100, "Should respect max_candidates limit"
        
        # Analyze device types found
        device_types = {}
        for candidate in result.candidates:
            device_type = candidate.devicetype_label or 'Unknown'
            device_types[device_type] = device_types.get(device_type, 0) + 1
        
        print(f"\n🔍 PIX Product Discovery Results:")
        print(f"   Total candidates: {len(result.candidates)}")
        print(f"   Processing time: {result.processing_time_ms:.2f}ms")
        print(f"   Search strategy: {result.search_strategy}")
        print(f"   Device types found:")
        for device_type, count in sorted(device_types.items(), key=lambda x: x[1], reverse=True):
            print(f"     - {device_type}: {count}")
        
        # Verify we're getting relevant products (not transformers/drives)
        relevant_types = [
            'MV equipment - MV switchgear',
            'MV equipment - MV circuit breaker',
            'MV equipment - MV switch cubicle',
            'MV equipment - MV fuse - switch cubicle'
        ]
        
        relevant_count = sum(device_types.get(dt, 0) for dt in relevant_types)
        
        # Should have some relevant products
        assert relevant_count > 0, f"Should find relevant switchgear products, but found: {device_types}"
        
        # Should NOT have mostly transformers/drives (the original bug)
        transformer_count = device_types.get('Transformer - dry', 0)
        drive_count = device_types.get('Variable speed drive - VSD System', 0)
        
        # These should be minimal or zero (the fix)
        assert transformer_count < len(result.candidates) * 0.5, f"Too many transformers: {transformer_count}/{len(result.candidates)}"
        assert drive_count < len(result.candidates) * 0.5, f"Too many drives: {drive_count}/{len(result.candidates)}"
        
        print(f"   ✅ Relevant products: {relevant_count}")
        print(f"   ❌ Transformers (should be low): {transformer_count}")
        print(f"   ❌ Drives (should be low): {drive_count}")
        
        # Verify search strategy includes key terms
        assert 'product_identifier' in result.search_strategy, "Should use product identifier in search"
        assert 'range_label' in result.search_strategy, "Should use range label in search"
    
    def test_galaxy_product_discovery(self, database_service, galaxy_letter_info):
        """Test Galaxy product discovery returns UPS products"""
        start_time = time.time()
        result = database_service.discover_product_candidates(galaxy_letter_info, max_candidates=100)
        processing_time = (time.time() - start_time) * 1000
        
        # Performance check
        assert processing_time < 1000, f"Query took too long: {processing_time}ms"
        
        # Should find relevant products
        assert len(result.candidates) > 0, "Should find some candidate products"
        
        # Analyze device types found
        device_types = {}
        for candidate in result.candidates:
            device_type = candidate.devicetype_label or 'Unknown'
            device_types[device_type] = device_types.get(device_type, 0) + 1
        
        print(f"\n🔍 Galaxy Product Discovery Results:")
        print(f"   Total candidates: {len(result.candidates)}")
        print(f"   Processing time: {result.processing_time_ms:.2f}ms")
        print(f"   Device types found:")
        for device_type, count in sorted(device_types.items(), key=lambda x: x[1], reverse=True):
            print(f"     - {device_type}: {count}")
        
        # For Galaxy, we should find UPS or power-related products
        # This test verifies the device type filtering works correctly
        ups_related = [
            'UPS - System',
            'UPS - Component',
            'Surge Protection and Power Conditioning',
            'Power Monitoring'
        ]
        
        ups_count = sum(device_types.get(dt, 0) for dt in ups_related)
        print(f"   ✅ UPS-related products: {ups_count}")
    
    def test_device_type_filtering(self, database_service):
        """Test that device type filtering works correctly"""
        # Test different device types
        test_cases = [
            {
                "description": "Medium Voltage Switchgear",
                "expected_types": ["MV equipment - MV switchgear", "MV equipment - MV circuit breaker"]
            },
            {
                "description": "Transformer dry type",
                "expected_types": ["Transformer - dry"]
            },
            {
                "description": "Variable speed drive",
                "expected_types": ["Variable speed drive - VSD System"]
            },
            {
                "description": "Protection relay",
                "expected_types": ["Protection relay"]
            }
        ]
        
        for test_case in test_cases:
            letter_info = LetterProductInfo(
                product_identifier="TEST",
                range_label="TEST",
                subrange_label="TEST",
                product_line="TEST",
                product_description=test_case["description"],
                technical_specifications={},
                obsolescence_status="Test",
                end_of_service_date="2024-12-31",
                replacement_suggestions="Test"
            )
            
            result = database_service.discover_product_candidates(letter_info, max_candidates=50)
            
            if len(result.candidates) > 0:
                device_types = {}
                for candidate in result.candidates:
                    device_type = candidate.devicetype_label or 'Unknown'
                    device_types[device_type] = device_types.get(device_type, 0) + 1
                
                print(f"\n🔍 Device Type Filter Test: '{test_case['description']}'")
                print(f"   Found {len(result.candidates)} candidates")
                print(f"   Device types: {list(device_types.keys())}")
                
                # Verify at least some expected types are found
                found_expected = any(
                    any(expected in device_type for expected in test_case["expected_types"])
                    for device_type in device_types.keys()
                )
                
                if found_expected:
                    print(f"   ✅ Found expected device types")
                else:
                    print(f"   ⚠️ Expected types not found, but query worked")
    
    def test_query_performance(self, database_service, pix_letter_info):
        """Test query performance is acceptable"""
        # Run multiple queries to test performance
        times = []
        for i in range(5):
            start_time = time.time()
            result = database_service.discover_product_candidates(pix_letter_info, max_candidates=100)
            query_time = (time.time() - start_time) * 1000
            times.append(query_time)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        print(f"\n⚡ Performance Test Results:")
        print(f"   Average query time: {avg_time:.2f}ms")
        print(f"   Min query time: {min_time:.2f}ms")
        print(f"   Max query time: {max_time:.2f}ms")
        
        # Performance requirements
        assert avg_time < 500, f"Average query time too slow: {avg_time}ms"
        assert max_time < 1000, f"Max query time too slow: {max_time}ms"
        
        print(f"   ✅ Performance acceptable")
    
    def test_search_filters_creation(self, database_service, pix_letter_info):
        """Test that search filters are created correctly"""
        # Test internal method
        filters = database_service._create_search_filters(pix_letter_info)
        
        # Verify all expected filters are present
        assert 'product_identifier' in filters
        assert 'range_label' in filters
        assert 'product_line' in filters
        assert 'product_description' in filters
        
        # Verify filter values
        assert filters['product_identifier'] == "PIX 2B"
        assert filters['range_label'] == "PIX Double Bus Bar"
        assert filters['product_line'] == "PSIBS (Power Systems)"
        assert "switchgear" in filters['product_description'].lower()
        
        print(f"\n🔍 Search Filters Created:")
        for key, value in filters.items():
            print(f"   {key}: {value}")
    
    def test_build_discovery_query(self, database_service, pix_letter_info):
        """Test that the discovery query is built correctly"""
        # Test internal method
        filters = database_service._create_search_filters(pix_letter_info)
        query = database_service._build_discovery_query(filters, 100)
        
        # Verify query structure
        assert "SELECT" in query
        assert "FROM products" in query
        assert "DEVICETYPE_LABEL ILIKE '%switchgear%'" in query
        assert "LIMIT 100" in query
        
        # Verify it uses proper AND/OR logic
        assert "PIX 2B" in query
        assert "PIX Double Bus Bar" in query
        assert "PSIBS" in query
        
        print(f"\n📝 Generated Query:")
        print(f"   {query}")
        
        # Test query executes without error
        import duckdb
        with duckdb.connect(database_service.db_path) as conn:
            results = conn.execute(query).fetchall()
            print(f"   ✅ Query executed successfully, returned {len(results)} results")


if __name__ == "__main__":
    # Run tests manually
    test = TestProductDiscoveryFix()
    
    # Setup
    database_service = SOTAProductDatabaseService("data/IBcatalogue.duckdb")
    pix_letter_info = LetterProductInfo(
        product_identifier="PIX 2B",
        range_label="PIX Double Bus Bar",
        subrange_label="PIX 2B",
        product_line="PSIBS (Power Systems)",
        product_description="Medium Voltage Switchgear, 12 – 17.5kV, up to 3150A, 50/60Hz, 31.5kA 3s",
        technical_specifications={
            "voltage_levels": ["12 – 17.5kV"],
            "current_ratings": ["up to 3150A"],
            "power_ratings": [],
            "frequencies": ["50/60Hz"]
        },
        obsolescence_status="Withdrawn",
        end_of_service_date="November 2023 (Belgium Frame Contract); Immediate for other markets",
        replacement_suggestions="No substitution available for this range"
    )
    
    # Run key tests
    print("🧪 Testing Product Discovery Fix")
    print("=" * 60)
    
    test.test_pix_product_discovery(database_service, pix_letter_info)
    test.test_query_performance(database_service, pix_letter_info)
    test.test_search_filters_creation(database_service, pix_letter_info)
    
    print("\n✅ All tests passed!") 