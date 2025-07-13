#!/usr/bin/env python3
"""
Enhanced Document Processor with Database Insights
Leverages comprehensive DuckDB analysis for improved semantic search and range extraction
"""

import sys
import time
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple, Optional
from collections import defaultdict, Counter
from dataclasses import dataclass
import random

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

import duckdb
import pandas as pd


@dataclass
class DatabaseInsights:
    """Database insights from comprehensive analysis"""
    
    # Top product ranges (from analysis)
    top_ranges: List[str]
    
    # Product identifier patterns
    product_prefixes: List[str]
    
    # Brand hierarchy
    brand_hierarchy: Dict[str, int]
    
    # Business unit mapping
    business_units: List[str]
    
    # Commercial status patterns
    commercial_statuses: List[str]
    
    # Device type classifications
    device_types: List[str]
    
    # Common description words
    description_keywords: List[str]


class DatabaseIntelligentExtractor:
    """Intelligent extractor using database insights"""
    
    def __init__(self, db_path: str = "data/IBcatalogue.duckdb"):
        self.db_path = db_path
        self.conn = None
        self.insights = None
        self._load_database_insights()
    
    def _load_database_insights(self):
        """Load insights from database analysis"""
        print("🧠 Loading database insights...")
        
        self.conn = duckdb.connect(self.db_path)
        
        # Get top ranges (from analysis results)
        top_ranges = [
            "Accutech", "Flow Measurement", "SCADAPack 100, 300, 32", "HDW3",
            "Trio Licensed Radios", "SCADAPack 300E, ES", "TeSys D", 
            "ComPacT NSX 2021-China", "PowerPact H-Frame Molded Case Circuit Breakers",
            "PowerPact P-Frame", "Compact NSX <630", "8903L/LX Lighting Contactors",
            "Power-Dry II Transformers", "EasyPact MVS", "QO(B) Circuit Breakers",
            "HDM3", "Class 8903 Type S Lighting Contactors", "WATSG", "I-Line® Busway"
        ]
        
        # Get product prefixes (from analysis)
        product_prefixes = [
            "TBU", "MRF", "LC1", "ATV", "HDW", "890", "HDB", "LV4", "HDM", "LC2",
            "MVS", "A9F", "PFX", "A9N", "EOC"
        ]
        
        # Get brand hierarchy
        brand_query = """
            SELECT BRAND_LABEL, COUNT(*) as count
            FROM products 
            WHERE BRAND_LABEL IS NOT NULL
            GROUP BY BRAND_LABEL 
            ORDER BY count DESC
            LIMIT 20
        """
        brands = self.conn.execute(brand_query).fetchall()
        brand_hierarchy = {brand: count for brand, count in brands}
        
        # Get business units
        bu_query = """
            SELECT DISTINCT BU_LABEL
            FROM products 
            WHERE BU_LABEL IS NOT NULL
            ORDER BY BU_LABEL
        """
        business_units = [bu[0] for bu in self.conn.execute(bu_query).fetchall()]
        
        # Get commercial statuses
        status_query = """
            SELECT DISTINCT COMMERCIAL_STATUS
            FROM products 
            WHERE COMMERCIAL_STATUS IS NOT NULL
            ORDER BY COMMERCIAL_STATUS
        """
        commercial_statuses = [status[0] for status in self.conn.execute(status_query).fetchall()]
        
        # Get device types
        device_query = """
            SELECT DISTINCT DEVICETYPE_LABEL
            FROM products 
            WHERE DEVICETYPE_LABEL IS NOT NULL
            ORDER BY DEVICETYPE_LABEL
        """
        device_types = [device[0] for device in self.conn.execute(device_query).fetchall()]
        
        # Common description keywords (from analysis)
        description_keywords = [
            "TYPE", "NEX", "POWER", "SUPPLY", "24V", "AIR", "CONDENSER", "COOLED", 
            "CHILLER", "VRQ3NS2", "CONTACTOR", "CIRCUIT", "BREAKER", "SWITCH",
            "RELAY", "MOTOR", "DRIVE", "PROTECTION", "CONTROL", "AUTOMATION"
        ]
        
        self.insights = DatabaseInsights(
            top_ranges=top_ranges,
            product_prefixes=product_prefixes,
            brand_hierarchy=brand_hierarchy,
            business_units=business_units,
            commercial_statuses=commercial_statuses,
            device_types=device_types,
            description_keywords=description_keywords
        )
        
        print(f"✅ Loaded insights: {len(top_ranges)} ranges, {len(product_prefixes)} prefixes, {len(brands)} brands")
    
    def extract_ranges_with_database_intelligence(self, text: str, document_name: str) -> List[str]:
        """Extract ranges using database intelligence"""
        extracted_ranges = set()
        text_upper = text.upper()
        
        # 1. Direct range matching (highest priority)
        for range_name in self.insights.top_ranges:
            range_upper = range_name.upper()
            
            # Exact match
            if range_upper in text_upper:
                extracted_ranges.add(range_name)
                continue
            
            # Partial match for compound names
            range_parts = range_upper.split()
            if len(range_parts) > 1:
                # Check if all parts are present
                if all(part in text_upper for part in range_parts):
                    extracted_ranges.add(range_name)
                    continue
                
                # Check if main part is present
                main_part = range_parts[0]
                if len(main_part) > 3 and main_part in text_upper:
                    extracted_ranges.add(range_name)
        
        # 2. Product identifier pattern matching
        for prefix in self.insights.product_prefixes:
            # Look for product codes starting with this prefix
            pattern = rf'\b{re.escape(prefix)}\w*\b'
            matches = re.findall(pattern, text_upper)
            if matches:
                # Try to find the range for this prefix
                range_query = f"""
                    SELECT DISTINCT RANGE_LABEL
                    FROM products 
                    WHERE UPPER(PRODUCT_IDENTIFIER) LIKE '{prefix}%'
                    AND RANGE_LABEL IS NOT NULL
                    LIMIT 5
                """
                try:
                    ranges = self.conn.execute(range_query).fetchall()
                    for (range_name,) in ranges:
                        if range_name:
                            extracted_ranges.add(range_name)
                except:
                    pass
        
        # 3. Brand and device type context analysis
        detected_brands = []
        for brand in self.insights.brand_hierarchy.keys():
            if brand.upper() in text_upper:
                detected_brands.append(brand)
        
        detected_device_types = []
        for device_type in self.insights.device_types:
            # Check for key words from device type
            device_words = device_type.upper().split()
            key_words = [word for word in device_words if len(word) > 4]
            if any(word in text_upper for word in key_words):
                detected_device_types.append(device_type)
        
        # 4. Context-based range discovery
        if detected_brands or detected_device_types:
            context_query = "SELECT DISTINCT RANGE_LABEL FROM products WHERE 1=1"
            params = []
            
            if detected_brands:
                brand_conditions = " OR ".join(["UPPER(BRAND_LABEL) = UPPER(?)" for _ in detected_brands])
                context_query += f" AND ({brand_conditions})"
                params.extend(detected_brands)
            
            if detected_device_types:
                device_conditions = " OR ".join(["UPPER(DEVICETYPE_LABEL) LIKE UPPER(?)" for _ in detected_device_types])
                context_query += f" AND ({device_conditions})"
                params.extend([f"%{dt}%" for dt in detected_device_types])
            
            context_query += " AND RANGE_LABEL IS NOT NULL LIMIT 10"
            
            try:
                context_ranges = self.conn.execute(context_query, params).fetchall()
                for (range_name,) in context_ranges:
                    if range_name and any(word in text_upper for word in range_name.upper().split()):
                        extracted_ranges.add(range_name)
            except Exception as e:
                print(f"Context query error: {e}")
        
        # 5. Filename-based range extraction
        filename_upper = document_name.upper()
        for range_name in self.insights.top_ranges:
            range_parts = range_name.upper().split()
            main_part = range_parts[0]
            
            if len(main_part) > 2 and main_part in filename_upper:
                extracted_ranges.add(range_name)
        
        # 6. Fuzzy matching for common patterns
        common_patterns = {
            'PIX': ['PIX', 'PIX-DC', 'PIX 36', 'PIX Compact'],
            'TESYS': ['TeSys D', 'TeSys F', 'TeSys U'],
            'COMPACT': ['Compact NSX <630', 'ComPacT NSX 2021-China'],
            'POWERPACT': ['PowerPact H-Frame Molded Case Circuit Breakers', 'PowerPact P-Frame'],
            'SCADAPACK': ['SCADAPack 100, 300, 32', 'SCADAPack 300E, ES'],
            'MASTERPACT': ['Masterpact MT', 'Masterpact MTZ'],
            'EASYPACT': ['EasyPact MVS', 'EasyPact CVS'],
        }
        
        for pattern, ranges in common_patterns.items():
            if pattern in text_upper or pattern in filename_upper:
                for range_name in ranges:
                    # Verify this range exists in database
                    verify_query = "SELECT COUNT(*) FROM products WHERE UPPER(RANGE_LABEL) = UPPER(?)"
                    try:
                        count = self.conn.execute(verify_query, [range_name]).fetchone()[0]
                        if count > 0:
                            extracted_ranges.add(range_name)
                    except:
                        pass
        
        return list(extracted_ranges)
    
    def get_range_context_information(self, ranges: List[str]) -> Dict[str, Any]:
        """Get context information for extracted ranges"""
        if not ranges:
            return {}
        
        context_info = {}
        
        for range_name in ranges:
            try:
                # Get range statistics
                stats_query = """
                    SELECT 
                        COUNT(*) as product_count,
                        COUNT(DISTINCT BRAND_LABEL) as brand_count,
                        COUNT(DISTINCT BU_LABEL) as bu_count,
                        COUNT(DISTINCT COMMERCIAL_STATUS) as status_count,
                        COUNT(DISTINCT DEVICETYPE_LABEL) as device_count
                    FROM products 
                    WHERE UPPER(RANGE_LABEL) = UPPER(?)
                """
                stats = self.conn.execute(stats_query, [range_name]).fetchone()
                
                # Get top brands for this range
                brand_query = """
                    SELECT BRAND_LABEL, COUNT(*) as count
                    FROM products 
                    WHERE UPPER(RANGE_LABEL) = UPPER(?)
                    AND BRAND_LABEL IS NOT NULL
                    GROUP BY BRAND_LABEL
                    ORDER BY count DESC
                    LIMIT 3
                """
                brands = self.conn.execute(brand_query, [range_name]).fetchall()
                
                # Get commercial status distribution
                status_query = """
                    SELECT COMMERCIAL_STATUS, COUNT(*) as count
                    FROM products 
                    WHERE UPPER(RANGE_LABEL) = UPPER(?)
                    AND COMMERCIAL_STATUS IS NOT NULL
                    GROUP BY COMMERCIAL_STATUS
                    ORDER BY count DESC
                    LIMIT 5
                """
                statuses = self.conn.execute(status_query, [range_name]).fetchall()
                
                context_info[range_name] = {
                    'product_count': stats[0] if stats else 0,
                    'brand_count': stats[1] if stats else 0,
                    'bu_count': stats[2] if stats else 0,
                    'status_count': stats[3] if stats else 0,
                    'device_count': stats[4] if stats else 0,
                    'top_brands': [{'brand': brand, 'count': count} for brand, count in brands],
                    'status_distribution': [{'status': status, 'count': count} for status, count in statuses]
                }
                
            except Exception as e:
                print(f"Error getting context for {range_name}: {e}")
                context_info[range_name] = {'error': str(e)}
        
        return context_info
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


