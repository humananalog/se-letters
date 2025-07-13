#!/usr/bin/env python3
"""
SE Letters Pipeline for Webapp - Returns JSON data instead of HTML files
This version is designed to work with the Next.js webapp and return structured data
"""

import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Set, Optional
from dataclasses import dataclass, field, asdict
import duckdb

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Import existing services
try:
    from se_letters.services.document_processor import DocumentProcessor
    from se_letters.services.enhanced_semantic_extraction_engine import (
        EnhancedSemanticExtractionEngine
    )
    from se_letters.services.enhanced_duckdb_service import (
        EnhancedDuckDBService, SearchCriteria
    )
    from se_letters.core.config import get_config
    ENHANCED_MODE = True
except ImportError:
    print("❌ Import error - using mock services", file=sys.stderr)
    ENHANCED_MODE = False
    
    class DocumentProcessor:
        def __init__(self, config):
            self.config = config
        
        def process_document(self, file_path):
            # Mock document processing
            class MockResult:
                def __init__(self, text):
                    self.text = text
            
            return MockResult(f"Mock text from {file_path.name}")
    
    class EnhancedSemanticExtractionEngine:
        def extract_enhanced_semantics(self, text, context=None):
            # Mock extraction
            mock_ranges = [
                'Custom', 'Masterpact NT', 'ID', 'Masterpact M', 'CT'
            ]
            
            class MockResult:
                def __init__(self):
                    self.ranges = mock_ranges
                    self.subranges = ['NSX100', 'ATV900']
                    self.device_types = ['LV equipment - Low voltage circuit breaker']
                    self.brands = ['Schneider Electric']
                    self.pl_services = ['PPIBS']
                    self.technical_specs = ['voltage: 690V', 'current: 630A']
                    self.extraction_confidence = 0.85
                    self.processing_time_ms = 50.0
                    self.extraction_method = 'mock_enhanced'
                    self.ai_metadata = {'mock': True}
            
            return MockResult()
        
        def close(self):
            pass
    
    class EnhancedDuckDBService:
        def __init__(self, db_path=None):
            pass
        
        def search_products(self, criteria):
            class MockSearchResult:
                def __init__(self):
                    self.products = []
                    self.total_count = 0
                    self.search_space_reduction = 0.0
                    self.processing_time_ms = 10.0
                    self.search_strategy = 'mock'
            return MockSearchResult()
        
        def close(self):
            pass
    
    class SearchCriteria:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    def get_config():
        class MockConfig:
            pass
        return MockConfig()


@dataclass
class DocumentContext:
    """Document context with intelligent analysis"""
    voltage_level: Optional[str] = None
    product_category: Optional[str] = None
    pl_services_hint: Optional[str] = None
    confidence_score: float = 0.0
    thumbnail_data: Optional[str] = None


@dataclass
class ProcessingResult:
    """Enhanced processing result with multi-dimensional extraction"""
    success: bool
    file_name: str
    file_path: str
    file_size: int
    context: DocumentContext
    content: str = ""
    extracted_text: str = ""  # Raw OCR/extracted text for debug
    # Multi-dimensional extraction results
    extracted_ranges: List[str] = field(default_factory=list)
    extracted_subranges: List[str] = field(default_factory=list)
    extracted_device_types: List[str] = field(default_factory=list)
    extracted_brands: List[str] = field(default_factory=list)
    extracted_pl_services: List[str] = field(default_factory=list)
    extracted_technical_specs: List[str] = field(default_factory=list)
    # Validated results
    valid_ranges: List[str] = field(default_factory=list)
    invalid_ranges: List[str] = field(default_factory=list)
    # Product results
    obsolete_products: List[Dict[str, Any]] = field(default_factory=list)
    replacement_products: List[Dict[str, Any]] = field(default_factory=list)
    obsolete_count: int = 0
    replacement_count: int = 0
    # Performance metrics
    processing_time_ms: float = 0.0
    search_space_reduction: float = 0.0
    search_strategy: str = ""
    extraction_method: str = ""
    extraction_confidence: float = 0.0
    error: str = ""


