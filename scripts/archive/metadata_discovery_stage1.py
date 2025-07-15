#!/usr/bin/env python3
"""
SE Letters - Metadata Discovery Stage 1 (Expanded)
===================================================

This script extracts comprehensive metadata from 40 random documents using
Grok's powerful analysis capabilities. It's designed to discover all possible
metadata fields that could exist across 300+ obsolescence letters.

Purpose: Pre-evaluation stage to understand field variability and commonalities
Output: 40 separate JSON files with comprehensive metadata extraction
"""

import json
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from se_letters.core.config import get_config
from se_letters.services.document_processor import DocumentProcessor
from se_letters.services.sota_grok_service import SOTAGrokService
from se_letters.utils.logger import get_logger

logger = get_logger(__name__)


class MetadataDiscoveryStage1:
    """Stage 1: Comprehensive metadata extraction from sample documents."""
    
    def __init__(self):
        """Initialize the metadata discovery system."""
        self.config = get_config()
        self.document_processor = DocumentProcessor(self.config)
        self.sota_grok_service = SOTAGrokService()
        self.output_dir = Path("data/output/metadata_discovery")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def get_sample_documents(self) -> List[Path]:
        """Get 40 random documents from all available directories."""
        # Start from the base directories and search recursively
        base_dirs = [
            Path("data/test/documents"),
            Path("data/input/letters"),
        ]
        
        # Collect all available documents
        available_docs = []
        for base_dir in base_dirs:
            if base_dir.exists():
                # Get all files recursively
                for pattern in ['*.pdf', '*.doc', '*.docx']:
                    available_docs.extend(base_dir.rglob(pattern))
                    
        # Filter out system files and templates
        available_docs = [
            f for f in available_docs 
            if f.is_file() 
            and not f.name.startswith('.')
            and not f.name.startswith('!')
            and not f.name.lower().startswith('template')
            and f.suffix.lower() in ['.pdf', '.doc', '.docx']
            and f.stat().st_size > 1000  # At least 1KB
        ]
        
        logger.info(f"Found {len(available_docs)} total documents")
        
        # Select 40 random documents (or all if less than 40)
        target_count = min(40, len(available_docs))
        if len(available_docs) < 40:
            logger.warning(
                f"Only {len(available_docs)} documents available, using all"
            )
            selected_docs = available_docs
        else:
            selected_docs = random.sample(available_docs, target_count)
        
        logger.info(f"Selected {len(selected_docs)} documents for metadata discovery")
        for i, doc in enumerate(selected_docs, 1):
            logger.info(f"  {i:2d}. {doc.name}")
        
        return selected_docs
    
    def create_comprehensive_extraction_prompt(self, document_name: str) -> str:
        """Create a comprehensive prompt for metadata extraction."""
        return f"""
You are an expert document analyst specializing in industrial obsolescence letters from Schneider Electric.

DOCUMENT: {document_name}

MISSION: Extract ALL POSSIBLE METADATA from this document. This is a discovery phase to understand what fields exist across 300+ obsolescence letters.

EXTRACTION REQUIREMENTS:
1. **DISCOVER EVERYTHING** - Don't assume what fields exist, find what's actually there
2. **COMPREHENSIVE COVERAGE** - Extract every piece of information that could be useful
3. **STRUCTURED OUTPUT** - Organize into logical categories
4. **NO ASSUMPTIONS** - Only extract what's explicitly stated in the document

METADATA CATEGORIES TO EXPLORE:

## Document Information
- Document type, title, reference number
- Creation date, effective date, revision
- Language, region, business unit
- Author, department, contact information
- Document status, classification level

## Product Information
- Product names, codes, references
- Product ranges, families, series
- Technical specifications (voltage, current, power, etc.)
- Commercial references, catalog numbers
- GTIN codes, part numbers
- Product descriptions, applications

## Business Information
- Business units, divisions, departments
- Geographic scope (countries, regions)
- Customer segments, market sectors
- Sales channels, distribution

## Lifecycle Information
- Obsolescence dates, end of life dates
- Last order dates, service end dates
- Production phases, commercialization status
- Replacement timelines, migration periods

## Technical Specifications
- Electrical characteristics
- Mechanical specifications
- Environmental ratings
- Certifications, standards compliance
- Installation requirements

## Commercial Information
- Pricing information
- Availability status
- Order codes, commercial references
- Distributor information

## Impact Analysis
- Affected customers, regions
- Business impact assessment
- Risk analysis
- Recommended actions

## Replacement Information
- Replacement products, alternatives
- Migration paths, upgrade options
- Compatibility information
- Technical differences

## Regulatory Information
- Compliance requirements
- Regulatory changes
- Standards updates
- Certification impacts

## Contact Information
- Support contacts
- Technical support
- Sales contacts
- Regional contacts

OUTPUT FORMAT:
Return a comprehensive JSON object with ALL discovered metadata organized by category. Include:
- Field names as keys
- Extracted values
- Confidence level for each extraction
- Source location in document (if identifiable)

IMPORTANT: This is a DISCOVERY phase - extract everything you can find, even if it seems minor. We want to understand the full scope of metadata across all obsolescence letters.

Extract ALL metadata from the document text provided.
"""

    def extract_comprehensive_metadata(self, document_path: Path) -> Dict[str, Any]:
        """Extract comprehensive metadata from a document."""
        logger.info(f"Processing document: {document_path.name}")
        
        try:
            # Process document to extract text
            document_obj = self.document_processor.process_document(document_path)
            
            if not document_obj or not hasattr(document_obj, 'text'):
                logger.error(f"Document processing failed: {document_path.name}")
                return {"error": "Document processing failed", "document": document_path.name}
            
            document_text = document_obj.text
            if not document_text or len(document_text.strip()) < 100:
                logger.error(f"Document text too short: {document_path.name}")
                return {"error": "Document text too short", "document": document_path.name}
            
            # Create comprehensive extraction prompt
            prompt = self.create_comprehensive_extraction_prompt(document_path.name)
            
            # Extract metadata using SOTA Grok service
            logger.info(f"Extracting metadata with SOTA Grok for {document_path.name}")
            
            # Use the SOTA Grok service for comprehensive extraction
            structured_data = self.sota_grok_service.extract_structured_data(
                document_text, 
                document_path.name
            )
            
            # Convert to dictionary format for metadata discovery
            metadata = {
                "document_information": {
                    "document_type": structured_data.document_metadata.document_type,
                    "language": structured_data.document_metadata.language,
                    "document_number": structured_data.document_metadata.document_number,
                    "total_products": structured_data.document_metadata.total_products,
                    "extraction_complexity": structured_data.document_metadata.extraction_complexity,
                    "has_tables": structured_data.document_metadata.has_tables,
                    "has_technical_specs": structured_data.document_metadata.has_technical_specs,
                },
                "product_information": [],
                "business_information": {
                    "affected_ranges": structured_data.document_metadata.affected_ranges,
                    "affected_countries": structured_data.document_metadata.affected_countries,
                    "customer_segments": structured_data.document_metadata.customer_segments,
                    "business_units": structured_data.document_metadata.business_units,
                    "business_impact": structured_data.document_metadata.business_impact,
                },
                "lifecycle_information": {
                    "key_dates": structured_data.document_metadata.key_dates,
                    "announcement_date": structured_data.document_metadata.announcement_date,
                    "effective_date": structured_data.document_metadata.effective_date,
                },
                "contact_information": {
                    "contact_details": structured_data.document_metadata.contact_information,
                    "migration_guidance": structured_data.document_metadata.migration_guidance,
                },
                "extraction_confidence": structured_data.extraction_confidence,
                "processing_timestamp": structured_data.processing_timestamp
            }
            
            # Add detailed product information
            for product in structured_data.products:
                product_info = {
                    "product_identifier": product.product_identifier,
                    "range_label": product.range_label,
                    "subrange_label": product.subrange_label,
                    "product_description": product.product_description,
                    "product_line": product.product_line,
                    "codification": product.codification,
                    "ref_commerciale": product.ref_commerciale,
                    "ref_technique": product.ref_technique,
                    "designation_constructeur": product.designation_constructeur,
                    "code_gtin": product.code_gtin,
                    "technical_specifications": {
                        "voltage_level": product.voltage_level,
                        "current_rating": product.current_rating,
                        "power_rating": product.power_rating,
                        "frequency": product.frequency,
                        "protection_class": product.protection_class,
                        "dimensions": product.dimensions,
                        "weight": product.weight,
                        "mounting_type": product.mounting_type,
                    },
                    "commercial_information": {
                        "part_number": product.part_number,
                        "catalog_number": product.catalog_number,
                        "obsolescence_status": product.obsolescence_status,
                        "last_order_date": product.last_order_date,
                        "end_of_service_date": product.end_of_service_date,
                    },
                    "replacement_information": {
                        "replacement_suggestions": product.replacement_suggestions,
                        "migration_path": product.migration_path,
                    },
                    "additional_specs": {
                        "technical_specs": product.technical_specs,
                        "certifications": product.certifications,
                        "applications": product.applications,
                    },
                    "quality_metrics": {
                        "confidence_score": product.confidence_score,
                        "extraction_method": product.extraction_method,
                    }
                }
                metadata["product_information"].append(product_info)
            
            # Add processing metadata
            metadata["_processing_info"] = {
                "document_name": document_path.name,
                "document_size": document_path.stat().st_size,
                "text_length": len(document_text),
                "extraction_timestamp": datetime.now().isoformat(),
                "model_used": "grok-3-mini",
                "extraction_method": "comprehensive_discovery"
            }
            
            logger.info(f"Successfully extracted metadata from {document_path.name}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {document_path.name}: {e}")
            return {
                "error": str(e),
                "document": document_path.name,
                "_processing_info": {
                    "extraction_timestamp": datetime.now().isoformat(),
                    "extraction_failed": True
                }
            }
    
    def save_metadata_output(self, metadata: Dict[str, Any], document_name: str) -> Path:
        """Save metadata to JSON file."""
        # Create safe filename
        safe_name = "".join(c for c in document_name if c.isalnum() or c in "._-")
        output_file = self.output_dir / f"stage1_metadata_{safe_name}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved metadata to: {output_file}")
        return output_file
    
    def run_discovery(self) -> List[Path]:
        """Run the complete Stage 1 metadata discovery."""
        logger.info("Starting Metadata Discovery Stage 1")
        
        # Get sample documents
        sample_docs = self.get_sample_documents()
        output_files = []
        
        # Process each document
        for doc_path in sample_docs:
            logger.info(f"Processing document {doc_path.name}")
            
            # Extract comprehensive metadata
            metadata = self.extract_comprehensive_metadata(doc_path)
            
            # Save to file
            output_file = self.save_metadata_output(metadata, doc_path.name)
            output_files.append(output_file)
            
            # Log summary
            if "error" not in metadata:
                field_count = self._count_fields(metadata)
                logger.info(f"Extracted {field_count} metadata fields from {doc_path.name}")
            else:
                logger.error(f"Failed to process {doc_path.name}: {metadata.get('error', 'Unknown error')}")
        
        # Create summary
        self._create_stage1_summary(output_files)
        
        logger.info(f"Stage 1 complete. Generated {len(output_files)} metadata files")
        return output_files
    
    def _count_fields(self, metadata: Dict[str, Any]) -> int:
        """Count the number of fields in metadata."""
        count = 0
        for key, value in metadata.items():
            if key.startswith("_"):
                continue
            if isinstance(value, dict):
                count += self._count_fields(value)
            elif isinstance(value, list):
                count += len(value)
            else:
                count += 1
        return count
    
    def _create_stage1_summary(self, output_files: List[Path]) -> None:
        """Create a summary of Stage 1 results."""
        summary = {
            "stage": "metadata_discovery_stage1",
            "timestamp": datetime.now().isoformat(),
            "processed_documents": len(output_files),
            "output_files": [str(f) for f in output_files],
            "next_step": "Run Stage 2 to unify metadata schemas"
        }
        
        summary_file = self.output_dir / "stage1_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created Stage 1 summary: {summary_file}")

def main():
    """Main execution function."""
    try:
        discovery = MetadataDiscoveryStage1()
        output_files = discovery.run_discovery()
        
        print("\n" + "="*60)
        print("METADATA DISCOVERY STAGE 1 COMPLETE")
        print("="*60)
        print(f"Processed {len(output_files)} documents")
        print(f"Output directory: {discovery.output_dir}")
        print("\nGenerated files:")
        for file in output_files:
            print(f"  - {file.name}")
        print(f"\nNext step: Run Stage 2 to unify metadata schemas")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Stage 1 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 