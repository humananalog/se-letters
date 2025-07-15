#!/usr/bin/env python3
"""
Integrated Intelligent Discovery Demo
Combines Enhanced Product Discovery with Intelligent Matching using Grok AI

This demo showcases the complete pipeline:
1. Enhanced Product Discovery (291,683 products found)
2. Intelligent Grok-based Matching (AI-powered selection)
3. Final product recommendations with confidence scoring

Version: 1.0.0
Author: SE Letters Team
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List

from intelligent_product_matching_service import (
    IntelligentProductMatchingService, 
    LetterProductInfo, 
    ProductCandidate
)
from loguru import logger


def load_pix2b_grok_metadata() -> Dict[str, Any]:
    """Load PIX2B grok metadata from the latest JSON output"""
    
    grok_metadata_path = Path(
        "data/output/json_outputs/PIX2B_Phase_out_Letter_22/latest/"
        "grok_metadata.json"
    )
    
    try:
        with open(grok_metadata_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load grok metadata: {e}")
        return {}


def simulate_enhanced_discovery_results() -> Dict[str, List[ProductCandidate]]:
    """Simulate results from enhanced product discovery service"""
    
    # These are realistic examples based on actual discovery results
    return {
        "exact_technical_match": [
            ProductCandidate(
                product_identifier="PIX2B-17KV-3150A",
                product_type="Switchgear",
                product_description="PIX Double Bus Bar 17.5kV 3150A 50/60Hz",
                brand_code="SE",
                brand_label="Schneider Electric",
                range_code="PIX",
                range_label="PIX",
                subrange_code="PIX2B",
                subrange_label="PIX2B",
                devicetype_label="Double Bus Bar",
                pl_services="PSIBS",
                commercial_status="Active",
                confidence_score=0.95,
                source="exact_technical_match"
            ),
            ProductCandidate(
                product_identifier="PIX2B-MV-DBLBUS",
                product_type="Switchgear",
                product_description="PIX Double Bus Bar Medium Voltage",
                brand_code="SE",
                brand_label="Schneider Electric",
                range_code="PIX",
                range_label="PIX",
                subrange_code="PIX2B",
                subrange_label="PIX2B",
                devicetype_label="Double Bus Bar",
                pl_services="PSIBS",
                commercial_status="Active",
                confidence_score=0.88,
                source="exact_technical_match"
            )
        ],
        "range_expansion_search": [
            ProductCandidate(
                product_identifier="PIX-DB-12KV",
                product_type="Switchgear",
                product_description="PIX Double Bus Bar 12kV Configuration",
                brand_code="SE",
                brand_label="Schneider Electric",
                range_code="PIX",
                range_label="PIX",
                subrange_code="PIX_DB",
                subrange_label="PIX_DB",
                devicetype_label="Double Bus Bar",
                pl_services="PSIBS",
                commercial_status="Active",
                confidence_score=0.82,
                source="range_expansion_search"
            ),
            ProductCandidate(
                product_identifier="PIX-2B-SWGR",
                product_type="Switchgear",
                product_description="PIX 2B Switchgear Assembly",
                brand_code="SE",
                brand_label="Schneider Electric",
                range_code="PIX",
                range_label="PIX",
                subrange_code="PIX2B",
                subrange_label="PIX2B",
                devicetype_label="Switchgear",
                pl_services="PSIBS",
                commercial_status="Active",
                confidence_score=0.79,
                source="range_expansion_search"
            )
        ],
                "semantic_similarity_search": [
            ProductCandidate(
                product_identifier="SM6-PIX2B-17KV",
                product_type="Switchgear",
                product_description="SM6 PIX Double Bus Bar 17.5kV",
                brand_code="SE",
                brand_label="Schneider Electric",
                range_code="SM6",
                range_label="SM6",
                subrange_code="PIX2B",
                subrange_label="PIX2B",
                devicetype_label="Double Bus Bar",
                pl_services="PSIBS",
                commercial_status="Active",
                confidence_score=0.75,
                source="semantic_similarity_search"
            ),
            ProductCandidate(
                product_identifier="FLUO-PIX2B-MV",
                product_type="Switchgear",
                product_description="FLUO PIX Double Bus Bar Medium Voltage",
                brand_code="SE",
                brand_label="Schneider Electric",
                range_code="FLUO",
                range_label="FLUO",
                subrange_code="PIX2B",
                subrange_label="PIX2B",
                devicetype_label="Double Bus Bar",
                pl_services="PSIBS",
                commercial_status="Active",
                confidence_score=0.71,
                source="semantic_similarity_search"
            )
        ],
        "specification_fuzzy_search": [
            ProductCandidate(
                product_identifier="PIX2B-15KV-2500A",
                product_type="Switchgear",
                product_description="PIX Double Bus Bar 15kV 2500A",
                brand_code="SE",
                brand_label="Schneider Electric",
                range_code="PIX",
                range_label="PIX",
                subrange_code="PIX2B",
                subrange_label="PIX2B",
                devicetype_label="Double Bus Bar",
                pl_services="PSIBS",
                commercial_status="Active",
                confidence_score=0.68,
                source="specification_fuzzy_search"
            ),
            ProductCandidate(
                product_identifier="PIX2B-17KV-4000A",
                product_type="Switchgear",
                product_description="PIX Double Bus Bar 17.5kV 4000A",
                brand_code="SE",
                brand_label="Schneider Electric",
                range_code="PIX",
                range_label="PIX",
                subrange_code="PIX2B",
                subrange_label="PIX2B",
                devicetype_label="Double Bus Bar",
                pl_services="PSIBS",
                commercial_status="Active",
                confidence_score=0.65,
                source="specification_fuzzy_search"
            )
        ],
        "hybrid_multi_modal_search": [
            ProductCandidate(
                product_identifier="PIX2B-HV-3150",
                product_type="Switchgear",
                product_description="PIX Double Bus Bar 17.5kV 3150A",
                brand_code="SE",
                brand_label="Schneider Electric",
                range_code="PIX",
                range_label="PIX",
                subrange_code="PIX2B",
                subrange_label="PIX2B",
                devicetype_label="Double Bus Bar",
                pl_services="PSIBS",
                commercial_status="Active",
                confidence_score=0.92,
                source="hybrid_multi_modal_search"
            ),
            ProductCandidate(
                product_identifier="PIX2B-MVSG-17KV",
                product_type="Switchgear",
                product_description="PIX2B Medium Voltage Switchgear 17kV",
                brand_code="SE",
                brand_label="Schneider Electric",
                range_code="PIX",
                range_label="PIX",
                subrange_code="PIX2B",
                subrange_label="PIX2B",
                devicetype_label="Switchgear",
                pl_services="PSIBS",
                commercial_status="Active",
                confidence_score=0.87,
                source="hybrid_multi_modal_search"
            )
        ]
    }


def extract_letter_products(grok_metadata: Dict[str, Any]) -> List[LetterProductInfo]:
    """Extract letter products from grok metadata"""
    
    letter_products = []
    
    for product_data in grok_metadata.get('products', []):
        letter_product = LetterProductInfo(
            product_identifier=product_data.get('product_identifier', ''),
            range_label=product_data.get('range_label', ''),
            subrange_label=product_data.get('subrange_label'),
            product_line=product_data.get('product_line', ''),
            product_description=product_data.get('product_description', ''),
            technical_specifications=grok_metadata.get('technical_specifications', {}),
            obsolescence_status=product_data.get('obsolescence_status'),
            end_of_service_date=product_data.get('end_of_service_date'),
            replacement_suggestions=product_data.get('replacement_suggestions')
        )
        letter_products.append(letter_product)
    
    return letter_products


def analyze_discovery_results(discovery_results: Dict[str, List[ProductCandidate]]) -> Dict[str, Any]:
    """Analyze the discovery results to provide statistics"""
    
    total_candidates = 0
    strategy_counts = {}
    confidence_distribution = {"high": 0, "medium": 0, "low": 0}
    
    for strategy, candidates in discovery_results.items():
        strategy_counts[strategy] = len(candidates)
        total_candidates += len(candidates)
        
        for candidate in candidates:
            if candidate.confidence_score >= 0.8:
                confidence_distribution["high"] += 1
            elif candidate.confidence_score >= 0.6:
                confidence_distribution["medium"] += 1
            else:
                confidence_distribution["low"] += 1
    
    return {
        "total_candidates": total_candidates,
        "strategy_counts": strategy_counts,
        "confidence_distribution": confidence_distribution,
        "average_confidence": sum(
            candidate.confidence_score 
            for candidates in discovery_results.values()
            for candidate in candidates
        ) / total_candidates if total_candidates > 0 else 0.0
    }


def main():
    """Main demonstration function"""
    
    print("\n" + "="*80)
    print("🚀 INTEGRATED INTELLIGENT DISCOVERY DEMONSTRATION")
    print("="*80)
    print("Combining Enhanced Product Discovery with Intelligent Grok Matching")
    print("="*80)
    
    start_time = time.time()
    
    # Step 1: Load PIX2B letter metadata
    print("\n🔍 STEP 1: Loading PIX2B Letter Metadata")
    grok_metadata = load_pix2b_grok_metadata()
    
    if not grok_metadata:
        print("❌ Failed to load grok metadata")
        return
    
    print(f"✅ Letter metadata loaded successfully")
    print(f"📋 Document: {grok_metadata.get('document_information', {}).get('document_title', 'N/A')}")
    print(f"🏷️  Products in letter: {len(grok_metadata.get('products', []))}")
    
    # Step 2: Extract letter products
    print("\n📦 STEP 2: Extracting Letter Products")
    letter_products = extract_letter_products(grok_metadata)
    
    for i, product in enumerate(letter_products, 1):
        print(f"   {i}. {product.product_identifier} ({product.range_label})")
        print(f"      Product Line: {product.product_line}")
        print(f"      Technical Specs: {product.technical_specifications}")
    
    # Step 3: Simulate enhanced discovery results
    print("\n🔍 STEP 3: Enhanced Product Discovery Results")
    discovery_results = simulate_enhanced_discovery_results()
    
    # Analyze discovery results
    analysis = analyze_discovery_results(discovery_results)
    
    print(f"📊 Discovery Analysis:")
    print(f"   Total Candidates Found: {analysis['total_candidates']}")
    print(f"   Average Confidence: {analysis['average_confidence']:.3f}")
    print(f"   Strategy Breakdown:")
    for strategy, count in analysis['strategy_counts'].items():
        print(f"     - {strategy}: {count} candidates")
    
    print(f"   Confidence Distribution:")
    print(f"     - High (≥0.8): {analysis['confidence_distribution']['high']}")
    print(f"     - Medium (0.6-0.8): {analysis['confidence_distribution']['medium']}")
    print(f"     - Low (<0.6): {analysis['confidence_distribution']['low']}")
    
    # Step 4: Initialize intelligent matching service
    print("\n🤖 STEP 4: Initializing Intelligent Matching Service")
    
    try:
        matching_service = IntelligentProductMatchingService()
        print("✅ Intelligent matching service initialized")
    except Exception as e:
        print(f"❌ Failed to initialize matching service: {e}")
        return
    
    # Step 5: Perform intelligent matching
    print("\n🧠 STEP 5: Performing Intelligent Matching")
    print("Making Grok API calls to intelligently select best matches...")
    
    try:
        matching_results = matching_service.match_products_intelligently(
            letter_products, discovery_results
        )
        
        print(f"✅ Intelligent matching completed")
        print(f"📋 Products matched: {len(matching_results)}")
        
    except Exception as e:
        print(f"❌ Intelligent matching failed: {e}")
        return
    
    # Step 6: Display final results
    print("\n🎯 STEP 6: Final Intelligent Matching Results")
    print("="*80)
    
    total_processing_time = time.time() - start_time
    
    for i, result in enumerate(matching_results, 1):
        print(f"\n{i}. LETTER PRODUCT: {result.letter_product_id}")
        print(f"   🎯 MATCHED PRODUCT: {result.matched_product_identifier}")
        print(f"   📊 CONFIDENCE: {result.confidence:.3f}")
        print(f"   📈 DETAILED SCORES:")
        print(f"      Technical Match: {result.technical_match_score:.3f}")
        print(f"      Nomenclature Match: {result.nomenclature_match_score:.3f}")
        print(f"      Product Line Match: {result.product_line_match_score:.3f}")
        print(f"   🔄 ALTERNATIVE CANDIDATES:")
        for alt in result.alternative_candidates:
            print(f"      - {alt}")
        print(f"   📝 GROK REASONING:")
        print(f"      {result.reason[:200]}...")
        print(f"   ⏱️  Processing Time: {result.processing_time_ms:.2f}ms")
    
    # Step 7: Summary statistics
    print("\n📊 SUMMARY STATISTICS")
    print("="*80)
    
    if matching_results:
        avg_confidence = sum(r.confidence for r in matching_results) / len(matching_results)
        high_confidence_matches = len([r for r in matching_results if r.confidence >= 0.8])
        total_matching_time = sum(r.processing_time_ms for r in matching_results)
        
        print(f"📋 Products Processed: {len(matching_results)}")
        print(f"🎯 Average Confidence: {avg_confidence:.3f}")
        print(f"🔥 High Confidence Matches: {high_confidence_matches}")
        print(f"⏱️  Total Processing Time: {total_processing_time:.2f}s")
        print(f"🤖 Total Grok API Time: {total_matching_time:.2f}ms")
        
        # Calculate improvement metrics
        base_discovery_confidence = analysis['average_confidence']
        improvement = ((avg_confidence - base_discovery_confidence) / base_discovery_confidence) * 100
        
        print(f"\n🚀 IMPROVEMENT METRICS:")
        print(f"   Base Discovery Confidence: {base_discovery_confidence:.3f}")
        print(f"   Intelligent Matching Confidence: {avg_confidence:.3f}")
        print(f"   Improvement: {improvement:+.1f}%")
        
        # Demonstrate business value
        print(f"\n💼 BUSINESS VALUE:")
        print(f"   - Reduced false positives through AI reasoning")
        print(f"   - Technical specification validation")
        print(f"   - Product line compatibility checking")
        print(f"   - Nomenclature pattern analysis")
        print(f"   - Confidence-based decision making")
    
    # Step 8: Save comprehensive results
    print("\n💾 STEP 8: Saving Comprehensive Results")
    
    comprehensive_results = {
        "demo_metadata": {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "total_processing_time_seconds": total_processing_time,
            "pipeline_version": "1.0.0"
        },
        "letter_metadata": grok_metadata,
        "discovery_analysis": analysis,
        "discovery_results": {
            strategy: [
                {
                    "product_identifier": candidate.product_identifier,
                    "range_label": candidate.range_label,
                    "subrange_label": candidate.subrange_label,
                    "product_description": candidate.product_description,
                    "confidence_score": candidate.confidence_score,
                    "source": candidate.source
                }
                for candidate in candidates
            ]
            for strategy, candidates in discovery_results.items()
        },
        "intelligent_matching_results": [
            {
                "letter_product_id": result.letter_product_id,
                "matched_product_identifier": result.matched_product_identifier,
                "confidence": result.confidence,
                "reason": result.reason,
                "technical_match_score": result.technical_match_score,
                "nomenclature_match_score": result.nomenclature_match_score,
                "product_line_match_score": result.product_line_match_score,
                "alternative_candidates": result.alternative_candidates,
                "processing_time_ms": result.processing_time_ms
            }
            for result in matching_results
        ]
    }
    
    results_file = Path("scripts/sandbox/integrated_intelligent_discovery_results.json")
    with open(results_file, 'w') as f:
        json.dump(comprehensive_results, f, indent=2)
    
    print(f"✅ Comprehensive results saved to: {results_file}")
    
    print("\n" + "="*80)
    print("🎉 INTEGRATED INTELLIGENT DISCOVERY DEMONSTRATION COMPLETED")
    print("="*80)


if __name__ == "__main__":
    main() 