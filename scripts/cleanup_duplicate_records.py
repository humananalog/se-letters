#!/usr/bin/env python3
"""
Database Cleanup Script - Remove Duplicate Records
Removes duplicate document records keeping the most recent successful one

Version: 1.0.0
Last Updated: 2025-07-14
"""

import sys
import duckdb
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def cleanup_duplicate_records(db_path: str = "data/letters.duckdb"):
    """Clean up duplicate document records"""
    
    logger.info("🧹 Starting duplicate record cleanup")
    
    try:
        with duckdb.connect(db_path) as conn:
            # Find duplicate documents (same document_name)
            duplicates = conn.execute("""
                SELECT document_name, COUNT(*) as count, 
                       array_agg(id ORDER BY created_at DESC) as ids,
                       array_agg(status ORDER BY created_at DESC) as statuses
                FROM letters 
                GROUP BY document_name 
                HAVING COUNT(*) > 1
            """).fetchall()
            
            if not duplicates:
                logger.info("✅ No duplicate records found")
                return
            
            logger.info(f"🔍 Found {len(duplicates)} documents with duplicates")
            
            for doc_name, count, ids, statuses in duplicates:
                logger.info(f"📄 Document: {doc_name} ({count} records)")
                
                # Keep the most recent record, delete the rest
                ids_to_keep = [ids[0]]  # Most recent (first after ORDER BY created_at DESC)
                ids_to_delete = ids[1:]  # Older records
                
                logger.info(f"  ✅ Keeping: {ids_to_keep} (status: {statuses[0]})")
                logger.info(f"  🗑️ Deleting: {ids_to_delete}")
                
                # Delete older records and their related data
                for old_id in ids_to_delete:
                    conn.execute("DELETE FROM processing_debug WHERE letter_id = ?", [old_id])
                    conn.execute("DELETE FROM letter_products WHERE letter_id = ?", [old_id])
                    conn.execute("DELETE FROM letters WHERE id = ?", [old_id])
                    logger.info(f"    🗑️ Deleted record ID: {old_id}")
            
            logger.success("✅ Duplicate cleanup completed successfully")
            
            # Show final state
            final_count = conn.execute("SELECT COUNT(*) FROM letters").fetchone()[0]
            logger.info(f"📊 Total letters after cleanup: {final_count}")
            
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")
        raise

if __name__ == "__main__":
    cleanup_duplicate_records() 