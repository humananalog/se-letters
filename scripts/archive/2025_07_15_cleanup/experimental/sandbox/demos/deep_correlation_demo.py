#!/usr/bin/env python3
"""
Deep Field Correlation Demo
Enhanced product mapping using ALL IBcatalogue fields

Features:
- Deep correlation analysis across PRODUCT_IDENTIFIER, PRODUCT_TYPE, 
  PRODUCT_DESCRIPTION
- Brand intelligence with BRAND_CODE, BRAND_LABEL correlation
- Enhanced range matching with RANGE_CODE, SUBRANGE_CODE
- Device type correlation with DEVICETYPE_LABEL
- Multi-dimensional semantic scoring and pattern recognition
- Product family detection and cross-field validation

Version: 3.0.0
Author: SE Letters Team
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

import json
import time
from typing import Dict, Any
from loguru import logger

from scripts.sandbox.product_mapping_service_v3 import (
    EnhancedProductMappingServiceV3
)


def analyze_field_coverage(mapping_service: EnhancedProductMappingServiceV3) -> Dict[str, Any]:
    """Analyze field coverage in the IBcatalogue database"""
    
    logger.info("📊 Analyzing IBcatalogue Field Coverage")
    
    df = mapping_service.products_df
    
    analysis = {
        'total_products': len(df),
        'field_statistics': {},
        'sample_values': {},
        'pl_services_distribution': {},
        'brand_distribution': {},
        'device_type_distribution': {},
        'range_distribution': {}
    }
    
    # Field coverage analysis
    key_fields = [
        'PRODUCT_IDENTIFIER', 'PRODUCT_TYPE', 'PRODUCT_DESCRIPTION',
        'BRAND_CODE', 'BRAND_LABEL', 'RANGE_CODE', 'RANGE_LABEL',
        'SUBRANGE_CODE', 'SUBRANGE_LABEL', 'DEVICETYPE_LABEL', 'PL_SERVICES'
    ]
    
    for field in key_fields:
        non_empty = df[field].fillna('').str.strip().str.len() > 0
        analysis['field_statistics'][field] = {
            'coverage_count': non_empty.sum(),
            'coverage_percentage': (non_empty.sum() / len(df)) * 100,
            'unique_values': df[field].nunique(),
            'sample_values': df[field].dropna().head(5).tolist()
        }
    
    # Distribution analyses
    analysis['pl_services_distribution'] = df['PL_SERVICES'].value_counts().head(10).to_dict()
    analysis['brand_distribution'] = df['BRAND_LABEL'].value_counts().head(10).to_dict()
    analysis['device_type_distribution'] = df['DEVICETYPE_LABEL'].value_counts().head(10).to_dict()
    analysis['range_distribution'] = df['RANGE_LABEL'].value_counts().head(15).to_dict()
    
    # Log key insights
    logger.info(f"📈 Total Products in Database: {analysis['total_products']:,}")
    logger.info(f"🔍 Field Coverage Analysis:")
    
    for field, stats in analysis['field_statistics'].items():
        logger.info(f"  • {field}: {stats['coverage_percentage']:.1f}% ({stats['coverage_count']:,} products)")
    
    logger.info(f"\n📊 PL_SERVICES Distribution:")
    for pl, count in list(analysis['pl_services_distribution'].items())[:5]:
        logger.info(f"  • {pl}: {count:,} products")
    
    logger.info(f"\n🏷️ Top Brands:")
    for brand, count in list(analysis['brand_distribution'].items())[:5]:
        logger.info(f"  • {brand}: {count:,} products")
    
    return analysis


def test_deep_correlation_scenarios():
    """Test various deep correlation scenarios"""
    
    logger.info("🧪 Testing Deep Correlation Scenarios")
    
    # Initialize enhanced mapping service
    mapping_service = EnhancedProductMappingServiceV3()
    
    # Analyze database first
    field_analysis = analyze_field_coverage(mapping_service)
    
    # Comprehensive test scenarios leveraging all fields
    test_scenarios = [
        {
            "name": "Galaxy UPS Deep Analysis",
            "description": "Testing UPS product identification with brand intelligence",
            "product_identifier": "Galaxy 6000",
            "range_label": "Galaxy", 
            "subrange_label": "6000",
            "product_line": "SPIBS",
            "context_description": "MGE Galaxy UPS uninterruptible power supply 6000 VA industrial three-phase",
            "expected_correlations": ["UPS", "Galaxy", "MGE", "Power Supply"]
        },
        {
            "name": "SEPAM Protection Relay Multi-Field Correlation",
            "description": "Testing protection relay with device type and technical specifications",
            "product_identifier": "SEPAM 2040",
            "range_label": "SEPAM",
            "subrange_label": "2040", 
            "product_line": "DPIBS",
            "context_description": "SEPAM digital protection relay microprocessor-based protective relay electrical protection",
            "expected_correlations": ["Protection", "Relay", "Digital", "SEPAM"]
        },
        {
            "name": "Masterpact Circuit Breaker Brand Intelligence",
            "description": "Testing circuit breaker with brand and device type correlation",
            "product_identifier": "Masterpact NT06",
            "range_label": "Masterpact",
            "subrange_label": "NT",
            "product_line": "PPIBS",
            "context_description": "Masterpact NT circuit breaker low voltage switchgear Schneider Electric",
            "expected_correlations": ["Circuit Breaker", "Masterpact", "Schneider", "Switchgear"]
        },
        {
            "name": "Altivar Variable Speed Drive Device Type Analysis",
            "description": "Testing motor drive with product type and technical correlation",
            "product_identifier": "Altivar 71",
            "range_label": "Altivar",
            "subrange_label": "71",
            "product_line": "PPIBS",
            "context_description": "Altivar 71 variable speed drive motor control variable frequency drive VFD",
            "expected_correlations": ["Motor Drive", "Variable Speed", "VFD", "Altivar"]
        },
        {
            "name": "Modicon PLC Controller Product Family",
            "description": "Testing PLC with product family and brand correlation",
            "product_identifier": "Modicon M580",
            "range_label": "Modicon",
            "subrange_label": "M580",
            "product_line": "PPIBS", 
            "context_description": "Modicon M580 programmable logic controller PLC automation controller Schneider",
            "expected_correlations": ["PLC", "Controller", "Modicon", "Automation"]
        }
    ]
    
    results_summary = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        logger.info(f"\n{'='*90}")
        logger.info(f"🧪 Test Scenario {i}: {scenario['name']}")
        logger.info(f"📝 Description: {scenario['description']}")
        logger.info(f"{'='*90}")
        
        # Execute deep correlation mapping
        start_time = time.time()
        
        result = mapping_service.map_product_with_deep_correlation(
            product_identifier=scenario["product_identifier"],
            range_label=scenario["range_label"],
            subrange_label=scenario["subrange_label"], 
            product_line=scenario["product_line"],
            context_description=scenario["context_description"],
            max_candidates=8
        )
        
        processing_time = time.time() - start_time
        
        # Analyze results
        logger.info(f"⏱️ Processing Time: {result.processing_time_ms:.1f}ms")
        logger.info(f"🎯 Confidence Level: {result.confidence_level}")
        logger.info(f"📊 Search Space Reduction: {result.search_space_reduction['original']:,} → {result.search_space_reduction['final_candidates']}")
        
        # Deep correlation analysis
        correlation_analysis = result.correlation_analysis
        logger.info(f"\n🔍 Deep Correlation Analysis:")
        
        if correlation_analysis.get('product_family_detected'):
            family = correlation_analysis['product_family_detected']
            logger.info(f"  👥 Product Family: {family['family']} (confidence: {family['confidence']:.2f})")
            logger.info(f"      Pattern Matched: {family['matched_pattern']}")
        
        if correlation_analysis.get('brand_correlations'):
            logger.info(f"  🏷️ Brand Correlations:")
            for brand_corr in correlation_analysis['brand_correlations']:
                logger.info(f"      • {brand_corr['brand']}: {brand_corr['variant_matched']} (confidence: {brand_corr['confidence']:.2f})")
        
        if correlation_analysis.get('device_type_correlations'):
            logger.info(f"  🛠️ Device Type Correlations:")
            for device_corr in correlation_analysis['device_type_correlations']:
                logger.info(f"      • {device_corr['device_type']}: {device_corr['pattern_matched']} (confidence: {device_corr['confidence']:.2f})")
        
        # Best match analysis
        if result.best_match:
            best = result.best_match
            logger.info(f"\n🏆 Best Match Analysis:")
            logger.info(f"  📦 Product: {best.product_identifier}")
            logger.info(f"  📝 Type: {best.product_type}")
            logger.info(f"  📄 Description: {best.product_description[:100]}...")
            logger.info(f"  🏷️ Brand: {best.brand_label} ({best.brand_code})")
            logger.info(f"  📊 Range: {best.range_label} / {best.subrange_label}")
            logger.info(f"  🔧 Device Type: {best.devicetype_label}")
            logger.info(f"  💼 PL Services: {best.pl_services}")
            logger.info(f"  🎯 Confidence: {best.confidence_score:.3f}")
            
            # Detailed score breakdown
            logger.info(f"\n📊 Score Breakdown:")
            for field, scores in best.match_breakdown.items():
                if isinstance(scores, dict) and 'weighted_score' in scores:
                    logger.info(f"    • {field.replace('_', ' ').title()}: {scores['raw_score']:.3f} × {scores['weight']:.2f} = {scores['weighted_score']:.3f}")
                elif isinstance(scores, (int, float)):
                    logger.info(f"    • {field.replace('_', ' ').title()}: {scores:.3f}")
        
        # Top candidates with field analysis
        logger.info(f"\n🏅 Top Candidates with Multi-Field Analysis:")
        for j, candidate in enumerate(result.candidates[:5], 1):
            logger.info(f"\n  {j}. {candidate.product_identifier} (Score: {candidate.confidence_score:.3f})")
            logger.info(f"     🏷️ {candidate.brand_label} | 📦 {candidate.range_label}")
            logger.info(f"     🔧 {candidate.devicetype_label} | 💼 {candidate.pl_services}")
            
            # Key field matches
            key_matches = []
            if scenario["product_identifier"].lower() in candidate.product_identifier.lower():
                key_matches.append("Identifier Match")
            if any(term in candidate.product_type.lower() for term in scenario["context_description"].lower().split()):
                key_matches.append("Type Match")
            if any(term in candidate.product_description.lower() for term in scenario["expected_correlations"]):
                key_matches.append("Description Match")
            
            if key_matches:
                logger.info(f"     ✅ Key Matches: {', '.join(key_matches)}")
        
        # Record results for summary
        results_summary.append({
            'scenario': scenario['name'],
            'confidence_level': result.confidence_level,
            'best_score': result.best_match.confidence_score if result.best_match else 0.0,
            'candidates_found': len(result.candidates),
            'processing_time_ms': result.processing_time_ms,
            'family_detected': bool(correlation_analysis.get('product_family_detected')),
            'brand_correlations': len(correlation_analysis.get('brand_correlations', [])),
            'device_correlations': len(correlation_analysis.get('device_type_correlations', []))
        })
        
        # Export individual result
        output_file = mapping_service.export_deep_mapping_results(result, "json")
        logger.info(f"📁 Results exported to: {output_file}")
    
    # Final summary
    logger.info(f"\n{'='*90}")
    logger.info(f"📋 DEEP CORRELATION ANALYSIS SUMMARY")
    logger.info(f"{'='*90}")
    
    total_scenarios = len(results_summary)
    exact_matches = sum(1 for r in results_summary if r['confidence_level'] == 'EXACT')
    high_matches = sum(1 for r in results_summary if r['confidence_level'] == 'HIGH')
    
    logger.info(f"🧪 Total Scenarios Tested: {total_scenarios}")
    logger.info(f"🎯 EXACT Confidence: {exact_matches}/{total_scenarios} ({exact_matches/total_scenarios*100:.1f}%)")
    logger.info(f"📈 HIGH+ Confidence: {exact_matches + high_matches}/{total_scenarios} ({(exact_matches + high_matches)/total_scenarios*100:.1f}%)")
    
    avg_processing_time = sum(r['processing_time_ms'] for r in results_summary) / len(results_summary)
    logger.info(f"⏱️ Average Processing Time: {avg_processing_time:.1f}ms")
    
    families_detected = sum(1 for r in results_summary if r['family_detected'])
    logger.info(f"👥 Product Families Detected: {families_detected}/{total_scenarios} ({families_detected/total_scenarios*100:.1f}%)")
    
    total_brand_correlations = sum(r['brand_correlations'] for r in results_summary)
    total_device_correlations = sum(r['device_correlations'] for r in results_summary)
    logger.info(f"🏷️ Total Brand Correlations Found: {total_brand_correlations}")
    logger.info(f"🛠️ Total Device Type Correlations Found: {total_device_correlations}")
    
    # Export comprehensive summary
    summary_export = {
        'analysis_timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'database_analysis': field_analysis,
        'test_scenarios': results_summary,
        'overall_metrics': {
            'total_scenarios': total_scenarios,
            'exact_matches': exact_matches,
            'high_plus_matches': exact_matches + high_matches,
            'success_rate': (exact_matches + high_matches) / total_scenarios * 100,
            'average_processing_time_ms': avg_processing_time,
            'families_detected': families_detected,
            'brand_correlations_total': total_brand_correlations,
            'device_correlations_total': total_device_correlations
        }
    }
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    summary_file = f"scripts/sandbox/deep_correlation_summary_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary_export, f, indent=2)
    
    logger.info(f"📊 Comprehensive summary exported to: {summary_file}")
    
    return results_summary


def demonstrate_field_correlation_matrix():
    """Demonstrate correlation matrix between different fields"""
    
    logger.info("\n🔗 Field Correlation Matrix Analysis")
    
    mapping_service = EnhancedProductMappingServiceV3()
    df = mapping_service.products_df
    
    # Sample product for correlation analysis
    sample_product = "Galaxy 6000"
    sample_context = "UPS uninterruptible power supply MGE Galaxy"
    
    # Find products matching the sample
    galaxy_products = df[df['range_label_norm'].str.contains('galaxy', na=False)].head(10)
    
    if not galaxy_products.empty:
        logger.info(f"🔍 Found {len(galaxy_products)} Galaxy products for correlation analysis")
        
        # Analyze field correlations
        field_correlations = {}
        
        for _, product in galaxy_products.iterrows():
            correlation_score = {}
            
            # Product Identifier correlation
            correlation_score['identifier'] = mapping_service._calculate_identifier_similarity(
                sample_product.lower(), product['product_identifier_norm']
            )
            
            # Product Type correlation
            correlation_score['type'] = mapping_service._calculate_semantic_similarity(
                sample_context, product['product_type_norm']
            )
            
            # Description correlation
            correlation_score['description'] = mapping_service._calculate_description_similarity(
                sample_context, product['description_norm']
            )
            
            # Brand correlation
            correlation_score['brand'] = mapping_service._calculate_brand_correlation(
                sample_context, product['brand_label_norm'], product['BRAND_CODE'], 
                {'brand_correlations': [{'brand': 'mge', 'confidence': 0.8}]}
            )
            
            # Range correlation
            correlation_score['range'] = mapping_service._calculate_enhanced_range_correlation(
                "Galaxy", "6000", product['range_label_norm'], product['subrange_label_norm']
            )
            
            product_id = product['PRODUCT_IDENTIFIER']
            field_correlations[product_id] = correlation_score
            
            logger.info(f"📊 {product_id}:")
            logger.info(f"    • Identifier: {correlation_score['identifier']:.3f}")
            logger.info(f"    • Type: {correlation_score['type']:.3f}")
            logger.info(f"    • Description: {correlation_score['description']:.3f}")
            logger.info(f"    • Brand: {correlation_score['brand']:.3f}")
            logger.info(f"    • Range: {correlation_score['range']:.3f}")
            
            total_score = sum(correlation_score.values()) / len(correlation_score)
            logger.info(f"    🎯 Average Score: {total_score:.3f}")
    
    return field_correlations


if __name__ == "__main__":
    logger.info("🚀 Deep Field Correlation Analysis - Comprehensive Demo")
    logger.info("🔍 Leveraging ALL IBcatalogue fields for enhanced product mapping")
    
    try:
        # Run comprehensive deep correlation tests
        test_results = test_deep_correlation_scenarios()
        
        # Demonstrate field correlation matrix
        field_correlations = demonstrate_field_correlation_matrix()
        
        logger.info("\n✅ Deep Correlation Analysis Complete!")
        logger.info("📊 All results have been exported to JSON files for detailed review")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        raise 