class EnhancedDocumentProcessor:
    """Enhanced document processor with database intelligence"""
    
    def __init__(self):
        self.db_extractor = DatabaseIntelligentExtractor()
        
    def process_document(self, file_path: Path) -> Dict[str, Any]:
        """Process document with enhanced intelligence"""
        
        print(f"\n📄 Processing: {file_path.name}")
        print("-" * 60)
        
        # Basic document processing (simplified for demo)
        try:
            if file_path.suffix.lower() == '.pdf':
                text = self._extract_pdf_text(file_path)
            elif file_path.suffix.lower() in ['.doc', '.docx']:
                text = self._extract_doc_text(file_path)
            else:
                text = file_path.read_text(encoding='utf-8', errors='ignore')
                
            if not text or len(text.strip()) < 10:
                text = f"Fallback content for {file_path.name}"
                
        except Exception as e:
            print(f"⚠️ Text extraction failed: {e}")
            text = f"Error processing {file_path.name}: {e}"
        
        # Enhanced range extraction using database intelligence
        start_time = time.time()
        extracted_ranges = self.db_extractor.extract_ranges_with_database_intelligence(
            text, file_path.name
        )
        extraction_time = time.time() - start_time
        
        # Get context information
        context_info = self.db_extractor.get_range_context_information(extracted_ranges)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(extracted_ranges, text, file_path.name)
        
        result = {
            'document_name': file_path.name,
            'file_path': str(file_path),
            'text_length': len(text),
            'extracted_ranges': extracted_ranges,
            'range_count': len(extracted_ranges),
            'context_information': context_info,
            'confidence_score': confidence_score,
            'extraction_time': round(extraction_time, 4),
            'processing_method': 'database_intelligent_extraction',
            'text_preview': text[:200] + "..." if len(text) > 200 else text
        }
        
        print(f"✅ Extracted {len(extracted_ranges)} ranges in {extraction_time:.3f}s")
        print(f"🎯 Confidence: {confidence_score:.1f}%")
        if extracted_ranges:
            print(f"📦 Ranges: {', '.join(extracted_ranges[:5])}")
            if len(extracted_ranges) > 5:
                print(f"    ... and {len(extracted_ranges) - 5} more")
        
        return result
    
    def _extract_pdf_text(self, file_path: Path) -> str:
        """Extract text from PDF (simplified)"""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except ImportError:
            return f"PDF processing not available for {file_path.name}"
        except Exception as e:
            return f"PDF extraction error: {e}"
    
    def _extract_doc_text(self, file_path: Path) -> str:
        """Extract text from DOC/DOCX (simplified)"""
        try:
            if file_path.suffix.lower() == '.docx':
                from docx import Document
                doc = Document(file_path)
                return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            else:
                # For .doc files, try LibreOffice conversion or fallback
                return f"DOC file processing for {file_path.name} - content simulation"
        except ImportError:
            return f"DOC processing not available for {file_path.name}"
        except Exception as e:
            return f"DOC extraction error: {e}"
    
    def _calculate_confidence_score(self, ranges: List[str], text: str, filename: str) -> float:
        """Calculate confidence score for extracted ranges"""
        if not ranges:
            return 0.0
        
        score = 0.0
        
        # Base score for having ranges
        score += 30.0
        
        # Bonus for multiple ranges (indicates comprehensive extraction)
        if len(ranges) > 1:
            score += min(20.0, len(ranges) * 5.0)
        
        # Bonus for ranges found in filename
        filename_upper = filename.upper()
        filename_matches = sum(1 for r in ranges if any(part in filename_upper for part in r.upper().split()))
        score += filename_matches * 15.0
        
        # Bonus for ranges found in text
        text_upper = text.upper()
        text_matches = sum(1 for r in ranges if r.upper() in text_upper)
        score += text_matches * 10.0
        
        # Penalty for very short text (might be extraction error)
        if len(text) < 100:
            score *= 0.7
        
        return min(100.0, score)
    
    def close(self):
        """Close resources"""
        self.db_extractor.close()


