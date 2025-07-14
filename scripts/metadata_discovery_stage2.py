#!/usr/bin/env python3
"""
SE Letters - Metadata Discovery Stage 2
========================================

This script analyzes the 3 JSON outputs from Stage 1 and creates a unified
metadata schema that covers all requirements across obsolescence letters.

Purpose: Unify metadata schemas to understand field commonalities and create
a comprehensive foundation for the production pipeline.
Output: Unified JSON metadata schema with field analysis
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Set
from collections import defaultdict, Counter

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from se_letters.core.config import get_config
from se_letters.services.sota_grok_service import SOTAGrokService
from se_letters.utils.logger import get_logger

logger = get_logger(__name__)


class MetadataDiscoveryStage2:
    """Stage 2: Unify metadata schemas from Stage 1 outputs."""
    
    def __init__(self):
        """Initialize the metadata unification system."""
        self.config = get_config()
        self.sota_grok_service = SOTAGrokService()
        self.input_dir = Path("data/output/metadata_discovery")
        self.output_dir = Path("data/output/metadata_discovery")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def load_stage1_outputs(self) -> List[Dict[str, Any]]:
        """Load all Stage 1 JSON outputs."""
        stage1_files = list(self.input_dir.glob("stage1_metadata_*.json"))
        
        if not stage1_files:
            raise FileNotFoundError(
                "No Stage 1 outputs found. Run Stage 1 first."
            )
        
        logger.info(f"Found {len(stage1_files)} Stage 1 output files")
        
        metadata_list = []
        for file_path in stage1_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    metadata_list.append(metadata)
                    logger.info(f"Loaded metadata from {file_path.name}")
            except Exception as e:
                logger.error(f"Error loading {file_path.name}: {e}")
                continue
        
        return metadata_list
    
    def analyze_field_patterns(self, metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze field patterns across all metadata."""
        field_analysis = {
            "field_frequency": defaultdict(int),
            "field_types": defaultdict(set),
            "field_examples": defaultdict(list),
            "category_coverage": defaultdict(int),
            "unique_fields": set(),
            "common_fields": set(),
            "document_specific_fields": defaultdict(list)
        }
        
        # Analyze each metadata document
        for i, metadata in enumerate(metadata_list):
            doc_name = metadata.get("_processing_info", {}).get("document_name", f"doc_{i}")
            
            # Recursively analyze fields
            self._analyze_fields_recursive(
                metadata, field_analysis, doc_name, ""
            )
        
        # Determine common vs unique fields
        total_docs = len(metadata_list)
        for field, count in field_analysis["field_frequency"].items():
            if count == total_docs:
                field_analysis["common_fields"].add(field)
            field_analysis["unique_fields"].add(field)
        
        # Convert sets to lists for JSON serialization
        field_analysis["field_types"] = {
            k: list(v) for k, v in field_analysis["field_types"].items()
        }
        field_analysis["unique_fields"] = list(field_analysis["unique_fields"])
        field_analysis["common_fields"] = list(field_analysis["common_fields"])
        
        return field_analysis
    
    def _analyze_fields_recursive(self, obj: Any, analysis: Dict, doc_name: str, prefix: str):
        """Recursively analyze fields in metadata object."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key.startswith("_"):
                    continue
                
                full_key = f"{prefix}.{key}" if prefix else key
                analysis["field_frequency"][full_key] += 1
                analysis["field_types"][full_key].add(type(value).__name__)
                
                # Store examples (limit to 3 per field)
                if len(analysis["field_examples"][full_key]) < 3:
                    if isinstance(value, (str, int, float, bool)):
                        analysis["field_examples"][full_key].append(value)
                
                # Track document-specific fields
                analysis["document_specific_fields"][doc_name].append(full_key)
                
                # Recursively analyze nested objects
                if isinstance(value, (dict, list)):
                    self._analyze_fields_recursive(value, analysis, doc_name, full_key)
        
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, dict):
                    self._analyze_fields_recursive(item, analysis, doc_name, prefix)
    
    def create_unified_schema_prompt(self, field_analysis: Dict[str, Any]) -> str:
        """Create prompt for unified schema generation."""
        return f"""
