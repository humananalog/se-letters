#!/usr/bin/env python3
"""
Comprehensive Range Demo - SOTA Product Range Mapping
Well-organized demonstration of finding ALL products in ranges/series

CRITICAL BUSINESS INSIGHT:
Obsolescence letters mention PRODUCT RANGES that apply to MULTIPLE products:
- "Galaxy 6000" → Galaxy 6000 250VA, 500VA, 1000VA, 3-phase variants, etc.
- "SEPAM 40" → All SEPAM 40 series protection relays and configurations
- "Masterpact NT" → All NT series circuit breakers with different ratings

This demo shows comprehensive range mapping with organized outputs.

Version: 1.0.0
Author: SE Letters Team
"""

import sys
from pathlib import Path

# Add project root to path  
sys.path.append(str(Path(__file__).parent.parent.parent))

import json
import time
import pandas as pd
from typing import Dict, Any, List
from loguru import logger

from scripts.sandbox.sota_range_mapping_service import SOTARangeMappingService


def create_comprehensive_analysis_report(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create comprehensive analysis report across all test scenarios"""
    
    report = {
        'executive_summary': {
            'total_scenarios_tested': len(results),
            'total_ranges_found': sum(len(r['result'].detected_ranges) for r in results),
            'total_products_identified': sum(r['result'].total_products_found for r in results),
            'average_processing_time_ms': sum(r['result'].processing_time_ms for r in results) / len(results),
            'confidence_distribution': {}
        },
        'scenario_analysis': [],
        'business_impact_summary': {
            'all_affected_brands': set(),
            'all_device_categories': set(),
            'criticality_distribution': {},
            'modernization_scope_analysis': {}
        },
        'range_mapping_insights': {
            'most_productive_ranges': [],
            'complexity_analysis': {},
            'brand_coverage_analysis': {}
        }
    }
    
    # Analyze each scenario
    for scenario_data in results:
        scenario = scenario_data['scenario']
        result = scenario_data['result']
        
        scenario_analysis = {
            'scenario_name': scenario['name'],
            'input_identifier': scenario['product_identifier'],
            'ranges_detected': len(result.detected_ranges),
            'products_found': result.total_products_found,
            'confidence_level': result.confidence_level,
            'processing_time_ms': result.processing_time_ms,
            'business_criticality': result.business_analysis.get('business_criticality', 'unknown'),
            'modernization_scope': result.business_analysis.get('modernization_scope', 'unknown'),
            'range_details': []
        }
        
        # Detailed range analysis
        for range_obj in result.detected_ranges:
            range_detail = {
                'range_identifier': range_obj.range_identifier,
                'range_label': range_obj.range_label,
                'subrange_label': range_obj.subrange_label,
                'product_count': range_obj.total_products,
                'range_confidence': range_obj.range_confidence,
                'primary_brands': list(range_obj.coverage_analysis['brand_coverage'].keys())[:3],
                'device_types_count': len(range_obj.coverage_analysis['device_type_coverage']),
                'complexity': range_obj.business_impact['complexity_assessment']
            }
            scenario_analysis['range_details'].append(range_detail)
        
        report['scenario_analysis'].append(scenario_analysis)
        
        # Aggregate business impact data
        report['business_impact_summary']['all_affected_brands'].update(
            result.business_analysis.get('affected_brands', [])
        )
        report['business_impact_summary']['all_device_categories'].update(
            result.business_analysis.get('affected_device_types', [])
        )
        
        # Count criticality and modernization scope
        criticality = result.business_analysis.get('business_criticality', 'unknown')
        modernization = result.business_analysis.get('modernization_scope', 'unknown')
        
        report['business_impact_summary']['criticality_distribution'][criticality] = \
            report['business_impact_summary']['criticality_distribution'].get(criticality, 0) + 1
        
        report['business_impact_summary']['modernization_scope_analysis'][modernization] = \
            report['business_impact_summary']['modernization_scope_analysis'].get(modernization, 0) + 1
    
    # Convert sets to lists for JSON serialization
    report['business_impact_summary']['all_affected_brands'] = list(
        report['business_impact_summary']['all_affected_brands']
    )
    report['business_impact_summary']['all_device_categories'] = list(
        report['business_impact_summary']['all_device_categories']
    )
    
    # Confidence level distribution
    confidence_counts = {}
    for scenario_data in results:
        confidence = scenario_data['result'].confidence_level
        confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1
    report['executive_summary']['confidence_distribution'] = confidence_counts
    
    # Range mapping insights
    all_ranges = []
    for scenario_data in results:
        all_ranges.extend(scenario_data['result'].detected_ranges)
    
    # Most productive ranges (by product count)
    sorted_ranges = sorted(all_ranges, key=lambda x: x.total_products, reverse=True)
    report['range_mapping_insights']['most_productive_ranges'] = [
        {
            'range_identifier': r.range_identifier,
            'product_count': r.total_products,
            'confidence': r.range_confidence,
            'complexity': r.business_impact['complexity_assessment']
        }
        for r in sorted_ranges[:10]
    ]
    
    # Complexity analysis
    complexity_counts = {}
    brand_coverage = {}
    
    for range_obj in all_ranges:
        complexity = range_obj.business_impact['complexity_assessment']
        complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
        
        for brand, count in range_obj.coverage_analysis['brand_coverage'].items():
            brand_coverage[brand] = brand_coverage.get(brand, 0) + count
    
    report['range_mapping_insights']['complexity_analysis'] = complexity_counts
    report['range_mapping_insights']['brand_coverage_analysis'] = dict(
        sorted(brand_coverage.items(), key=lambda x: x[1], reverse=True)[:10]
    )
    
    return report


def export_organized_results(
    results: List[Dict[str, Any]], 
    comprehensive_report: Dict[str, Any]
) -> Dict[str, str]:
    """Export results in well-organized formats"""
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    exported_files = {}
    
    # 1. Executive Summary JSON
    summary_data = {
        'sota_range_mapping_executive_summary': {
            'generation_timestamp': timestamp,
            'summary': comprehensive_report['executive_summary'],
            'business_impact': comprehensive_report['business_impact_summary'],
            'key_insights': {
                'total_product_universe_mapped': comprehensive_report['executive_summary']['total_products_identified'],
                'range_coverage_efficiency': f"{comprehensive_report['executive_summary']['total_ranges_found']} ranges mapped",
                'average_processing_speed': f"{comprehensive_report['executive_summary']['average_processing_time_ms']:.1f}ms per range",
                'business_scope': f"{len(comprehensive_report['business_impact_summary']['all_affected_brands'])} brands affected"
            }
        }
    }
    
    summary_file = f"executive_summary_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary_data, f, indent=2)
    exported_files['executive_summary'] = summary_file
    
    # 2. Detailed Results JSON
    detailed_data = {
        'sota_range_mapping_detailed_analysis': {
            'generation_timestamp': timestamp,
            'comprehensive_report': comprehensive_report,
            'scenario_results': []
        }
    }
    
    for scenario_data in results:
        scenario_export = {
            'scenario': scenario_data['scenario'],
            'result_summary': {
                'ranges_detected': len(scenario_data['result'].detected_ranges),
                'products_found': scenario_data['result'].total_products_found,
                'confidence_level': scenario_data['result'].confidence_level,
                'processing_time_ms': scenario_data['result'].processing_time_ms
            },
            'business_analysis': scenario_data['result'].business_analysis,
            'detected_ranges': []
        }
        
        for range_obj in scenario_data['result'].detected_ranges:
            range_export = {
                'range_identification': {
                    'range_identifier': range_obj.range_identifier,
                    'range_label': range_obj.range_label,
                    'subrange_label': range_obj.subrange_label,
                    'product_line': range_obj.product_line
                },
                'range_metrics': {
                    'total_products': range_obj.total_products,
                    'range_confidence': range_obj.range_confidence,
                    'complexity_assessment': range_obj.business_impact['complexity_assessment']
                },
                'coverage_analysis': range_obj.coverage_analysis,
                'business_impact': range_obj.business_impact,
                'sample_products': [
                    {
                        'product_identifier': p.product_identifier,
                        'product_description': p.product_description,
                        'brand_label': p.brand_label,
                        'devicetype_label': p.devicetype_label,
                        'confidence_score': p.confidence_score,
                        'match_reason': p.match_reason
                    }
                    for p in range_obj.products[:10]  # Top 10 samples
                ]
            }
            scenario_export['detected_ranges'].append(range_export)
        
        detailed_data['sota_range_mapping_detailed_analysis']['scenario_results'].append(scenario_export)
    
    detailed_file = f"detailed_analysis_{timestamp}.json"
    with open(detailed_file, 'w') as f:
        json.dump(detailed_data, f, indent=2)
    exported_files['detailed_analysis'] = detailed_file
    
    # 3. Business Report CSV for Excel
    business_rows = []
    for scenario_data in results:
        for range_obj in scenario_data['result'].detected_ranges:
            for product in range_obj.products:
                business_rows.append({
                    'Scenario': scenario_data['scenario']['name'],
                    'Input_Identifier': scenario_data['scenario']['product_identifier'],
                    'Range_Label': range_obj.range_label,
                    'Subrange_Label': range_obj.subrange_label,
                    'Product_Identifier': product.product_identifier,
                    'Product_Description': product.product_description,
                    'Brand_Label': product.brand_label,
                    'Device_Type': product.devicetype_label,
                    'PL_Services': product.pl_services,
                    'Confidence_Score': product.confidence_score,
                    'Match_Reason': product.match_reason,
                    'Series_Membership': product.series_membership,
                    'Range_Confidence': range_obj.range_confidence,
                    'Business_Criticality': scenario_data['result'].business_analysis.get('business_criticality', ''),
                    'Modernization_Scope': scenario_data['result'].business_analysis.get('modernization_scope', '')
                })
    
    if business_rows:
        business_df = pd.DataFrame(business_rows)
        business_file = f"business_analysis_{timestamp}.csv"
        business_df.to_csv(business_file, index=False)
        exported_files['business_csv'] = business_file
    
    return exported_files


def run_comprehensive_demo():
    """Run comprehensive SOTA range mapping demonstration"""
    
    logger.info("🚀 SOTA Range Mapping - Comprehensive Demo")
    logger.info("🎯 Finding ALL products in ranges/series from obsolescence letters")
    logger.info("📊 Well-organized outputs for business analysis")
    
    # Initialize SOTA service
    try:
        mapping_service = SOTARangeMappingService()
    except Exception as e:
        logger.error(f"❌ Failed to initialize mapping service: {e}")
        return
    
    # Comprehensive test scenarios focusing on product series
    test_scenarios = [
        {
            "name": "Galaxy UPS Series - Complete Product Universe",
            "description": "Finding ALL Galaxy UPS products across all power ratings",
            "product_identifier": "Galaxy 6000",
            "range_label": "Galaxy",
            "subrange_label": "6000",
            "product_line": "SPIBS",
            "context_description": "MGE Galaxy UPS series 6000 range uninterruptible power supply all variants",
            "business_context": "UPS obsolescence affects multiple power ratings and configurations"
        },
        {
            "name": "SEPAM Protection Family - Digital Relay Universe",
            "description": "Finding ALL SEPAM protection relay products and configurations",
            "product_identifier": "SEPAM 2040",
            "range_label": "SEPAM",
            "subrange_label": "40",
            "product_line": "DPIBS",
            "context_description": "SEPAM protection relay series 40 range digital protection all models",
            "business_context": "Protection relay obsolescence affects critical electrical protection systems"
        },
        {
            "name": "Masterpact Circuit Breaker Series - Switchgear Universe",
            "description": "Finding ALL Masterpact NT switchgear products and ratings",
            "product_identifier": "Masterpact NT",
            "range_label": "Masterpact",
            "subrange_label": "NT",
            "product_line": "PPIBS",
            "context_description": "Masterpact NT circuit breaker series low voltage switchgear all ratings",
            "business_context": "Circuit breaker obsolescence affects electrical distribution systems"
        },
        {
            "name": "Altivar Drive Series - Motor Control Universe",
            "description": "Finding ALL Altivar variable speed drive products",
            "product_identifier": "Altivar 71",
            "range_label": "Altivar",
            "subrange_label": "71",
            "product_line": "PPIBS",
            "context_description": "Altivar 71 variable speed drive series motor control all power ratings",
            "business_context": "Motor drive obsolescence affects industrial automation systems"
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        logger.info(f"\n{'='*120}")
        logger.info(f"🧪 Test Scenario {i}: {scenario['name']}")
        logger.info(f"📝 Description: {scenario['description']}")
        logger.info(f"💼 Business Context: {scenario['business_context']}")
        logger.info(f"{'='*120}")
        
        try:
            # Execute SOTA range mapping
            start_time = time.time()
            
            result = mapping_service.map_letter_to_product_ranges(
                product_identifier=scenario["product_identifier"],
                range_label=scenario["range_label"],
                subrange_label=scenario["subrange_label"],
                product_line=scenario["product_line"],
                context_description=scenario["context_description"],
                include_similar_ranges=True
            )
            
            processing_time = time.time() - start_time
            
            # Store results
            results.append({
                'scenario': scenario,
                'result': result,
                'processing_time': processing_time
            })
            
            # Display summary results
            logger.info(f"⏱️ Processing Time: {result.processing_time_ms:.1f}ms")
            logger.info(f"🎯 Confidence Level: {result.confidence_level}")
            logger.info(f"📊 Ranges Detected: {len(result.detected_ranges)}")
            logger.info(f"📦 Total Products Found: {result.total_products_found}")
            
            # Business impact summary
            business = result.business_analysis
            logger.info(f"\n💼 Business Impact Summary:")
            logger.info(f"  🏭 Affected Brands: {len(business.get('affected_brands', []))} brands")
            logger.info(f"  🔧 Device Categories: {len(business.get('affected_device_types', []))} categories")
            logger.info(f"  ⚠️ Business Criticality: {business.get('business_criticality', 'unknown')}")
            logger.info(f"  🔄 Modernization Scope: {business.get('modernization_scope', 'unknown')}")
            
            # Range breakdown
            logger.info(f"\n📋 Range Breakdown:")
            for j, range_obj in enumerate(result.detected_ranges, 1):
                logger.info(f"  📦 Range {j}: {range_obj.range_label} / {range_obj.subrange_label}")
                logger.info(f"      🔢 Products: {range_obj.total_products}")
                logger.info(f"      🎯 Confidence: {range_obj.range_confidence:.3f}")
                logger.info(f"      🏭 Primary Brands: {', '.join(list(range_obj.coverage_analysis['brand_coverage'].keys())[:3])}")
                logger.info(f"      📊 Complexity: {range_obj.business_impact['complexity_assessment']}")
                
                # Show top products
                logger.info(f"      📋 Top Products:")
                for k, product in enumerate(range_obj.products[:5], 1):
                    logger.info(f"        {k}. {product.product_identifier} - {product.brand_label}")
                    logger.info(f"           {product.devicetype_label} (confidence: {product.confidence_score:.3f})")
                
                if range_obj.total_products > 5:
                    logger.info(f"        ... and {range_obj.total_products - 5} more products")
            
        except Exception as e:
            logger.error(f"❌ Scenario {i} failed: {e}")
            continue
    
    if not results:
        logger.error("❌ No successful results to analyze")
        return
    
    # Create comprehensive analysis
    logger.info(f"\n{'='*120}")
    logger.info(f"📊 COMPREHENSIVE ANALYSIS & REPORTING")
    logger.info(f"{'='*120}")
    
    comprehensive_report = create_comprehensive_analysis_report(results)
    
    # Display executive summary
    summary = comprehensive_report['executive_summary']
    logger.info(f"📈 Executive Summary:")
    logger.info(f"  🧪 Scenarios Tested: {summary['total_scenarios_tested']}")
    logger.info(f"  📊 Total Ranges Mapped: {summary['total_ranges_found']}")
    logger.info(f"  📦 Total Products Identified: {summary['total_products_identified']}")
    logger.info(f"  ⏱️ Average Processing Time: {summary['average_processing_time_ms']:.1f}ms")
    logger.info(f"  🎯 Confidence Distribution: {summary['confidence_distribution']}")
    
    # Business impact overview
    business_summary = comprehensive_report['business_impact_summary']
    logger.info(f"\n💼 Business Impact Overview:")
    logger.info(f"  🏭 Total Brands Affected: {len(business_summary['all_affected_brands'])}")
    logger.info(f"  🔧 Total Device Categories: {len(business_summary['all_device_categories'])}")
    logger.info(f"  ⚠️ Criticality Distribution: {business_summary['criticality_distribution']}")
    logger.info(f"  🔄 Modernization Scope: {business_summary['modernization_scope_analysis']}")
    
    # Export organized results
    logger.info(f"\n📁 Exporting Well-Organized Results...")
    exported_files = export_organized_results(results, comprehensive_report)
    
    logger.info(f"✅ Results exported to multiple formats:")
    for file_type, file_path in exported_files.items():
        logger.info(f"  📄 {file_type.replace('_', ' ').title()}: {file_path}")
    
    # Final summary
    logger.info(f"\n🎉 SOTA Range Mapping Demo Complete!")
    logger.info(f"✅ Successfully mapped {summary['total_ranges_found']} ranges to {summary['total_products_identified']} products")
    logger.info(f"📊 Business impact across {len(business_summary['all_affected_brands'])} brands")
    logger.info(f"📁 Comprehensive outputs ready for business analysis")
    
    return exported_files


if __name__ == "__main__":
    try:
        exported_files = run_comprehensive_demo()
        logger.info("🎯 Demo completed successfully!")
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        raise 