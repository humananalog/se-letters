#!/usr/bin/env python3
"""
End-to-End Analysis Test

Uses existing production scripts and analyzes the JSON outputs
to provide comprehensive analysis of product findings, matching, and database queries.
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from se_letters.services.postgresql_production_pipeline_service import PostgreSQLProductionPipelineService
from se_letters.utils.logger import get_logger

logger = get_logger(__name__)


def analyze_json_outputs(document_id: int) -> Dict[str, Any]:
    """Analyze JSON outputs for a specific document"""
    analysis = {
        "document_id": document_id,
        "grok_analysis": {},
        "product_matching_analysis": {},
        "database_analysis": {},
        "performance_metrics": {}
    }
    
    # Find the latest JSON output directory
    json_dir = Path(f"data/output/json_outputs/{document_id}")
    if not json_dir.exists():
        return analysis
    
    # Find the most recent timestamp directory
    timestamp_dirs = [d for d in json_dir.iterdir() if d.is_dir() and d.name != "latest"]
    if not timestamp_dirs:
        return analysis
    
    latest_dir = max(timestamp_dirs, key=lambda x: x.name)
    
    # Analyze Grok result
    grok_file = latest_dir / "grok_result.json"
    if grok_file.exists():
        with open(grok_file, 'r', encoding='utf-8') as f:
            grok_data = json.load(f)
        
        analysis["grok_analysis"] = {
            "ranges_found": len(grok_data.get("product_identification", {}).get("ranges", [])),
            "ranges": grok_data.get("product_identification", {}).get("ranges", []),
            "confidence": grok_data.get("extraction_metadata", {}).get("confidence", 0.0),
            "processing_time": grok_data.get("extraction_metadata", {}).get("processing_time", 0.0),
            "business_context": grok_data.get("business_context", {}),
            "commercial_lifecycle": grok_data.get("commercial_lifecycle", {})
        }
    
    # Analyze validation result
    validation_file = latest_dir / "validation_result.json"
    if validation_file.exists():
        with open(validation_file, 'r', encoding='utf-8') as f:
            validation_data = json.load(f)
        
        analysis["validation_analysis"] = {
            "is_compliant": validation_data.get("is_compliant", False),
            "confidence_score": validation_data.get("confidence_score", 0.0),
            "product_ranges": validation_data.get("product_ranges", []),
            "document_type": validation_data.get("document_type", ""),
            "document_title": validation_data.get("document_title", "")
        }
    
    # Analyze processing summary
    summary_file = latest_dir / "processing_summary.json"
    if summary_file.exists():
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)
        
        analysis["performance_metrics"] = {
            "total_processing_time": summary_data.get("total_processing_time_ms", 0) / 1000,
            "status": summary_data.get("status", ""),
            "success": summary_data.get("success", False)
        }
    
    # Analyze ingestion result
    ingestion_file = latest_dir / "ingestion_result.json"
    if ingestion_file.exists():
        with open(ingestion_file, 'r', encoding='utf-8') as f:
            ingestion_data = json.load(f)
        
        analysis["database_analysis"] = {
            "ingestion_success": ingestion_data.get("success", False),
            "letter_id": ingestion_data.get("letter_id"),
            "products_stored": ingestion_data.get("products_stored", 0),
            "matches_stored": ingestion_data.get("matches_stored", 0)
        }
    
    return analysis


def analyze_database_storage(document_id: int, pipeline_service) -> Dict[str, Any]:
    """Analyze database storage for a document"""
    analysis = {
        "letter_data": {},
        "products_stored": {},
        "matches_stored": {},
        "storage_summary": {}
    }
    
    try:
        import psycopg2
        import psycopg2.extras
        
        # Connect to database
        conn = psycopg2.connect(pipeline_service.connection_string)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            
            # Get letter data
            cur.execute("SELECT * FROM letters WHERE id = %s", [document_id])
            letter = cur.fetchone()
            
            if letter:
                analysis["letter_data"] = dict(letter)
                
                # Get products
                cur.execute("""
                    SELECT * FROM letter_products 
                    WHERE letter_id = %s 
                    ORDER BY confidence_score DESC
                """, [document_id])
                products = [dict(row) for row in cur.fetchall()]
                
                analysis["products_stored"] = {
                    "total_products": len(products),
                    "products": products
                }
                
                # Get matches
                cur.execute("""
                    SELECT lpm.*, lp.range_label, lp.product_identifier
                    FROM letter_product_matches lpm
                    JOIN letter_products lp ON lpm.letter_product_id = lp.id
                    WHERE lpm.letter_id = %s
                    ORDER BY lpm.match_confidence DESC
                """, [document_id])
                matches = [dict(row) for row in cur.fetchall()]
                
                analysis["matches_stored"] = {
                    "total_matches": len(matches),
                    "matches": matches
                }
                
                # Database statistics
                analysis["storage_summary"] = {
                    "letter_stored": True,
                    "products_stored": len(products),
                    "matches_stored": len(matches),
                    "storage_success": len(products) > 0
                }
            
    except Exception as e:
        analysis["storage_summary"] = {
            "error": str(e),
            "storage_success": False
        }
    
    return analysis


def run_end_to_end_analysis():
    """Run comprehensive end-to-end analysis using production scripts"""
    
    logger.info("🚀 Starting End-to-End Analysis using Production Scripts")
    logger.info(f"📅 Analysis started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize pipeline service
    pipeline_service = PostgreSQLProductionPipelineService()
    
    # Test documents
    test_documents = [
        Path("data/test/documents/PIX2B_Phase_out_Letter.pdf"),
        Path("data/test/documents/SEPAM2040_PWP_Notice.pdf"),
        Path("data/test/documents/Galaxy_6000_End_of_Life.doc")
    ]
    
    overall_analysis = {
        "analysis_timestamp": datetime.now().isoformat(),
        "test_summary": {
            "total_documents": len(test_documents),
            "successful_processing": 0,
            "failed_processing": 0,
            "total_products_found": 0,
            "total_matches_found": 0
        },
        "document_analyses": []
    }
    
    # Process each document using production pipeline
    for doc_path in test_documents:
        if not doc_path.exists():
            logger.warning(f"⚠️ Document not found: {doc_path}")
            continue
        
        logger.info(f"🔍 Processing: {doc_path.name}")
        
        doc_analysis = {
            "document_name": doc_path.name,
            "document_path": str(doc_path),
            "processing_start": datetime.now().isoformat(),
            "json_analysis": {},
            "database_analysis": {},
            "errors": []
        }
        
        try:
            # Use production pipeline to process document
            start_time = time.time()
            result = pipeline_service.process_document(doc_path, force_reprocess=True)
            processing_time = time.time() - start_time
            
            doc_analysis["processing_success"] = result.success
            doc_analysis["processing_time"] = processing_time
            doc_analysis["confidence_score"] = result.confidence_score
            doc_analysis["document_id"] = result.document_id
            
            if result.success:
                overall_analysis["test_summary"]["successful_processing"] += 1
                
                # Analyze JSON outputs
                if result.document_id:
                    json_analysis = analyze_json_outputs(result.document_id)
                    doc_analysis["json_analysis"] = json_analysis
                    
                    # Count products found
                    ranges_found = json_analysis["grok_analysis"].get("ranges_found", 0)
                    overall_analysis["test_summary"]["total_products_found"] += ranges_found
                    
                    # Analyze database storage
                    db_analysis = analyze_database_storage(result.document_id, pipeline_service)
                    doc_analysis["database_analysis"] = db_analysis
                    
                    # Count matches found
                    matches_stored = db_analysis["storage_summary"].get("matches_stored", 0)
                    overall_analysis["test_summary"]["total_matches_found"] += matches_stored
                    
                    logger.info(f"✅ {doc_path.name}: {ranges_found} ranges, {matches_stored} matches")
                
            else:
                overall_analysis["test_summary"]["failed_processing"] += 1
                doc_analysis["errors"].append(result.error_message)
                logger.error(f"❌ {doc_path.name}: {result.error_message}")
            
        except Exception as e:
            overall_analysis["test_summary"]["failed_processing"] += 1
            doc_analysis["errors"].append(str(e))
            logger.error(f"❌ {doc_path.name}: Exception - {e}")
        
        doc_analysis["processing_end"] = datetime.now().isoformat()
        overall_analysis["document_analyses"].append(doc_analysis)
    
    # Save comprehensive analysis
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"data/output/json_outputs/end_to_end_analysis_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    analysis_file = output_dir / "comprehensive_analysis.json"
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(overall_analysis, f, indent=2, ensure_ascii=False, default=str)
    
    # Print summary
    logger.info(f"📊 Analysis complete: {analysis_file}")
    logger.info(f"📈 Summary: {overall_analysis['test_summary']['successful_processing']}/{len(test_documents)} documents processed")
    logger.info(f"📦 Products found: {overall_analysis['test_summary']['total_products_found']}")
    logger.info(f"🔗 Matches found: {overall_analysis['test_summary']['total_matches_found']}")
    
    # Validate results
    assert overall_analysis["test_summary"]["successful_processing"] > 0, "No documents processed successfully"
    assert overall_analysis["test_summary"]["total_products_found"] > 0, "No products found"
    
    logger.info("✅ End-to-end analysis completed successfully!")
    return overall_analysis


if __name__ == "__main__":
    run_end_to_end_analysis() 