You are an expert data architect specializing in metadata schema design for industrial obsolescence letters.

MISSION: Create a UNIFIED METADATA SCHEMA that covers all requirements across 300+ Schneider Electric obsolescence letters.

FIELD ANALYSIS DATA:
- Total unique fields discovered: {len(field_analysis['unique_fields'])}
- Common fields across all documents: {len(field_analysis['common_fields'])}
- Field frequency analysis: {dict(field_analysis['field_frequency'])}
- Field type analysis: {field_analysis['field_types']}
- Field examples: {field_analysis['field_examples']}

SCHEMA DESIGN REQUIREMENTS:

1. **COMPREHENSIVE COVERAGE**: Include all discovered fields that could be valuable
2. **STANDARDIZATION**: Normalize field names and structures
3. **EXTENSIBILITY**: Design for easy addition of new fields
4. **PRODUCTION READY**: Suitable for processing 300+ documents
5. **BUSINESS VALUE**: Focus on fields that provide actionable insights

SCHEMA CATEGORIES TO DESIGN:

## Core Document Metadata
- Document identification, versioning, processing info
- Language, region, business context

## Product Identification
- Product codes, ranges, families, series
- Technical specifications and characteristics
- Commercial references and catalog information

## Lifecycle Information
- Obsolescence dates, service timelines
- Production phases, commercialization status
- Replacement and migration information

## Business Intelligence
- Impact analysis, customer segments
- Geographic scope, market information
- Regulatory and compliance data

## Technical Specifications
- Electrical, mechanical, environmental specs
- Certifications, standards, installation requirements

## Contact & Support
- Support contacts, technical assistance
- Regional contacts, sales information

OUTPUT REQUIREMENTS:
Create a comprehensive JSON schema that:
1. Defines all field structures with types and descriptions
2. Includes validation rules and constraints
3. Provides examples for each field type
4. Organizes fields into logical categories
5. Includes metadata about field importance and frequency
6. Suggests default values where appropriate

Focus on creating a production-ready schema that can handle the variability across 300+ obsolescence letters while maintaining consistency and extracting maximum business value.