class WebappDuckDBService:
    """DuckDB service for webapp - returns structured data"""
    
    def __init__(self, db_path: str = "data/IBcatalogue.duckdb"):
        self.conn = duckdb.connect(db_path)
        
        # Define correct obsolete statuses
        self.obsolete_statuses = [
            '18-End of commercialisation',
            '19-end of commercialization block',
            '14-End of commerc. announced',
            '20-Temporary block'
        ]
        
        # Load valid ranges from database
        self.valid_ranges = self._load_valid_ranges()
        print(f"✅ Loaded {len(self.valid_ranges)} valid ranges from database", file=sys.stderr)
        
        # Get obsolete product count
        self.total_obsolete_products = self._get_total_obsolete_count()
        print(f"✅ Total obsolete products in database: {self.total_obsolete_products:,}", file=sys.stderr)
    
    def _load_valid_ranges(self) -> Set[str]:
        """Load all valid product ranges from database"""
        query = "SELECT DISTINCT RANGE_LABEL FROM products WHERE RANGE_LABEL IS NOT NULL"
        result = self.conn.execute(query).fetchall()
        return set(r[0] for r in result)
    
    def _get_total_obsolete_count(self) -> int:
        """Get total obsolete products count"""
        query = f"SELECT COUNT(*) FROM products WHERE COMMERCIAL_STATUS IN ({','.join(['?' for _ in self.obsolete_statuses])})"
        return self.conn.execute(query, self.obsolete_statuses).fetchone()[0]
    
    def validate_ranges(self, extracted_ranges: List[str]) -> tuple[List[str], List[str]]:
        """Validate extracted ranges against database"""
        valid_ranges = []
        invalid_ranges = []
        
        for range_name in extracted_ranges:
            if range_name in self.valid_ranges:
                if range_name not in valid_ranges:
                    valid_ranges.append(range_name)
            elif len(range_name) > 3:
                matches = [vr for vr in self.valid_ranges if range_name.upper() in vr.upper()]
                if matches:
                    for match in matches[:3]:
                        if match not in valid_ranges:
                            valid_ranges.append(match)
                else:
                    invalid_ranges.append(range_name)
            else:
                invalid_ranges.append(range_name)
        
        return valid_ranges, invalid_ranges
    
    def find_obsolete_products(self, valid_ranges: List[str]) -> List[Dict[str, Any]]:
        """Find obsolete products for valid ranges"""
        if not valid_ranges:
            return []
        
        # Create placeholders for the query
        placeholders = ','.join(['?' for _ in valid_ranges])
        query = f"""
        SELECT 
            PRODUCT_IDENTIFIER,
            RANGE_LABEL,
            PRODUCT_DESCRIPTION,
            COMMERCIAL_STATUS,
            END_OF_COMMERCIALISATION,
            SERVICE_OBSOLECENSE_DATE
        FROM products 
        WHERE RANGE_LABEL IN ({placeholders})
        AND COMMERCIAL_STATUS IN ({','.join(['?' for _ in self.obsolete_statuses])})
        LIMIT 100
        """
        
        params = valid_ranges + self.obsolete_statuses
        result = self.conn.execute(query, params).fetchall()
        
        products = []
        for row in result:
            # Clean data to remove any logging contamination
            def clean_field(field):
                if field is None:
                    return ""
                text = str(field).replace('\n', ' ').replace('\r', ' ').strip()
                # Remove any logging messages that might be embedded
                text = text.replace('Real Pipeline', '').replace('stdout:', '').replace('stderr:', '')
                # Remove any process IDs or timestamps
                import re
                text = re.sub(r'\d{5,}\s+stdout:\s*', '', text)
                text = re.sub(r'\d{5,}\s+stderr:\s*', '', text)
                return text.strip()
            
            products.append({
                'product_id': clean_field(row[0]),
                'range_label': clean_field(row[1]),
                'description': clean_field(row[2]),
                'commercial_status': clean_field(row[3]),
                'commercialization_end': str(row[4]) if row[4] else None,
                'service_end': str(row[5]) if row[5] else None
            })
        
        return products
    
    def find_replacement_products(self, valid_ranges: List[str]) -> List[Dict[str, Any]]:
        """Find replacement products for valid ranges"""
        if not valid_ranges:
            return []
        
        # Create placeholders for the query
        placeholders = ','.join(['?' for _ in valid_ranges])
        query = f"""
        SELECT 
            PRODUCT_IDENTIFIER,
            RANGE_LABEL,
            PRODUCT_DESCRIPTION,
            COMMERCIAL_STATUS
        FROM products 
        WHERE RANGE_LABEL IN ({placeholders})
        AND COMMERCIAL_STATUS NOT IN ({','.join(['?' for _ in self.obsolete_statuses])})
        LIMIT 50
        """
        
        params = valid_ranges + self.obsolete_statuses
        result = self.conn.execute(query, params).fetchall()
        
        products = []
        for row in result:
            # Clean data to remove any logging contamination
            def clean_field(field):
                if field is None:
                    return ""
                text = str(field).replace('\n', ' ').replace('\r', ' ').strip()
                # Remove any logging messages that might be embedded
                text = text.replace('Real Pipeline', '').replace('stdout:', '').replace('stderr:', '')
                # Remove any process IDs or timestamps
                import re
                text = re.sub(r'\d{5,}\s+stdout:\s*', '', text)
                text = re.sub(r'\d{5,}\s+stderr:\s*', '', text)
                return text.strip()
            
            products.append({
                'product_id': clean_field(row[0]),
                'range_label': clean_field(row[1]),
                'description': clean_field(row[2]),
                'commercial_status': clean_field(row[3])
            })
        
        return products
    
    def close(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()


class WebappContextAnalyzer:
    """Context analyzer for webapp"""
    
    def __init__(self, db_service):
        self.db_service = db_service
    
    def analyze_document_context(self, file_path: Path) -> DocumentContext:
        """Analyze document context"""
        # Simple context analysis based on filename
        filename = file_path.name.lower()
        
        if 'pix' in filename:
            return DocumentContext(
                product_category="PIX Circuit Breakers",
                confidence_score=0.8
            )
        elif 'mge' in filename:
            return DocumentContext(
                product_category="MGE UPS Systems",
                confidence_score=0.7
            )
        elif 'motorpact' in filename:
            return DocumentContext(
                product_category="Motorpact Contactors",
                confidence_score=0.9
            )
        else:
            return DocumentContext(
                product_category="Unknown",
                confidence_score=0.0
            )


class WebappPipeline:
    """Pipeline for webapp that returns JSON data"""
    
    def __init__(self):
        print("🔧 WEBAPP PIPELINE INITIALIZED", file=sys.stderr)
        print("✅ All services configured for JSON output", file=sys.stderr)
        
        # Initialize services
        config = get_config()
        self.doc_processor = DocumentProcessor(config)
        self.db_service = WebappDuckDBService()
        self.context_analyzer = WebappContextAnalyzer(self.db_service)
        
        if ENHANCED_MODE:
            self.extraction_engine = EnhancedSemanticExtractionEngine()
            self.enhanced_db_service = EnhancedDuckDBService()
        else:
            self.extraction_engine = None
            self.enhanced_db_service = None
    
    def process_single_document(self, document_path: str) -> Dict[str, Any]:
        """Process a single document and return JSON data"""
        doc_file = Path(document_path)
        
        if not doc_file.exists():
            return {
                'success': False,
                'error': f'Document not found: {document_path}',
                'file_name': doc_file.name
            }
        
        print(f"🔄 Processing: {doc_file.name}", file=sys.stderr)
        start_time = time.time()
        
        try:
            # 1. Context analysis
            context = self.context_analyzer.analyze_document_context(doc_file)
            print(f"  🧠 Context: {context.product_category or 'Unknown'} (Conf: {context.confidence_score:.2f})", file=sys.stderr)
            
            # 2. Document processing
            doc_result = self.doc_processor.process_document(doc_file)
            
            if doc_result is None:
                return {
                    'success': False,
                    'error': 'Document processing failed',
                    'file_name': doc_file.name,
                    'processing_time_ms': (time.time() - start_time) * 1000
                }
            
            print(f"  📄 Text: {len(doc_result.text)} characters", file=sys.stderr)
            
            # 3. Semantic extraction
            if self.extraction_engine:
                extraction_result = self.extraction_engine.extract_enhanced_semantics(
                    doc_result.text, context
                )
            else:
                # Mock extraction
                extraction_result = self._mock_extraction()
            
            print(f"  🔍 Raw extraction: {len(extraction_result.ranges)} ranges", file=sys.stderr)
            
            # 4. Database search
            valid_ranges, invalid_ranges = self.db_service.validate_ranges(extraction_result.ranges)
            obsolete_products = self.db_service.find_obsolete_products(valid_ranges)
            replacement_products = self.db_service.find_replacement_products(valid_ranges)
            
            print(f"  ✅ Valid ranges: {len(valid_ranges)}", file=sys.stderr)
            print(f"  ❌ Invalid ranges filtered: {len(invalid_ranges)}", file=sys.stderr)
            print(f"  🎯 Obsolete products: {len(obsolete_products):,}", file=sys.stderr)
            print(f"  🔄 Replacement products: {len(replacement_products):,}", file=sys.stderr)
            
            processing_time = time.time() - start_time
            print(f"  ⚡ Processing time: {processing_time*1000:.1f}ms", file=sys.stderr)
            
            # Calculate vector search metrics
            total_extracted = len(extraction_result.ranges)
            total_valid = len(valid_ranges)
            search_space_reduction = (total_valid / total_extracted * 100) if total_extracted > 0 else 0.0
            search_strategy = (
                f"Database Range Validation + Product Matching "
                f"({self.db_service.total_obsolete_products:,} products)"
            )
            
            # Create result with enhanced OCR and raw data
            result = ProcessingResult(
                success=True,
                file_name=doc_file.name,
                file_path=str(doc_file),
                file_size=doc_file.stat().st_size,
                context=context,
                content=doc_result.text,  # Full content for raw data tab
                extracted_text=doc_result.text,  # OCR/extracted text for debug
                extracted_ranges=extraction_result.ranges,
                extracted_subranges=getattr(extraction_result, 'subranges', []),
                extracted_device_types=getattr(extraction_result, 'device_types', []),
                extracted_brands=getattr(extraction_result, 'brands', []),
                extracted_pl_services=getattr(extraction_result, 'pl_services', []),
                extracted_technical_specs=getattr(extraction_result, 'technical_specs', []),
                valid_ranges=valid_ranges,
                invalid_ranges=invalid_ranges,
                obsolete_products=obsolete_products,
                replacement_products=replacement_products,
                obsolete_count=len(obsolete_products),
                replacement_count=len(replacement_products),
                processing_time_ms=processing_time * 1000,
                search_space_reduction=search_space_reduction,
                search_strategy=search_strategy,
                extraction_method=getattr(extraction_result, 'extraction_method', 'webapp'),
                extraction_confidence=getattr(extraction_result, 'extraction_confidence', 0.0)
            )
            
            # Convert to dict for JSON serialization
            return self._result_to_dict(result)
            
        except Exception as e:
            print(f"  ❌ Error: {e}", file=sys.stderr)
            return {
                'success': False,
                'error': str(e),
                'file_name': doc_file.name,
                'processing_time_ms': (time.time() - start_time) * 1000
            }
    
    def _mock_extraction(self):
        """Mock extraction for fallback mode"""
        class MockResult:
            def __init__(self):
                self.ranges = ['Custom', 'Masterpact NT', 'ID', 'Masterpact M', 'CT']
                self.subranges = ['NSX100', 'ATV900']
                self.device_types = ['LV equipment - Low voltage circuit breaker']
                self.brands = ['Schneider Electric']
                self.pl_services = ['PPIBS']
                self.technical_specs = ['voltage: 690V', 'current: 630A']
                self.extraction_confidence = 0.85
                self.processing_time_ms = 50.0
                self.extraction_method = 'mock_webapp'
                self.ai_metadata = {'mock': True}
        
        return MockResult()
    
    def _result_to_dict(self, result: ProcessingResult) -> Dict[str, Any]:
        """Convert ProcessingResult to dict for JSON serialization"""
        data = asdict(result)
        
        # Convert context to dict
        data['context'] = asdict(result.context)
        
        return data
    
    def close(self):
        """Close connections"""
        self.db_service.close()
        if self.extraction_engine:
            self.extraction_engine.close()
        if self.enhanced_db_service:
            self.enhanced_db_service.close()


def main():
    """Main function for command line usage"""
    if len(sys.argv) < 2:
        print("Usage: python se_letters_pipeline_webapp.py <document_path>", file=sys.stderr)
        sys.exit(1)
    
    document_path = sys.argv[1]
    pipeline = WebappPipeline()
    
    try:
        result = pipeline.process_single_document(document_path)
        # Validate JSON before output
        json_output = json.dumps(result, indent=2, default=str)
        # Test parse to ensure valid JSON
        json.loads(json_output)
        print(json_output)
    except json.JSONDecodeError as e:
        print(f"❌ JSON encoding error: {e}", file=sys.stderr)
        # Output minimal fallback result
        fallback = {
            'success': False,
            'error': f'JSON encoding failed: {e}',
            'file_name': document_path.split('/')[-1]
        }
        print(json.dumps(fallback, indent=2))
    except Exception as e:
        print(f"❌ Pipeline error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    finally:
        pipeline.close()


if __name__ == "__main__":
    main() 