def main():
    """Main function to test enhanced document processor"""
    print("🚀 ENHANCED DOCUMENT PROCESSOR WITH DATABASE INSIGHTS")
    print("=" * 80)
    print("🧠 Database Intelligence | 🎯 Smart Range Extraction | 📊 Context Analysis")
    print()
    
    processor = EnhancedDocumentProcessor()
    
    try:
        # Find documents to process
        docs_dir = Path("data/input/letters")
        doc_files = []
        for pattern in ["*.doc*", "*.pdf"]:
            doc_files.extend(docs_dir.glob(pattern))
            doc_files.extend(docs_dir.glob(f"*/{pattern}"))
            doc_files.extend(docs_dir.glob(f"*/*/{pattern}"))
        
        if not doc_files:
            print("❌ No documents found")
            return 1
        
        # Process a few random documents
        selected_docs = random.sample(doc_files, min(5, len(doc_files)))
        print(f"📄 Processing {len(selected_docs)} documents with database intelligence")
        
        results = []
        total_start_time = time.time()
        
        for doc_file in selected_docs:
            result = processor.process_document(doc_file)
            results.append(result)
        
        total_time = time.time() - total_start_time
        
        # Summary statistics
        print(f"\n📊 PROCESSING SUMMARY")
        print("=" * 50)
        print(f"Documents processed: {len(results)}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Average time per document: {total_time/len(results):.2f}s")
        
        total_ranges = sum(r['range_count'] for r in results)
        print(f"Total ranges extracted: {total_ranges}")
        
        avg_confidence = sum(r['confidence_score'] for r in results) / len(results)
        print(f"Average confidence: {avg_confidence:.1f}%")
        
        successful_extractions = sum(1 for r in results if r['range_count'] > 0)
        success_rate = (successful_extractions / len(results)) * 100
        print(f"Success rate: {success_rate:.1f}% ({successful_extractions}/{len(results)})")
        
        # Show top ranges found
        all_ranges = []
        for result in results:
            all_ranges.extend(result['extracted_ranges'])
        
        if all_ranges:
            range_counts = Counter(all_ranges)
            print(f"\n🔝 TOP RANGES FOUND:")
            for range_name, count in range_counts.most_common(10):
                print(f"  {range_name}: {count} documents")
        
        # Save results
        output_dir = Path("data/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results_file = output_dir / "enhanced_processor_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n✅ Results saved: {results_file}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        processor.close()


if __name__ == "__main__":
    exit(main()) 