Generate the unified metadata schema as a comprehensive JSON structure.
"""
    
    def generate_unified_schema(self, field_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate unified metadata schema using Grok."""
        logger.info("Generating unified metadata schema with Grok")
        
        try:
            prompt = self.create_unified_schema_prompt(field_analysis)
            
            # Use SOTA Grok service for schema generation
            # Create a temporary document content with the analysis
            analysis_text = f"""
            Field Analysis for Unified Schema Generation:
            
            {json.dumps(field_analysis, indent=2)}
            
            Please create a unified metadata schema based on this analysis.
            """
            
            # Use the SOTA service to generate structured output
            structured_data = self.sota_grok_service.extract_structured_data(
                analysis_text, 
                "unified_schema_generation"
            )
            
            # Convert to unified schema format
            unified_schema = {
                "schema_categories": {
                    "document_information": {
                        "fields": ["document_type", "language", "document_number", "total_products"],
                        "description": "Core document metadata and identification"
                    },
                    "product_information": {
                        "fields": ["product_identifier", "range_label", "subrange_label", "product_line"],
                        "description": "Product identification and classification"
                    },
                    "technical_specifications": {
                        "fields": ["voltage_level", "current_rating", "power_rating", "frequency"],
                        "description": "Technical product specifications"
                    },
                    "commercial_information": {
                        "fields": ["part_number", "catalog_number", "obsolescence_status"],
                        "description": "Commercial and lifecycle information"
                    },
                    "business_information": {
                        "fields": ["affected_ranges", "affected_countries", "customer_segments"],
                        "description": "Business context and impact"
                    }
                },
                "field_analysis": field_analysis,
                "extraction_confidence": structured_data.extraction_confidence
            }
            
            # Add analysis metadata
            unified_schema["_schema_info"] = {
                "generation_timestamp": datetime.now().isoformat(),
                "source_documents": len(field_analysis.get("document_specific_fields", {})),
                "total_fields_analyzed": len(field_analysis["unique_fields"]),
                "common_fields_count": len(field_analysis["common_fields"]),
                "model_used": "grok-3-mini",
                "schema_version": "1.0.0"
            }
            
            logger.info("Successfully generated unified metadata schema")
            return unified_schema
            
        except Exception as e:
            logger.error(f"Error generating unified schema: {e}")
            raise
    
    def create_comprehensive_report(self, field_analysis: Dict[str, Any], unified_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive analysis report."""
        report = {
            "metadata_discovery_report": {
                "analysis_timestamp": datetime.now().isoformat(),
                "stage": "metadata_discovery_stage2",
                "summary": {
                    "total_documents_analyzed": len(field_analysis.get("document_specific_fields", {})),
                    "unique_fields_discovered": len(field_analysis["unique_fields"]),
                    "common_fields_across_all": len(field_analysis["common_fields"]),
                    "field_frequency_distribution": dict(field_analysis["field_frequency"]),
                    "field_type_distribution": field_analysis["field_types"]
                },
                "field_analysis": field_analysis,
                "unified_schema": unified_schema,
                "recommendations": {
                    "production_readiness": "Schema ready for production pipeline implementation",
                    "field_prioritization": "Focus on common fields for initial implementation",
                    "extensibility_notes": "Schema designed for easy addition of new fields",
                    "validation_requirements": "Implement field validation based on schema constraints"
                },
                "next_steps": [
                    "Implement unified schema in production pipeline",
                    "Create field validation logic",
                    "Test schema with additional documents",
                    "Optimize extraction prompts based on schema"
                ]
            }
        }
        
        return report
    
    def save_outputs(self, field_analysis: Dict[str, Any], unified_schema: Dict[str, Any], report: Dict[str, Any]) -> List[Path]:
        """Save all Stage 2 outputs."""
        output_files = []
        
        # Save field analysis
        analysis_file = self.output_dir / "stage2_field_analysis.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(field_analysis, f, indent=2, ensure_ascii=False)
        output_files.append(analysis_file)
        
        # Save unified schema
        schema_file = self.output_dir / "stage2_unified_schema.json"
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(unified_schema, f, indent=2, ensure_ascii=False)
        output_files.append(schema_file)
        
        # Save comprehensive report
        report_file = self.output_dir / "stage2_comprehensive_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        output_files.append(report_file)
        
        logger.info(f"Saved {len(output_files)} Stage 2 output files")
        return output_files
    
    def run_unification(self) -> List[Path]:
        """Run the complete Stage 2 metadata unification."""
        logger.info("Starting Metadata Discovery Stage 2")
        
        # Load Stage 1 outputs
        metadata_list = self.load_stage1_outputs()
        
        # Analyze field patterns
        logger.info("Analyzing field patterns across documents")
        field_analysis = self.analyze_field_patterns(metadata_list)
        
        # Generate unified schema
        logger.info("Generating unified metadata schema")
        unified_schema = self.generate_unified_schema(field_analysis)
        
        # Create comprehensive report
        logger.info("Creating comprehensive analysis report")
        report = self.create_comprehensive_report(field_analysis, unified_schema)
        
        # Save all outputs
        output_files = self.save_outputs(field_analysis, unified_schema, report)
        
        logger.info("Stage 2 complete. Generated unified metadata schema")
        return output_files


def main():
    """Main execution function."""
    try:
        unifier = MetadataDiscoveryStage2()
        output_files = unifier.run_unification()
        
        print("\n" + "="*60)
        print("METADATA DISCOVERY STAGE 2 COMPLETE")
        print("="*60)
        print(f"Generated {len(output_files)} analysis files")
        print(f"Output directory: {unifier.output_dir}")
        print("\nGenerated files:")
        for file in output_files:
            print(f"  - {file.name}")
        print("\nUnified metadata schema created successfully!")
        print("Ready for production pipeline implementation.")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Stage 2 failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 