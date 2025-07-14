#!/usr/bin/env python3
"""
Database Schema Validation Script
Validates that database schema matches documentation and version alignment

Version: 2.1.0
Last Updated: 2025-01-27
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

import duckdb
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from se_letters.core.config import get_config


class DatabaseSchemaValidator:
    """Validates database schema against documentation"""
    
    def __init__(self):
        self.config = get_config()
        self.validation_results = {
            "version": "2.1.0",
            "timestamp": None,
            "databases": {},
            "overall_status": "PASS"
        }
        
        # Expected schema definitions from documentation
        self.expected_schemas = {
            "production": {
                "tables": ["letters", "letter_products", "processing_debug"],
                "sequences": [
                    "letters_id_seq", "products_id_seq", "debug_id_seq"
                ],
                "indexes": [
                    "idx_letters_source_path",
                    "idx_letters_document_name", 
                    "idx_products_letter_id",
                    "idx_debug_letter_id"
                ]
            },
            "staging": {
                "tables": ["raw_processing_staging", "document_staging"],
                "sequences": ["raw_staging_id_seq", "raw_debug_id_seq"],
                "indexes": [
                    "idx_raw_staging_source_path",
                    "idx_staging_source_path"
                ]
            },
            "document_metadata": {
                "tables": ["documents", "document_products", "business_information"],
                "sequences": [],
                "indexes": []
            }
        }
    
    def validate_all_databases(self) -> Dict[str, Any]:
        """Validate all database schemas"""
        logger.info("🔍 Starting database schema validation")
        
        databases = {
            "production": "data/letters.duckdb",
            "staging": "data/staging.duckdb", 
            "document_metadata": "data/document_metadata.duckdb"
        }
        
        for db_name, db_path in databases.items():
            logger.info(f"📊 Validating {db_name} database: {db_path}")
            self.validation_results["databases"][db_name] = self._validate_database(db_name, db_path)
        
        # Check overall status
        all_passed = all(
            result["status"] == "PASS" 
            for result in self.validation_results["databases"].values()
        )
        
        if not all_passed:
            self.validation_results["overall_status"] = "FAIL"
        
        return self.validation_results
    
    def _validate_database(self, db_name: str, db_path: str) -> Dict[str, Any]:
        """Validate a specific database"""
        result = {
            "database_name": db_name,
            "database_path": db_path,
            "status": "PASS",
            "errors": [],
            "warnings": [],
            "tables": {},
            "sequences": {},
            "indexes": {},
            "foreign_keys": {},
            "version_compatibility": "PASS"
        }
        
        try:
            # Check if database file exists
            if not Path(db_path).exists():
                result["status"] = "FAIL"
                result["errors"].append(f"Database file not found: {db_path}")
                return result
            
            with duckdb.connect(db_path) as conn:
                # Validate tables
                result["tables"] = self._validate_tables(conn, db_name)
                
                # Validate sequences
                result["sequences"] = self._validate_sequences(conn, db_name)
                
                # Validate indexes
                result["indexes"] = self._validate_indexes(conn, db_name)
                
                # Validate foreign keys
                result["foreign_keys"] = self._validate_foreign_keys(conn, db_name)
                
                # Validate version compatibility
                result["version_compatibility"] = self._validate_version_compatibility(conn, db_name)
                
                # Check for errors
                if any(result["tables"].get("errors", [])):
                    result["status"] = "FAIL"
                    result["errors"].extend(result["tables"]["errors"])
                
                if any(result["sequences"].get("errors", [])):
                    result["status"] = "FAIL"
                    result["errors"].extend(result["sequences"]["errors"])
                
                if any(result["indexes"].get("errors", [])):
                    result["warnings"].extend(result["indexes"]["errors"])
                
        except Exception as e:
            result["status"] = "FAIL"
            result["errors"].append(f"Database connection error: {str(e)}")
        
        return result
    
    def _validate_tables(self, conn, db_name: str) -> Dict[str, Any]:
        """Validate table structure"""
        result = {
            "expected": self.expected_schemas[db_name]["tables"],
            "actual": [],
            "missing": [],
            "extra": [],
            "errors": []
        }
        
        try:
            # Get actual tables
            tables = conn.execute("SHOW TABLES").fetchall()
            result["actual"] = [t[0] for t in tables]
            
            # Check for missing tables
            for expected_table in result["expected"]:
                if expected_table not in result["actual"]:
                    result["missing"].append(expected_table)
            
            # Check for extra tables
            for actual_table in result["actual"]:
                if actual_table not in result["expected"]:
                    result["extra"].append(actual_table)
            
            # Validate table schemas
            for table_name in result["actual"]:
                if table_name in result["expected"]:
                    table_schema = self._get_table_schema(conn, table_name)
                    schema_validation = self._validate_table_schema(table_name, table_schema, db_name)
                    if schema_validation["errors"]:
                        result["errors"].extend(schema_validation["errors"])
            
        except Exception as e:
            result["errors"].append(f"Table validation error: {str(e)}")
        
        return result
    
    def _validate_sequences(self, conn, db_name: str) -> Dict[str, Any]:
        """Validate sequences"""
        result = {
            "expected": self.expected_schemas[db_name]["sequences"],
            "actual": [],
            "missing": [],
            "extra": [],
            "errors": []
        }
        
        try:
            # DuckDB doesn't have SHOW SEQUENCES, check system tables
            try:
                sequences = conn.execute("""
                    SELECT sequence_name FROM information_schema.sequences
                """).fetchall()
                result["actual"] = [s[0] for s in sequences]
            except Exception:
                # Fallback: check if sequences exist by trying to use them
                result["actual"] = []
                for expected_seq in result["expected"]:
                    try:
                        conn.execute(f"SELECT nextval('{expected_seq}')")
                        result["actual"].append(expected_seq)
                    except Exception:
                        pass
            
            # Check for missing sequences
            for expected_seq in result["expected"]:
                if expected_seq not in result["actual"]:
                    result["missing"].append(expected_seq)
            
            # Check for extra sequences
            for actual_seq in result["actual"]:
                if actual_seq not in result["expected"]:
                    result["extra"].append(actual_seq)
            
        except Exception as e:
            result["errors"].append(f"Sequence validation error: {str(e)}")
        
        return result
    
    def _validate_indexes(self, conn, db_name: str) -> Dict[str, Any]:
        """Validate indexes"""
        result = {
            "expected": self.expected_schemas[db_name]["indexes"],
            "actual": [],
            "missing": [],
            "extra": [],
            "errors": []
        }
        
        try:
            # DuckDB doesn't have SHOW INDEXES, check system tables
            try:
                indexes = conn.execute("""
                    SELECT index_name FROM information_schema.indexes
                """).fetchall()
                result["actual"] = [i[0] for i in indexes]
            except Exception:
                # Fallback: skip index validation for now
                result["actual"] = []
            
            # Check for missing indexes
            for expected_idx in result["expected"]:
                if expected_idx not in result["actual"]:
                    result["missing"].append(expected_idx)
            
            # Check for extra indexes
            for actual_idx in result["actual"]:
                if actual_idx not in result["expected"]:
                    result["extra"].append(actual_idx)
            
        except Exception as e:
            result["errors"].append(f"Index validation error: {str(e)}")
        
        return result
    
    def _validate_foreign_keys(self, conn, db_name: str) -> Dict[str, Any]:
        """Validate foreign key constraints"""
        result = {
            "constraints": [],
            "errors": []
        }
        
        try:
            # Get foreign key constraints
            if db_name == "production":
                # Check letters -> letter_products relationship
                try:
                    conn.execute("""
                        INSERT INTO letter_products (letter_id, product_identifier) 
                        VALUES (999999, 'test')
                    """)
                    result["errors"].append("Foreign key constraint not enforced")
                except Exception:
                    # Expected behavior - foreign key constraint working
                    pass
                finally:
                    # Clean up test
                    conn.execute("DELETE FROM letter_products WHERE letter_id = 999999")
            
        except Exception as e:
            result["errors"].append(f"Foreign key validation error: {str(e)}")
        
        return result
    
    def _validate_version_compatibility(self, conn, db_name: str) -> str:
        """Validate version compatibility"""
        try:
            # Check for version-specific features
            if db_name == "production":
                # Check for processing_steps_json column (v2.1.0 feature)
                columns = conn.execute("DESCRIBE letters").fetchall()
                column_names = [c[0] for c in columns]
                
                if "processing_steps_json" not in column_names:
                    return "FAIL - Missing v2.1.0 features"
                
                # Check for proper sequences (DuckDB compatible)
                try:
                    conn.execute("SELECT nextval('letters_id_seq')")
                    return "PASS"
                except Exception:
                    return "FAIL - Missing auto-increment sequences"
            
            return "PASS"
            
        except Exception:
            return "FAIL - Version compatibility check failed"
    
    def _get_table_schema(self, conn, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema information"""
        try:
            schema = conn.execute(f"DESCRIBE {table_name}").fetchall()
            return [
                {
                    "column": row[0],
                    "type": row[1],
                    "null": row[2],
                    "key": row[3],
                    "default": row[4]
                }
                for row in schema
            ]
        except Exception:
            return []
    
    def _validate_table_schema(self, table_name: str, schema: List[Dict[str, Any]], db_name: str) -> Dict[str, Any]:
        """Validate table schema against expected structure"""
        result = {"errors": []}
        
        # Define expected columns for each table
        expected_columns = {
            "letters": [
                "id", "document_name", "document_type", "document_title",
                "source_file_path", "file_size", "processing_method",
                "processing_time_ms", "extraction_confidence", "created_at",
                "status", "raw_grok_json", "ocr_supplementary_json", "processing_steps_json"
            ],
            "letter_products": [
                "id", "letter_id", "product_identifier", "range_label",
                "subrange_label", "product_line", "product_description",
                "obsolescence_status", "end_of_service_date", "replacement_suggestions"
            ],
            "processing_debug": [
                "id", "letter_id", "processing_step", "step_timestamp",
                "step_duration_ms", "step_success", "step_details"
            ]
        }
        
        if table_name in expected_columns:
            actual_columns = [col["column"] for col in schema]
            expected_cols = expected_columns[table_name]
            
            for expected_col in expected_cols:
                if expected_col not in actual_columns:
                    result["errors"].append(f"Missing column: {expected_col}")
        
        return result
    
    def generate_report(self) -> str:
        """Generate validation report"""
        report = []
        report.append("# Database Schema Validation Report")
        report.append(f"**Version**: {self.validation_results['version']}")
        report.append(f"**Status**: {self.validation_results['overall_status']}")
        report.append("")
        
        for db_name, result in self.validation_results["databases"].items():
            report.append(f"## {db_name.title()} Database")
            report.append(f"**Status**: {result['status']}")
            report.append(f"**Path**: {result['database_path']}")
            report.append("")
            
            if result["errors"]:
                report.append("### ❌ Errors")
                for error in result["errors"]:
                    report.append(f"- {error}")
                report.append("")
            
            if result["warnings"]:
                report.append("### ⚠️ Warnings")
                for warning in result["warnings"]:
                    report.append(f"- {warning}")
                report.append("")
            
            # Tables
            if result["tables"].get("missing"):
                report.append("### Missing Tables")
                for table in result["tables"]["missing"]:
                    report.append(f"- {table}")
                report.append("")
            
            # Sequences
            if result["sequences"].get("missing"):
                report.append("### Missing Sequences")
                for seq in result["sequences"]["missing"]:
                    report.append(f"- {seq}")
                report.append("")
            
            # Indexes
            if result["indexes"].get("missing"):
                report.append("### Missing Indexes")
                for idx in result["indexes"]["missing"]:
                    report.append(f"- {idx}")
                report.append("")
            
            if result["version_compatibility"] != "PASS":
                report.append(f"### Version Compatibility: {result['version_compatibility']}")
                report.append("")
        
        return "\n".join(report)
    
    def save_results(self, output_path: str = "logs/database_validation_results.json"):
        """Save validation results to file"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.validation_results, f, indent=2, default=str)
        
        logger.info(f"Validation results saved to: {output_path}")


def main():
    """Main validation function"""
    logger.info("🔍 Starting Database Schema Validation")
    
    validator = DatabaseSchemaValidator()
    results = validator.validate_all_databases()
    
    # Generate and display report
    report = validator.generate_report()
    print(report)
    
    # Save results
    validator.save_results()
    
    # Exit with appropriate code
    if results["overall_status"] == "PASS":
        logger.info("✅ Database schema validation PASSED")
        sys.exit(0)
    else:
        logger.error("❌ Database schema validation FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main() 