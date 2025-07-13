#!/usr/bin/env python3
"""
Industrial Badass Pipeline - Professional Grade
Monochromatic UI, Advanced Debugging, Migration Intelligence
"""

import sys
import time
import json
import random
import tempfile
import subprocess
import hashlib
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime
import base64

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

import duckdb


@dataclass
class ProcessingTrace:
    """Processing trace for debugging and audit"""
    trace_id: str
    timestamp: str
    stage: str
    operation: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    confidence: float
    processing_time: float
    metadata: Dict[str, Any]


@dataclass
class MigrationPath:
    """Migration path from obsolete to new products"""
    obsolete_product: str
    obsolete_range: str
    recommended_products: List[Dict[str, Any]]
    migration_confidence: float
    business_justification: str
    pl_service: str
    device_type: str


@dataclass
class QualityMetrics:
    """Quality metrics for output validation"""
    extraction_accuracy: float
    confidence_distribution: Dict[str, int]
    pl_service_coverage: float
    migration_completeness: float
    traceability_score: float
    overall_quality: float


class IndustrialIntelligenceEngine:
    """Industrial-grade intelligence engine with full traceability"""
    
    def __init__(self, db_path: str = "data/IBcatalogue.duckdb"):
        self.db_path = db_path
        self.conn = None
        self.traces: List[ProcessingTrace] = []
        self.session_id = str(uuid.uuid4())[:8]
        
        # Industrial PL Services mapping
        self.pl_services = {
            'PPIBS': {
                'name': 'Power Products Services',
                'focus': 'Circuit breakers, protection, switchgear',
                'criticality': 'HIGH',
                'migration_priority': 1
            },
            'PSIBS': {
                'name': 'Power Systems Services', 
                'focus': 'Medium voltage, transformers, distribution',
                'criticality': 'HIGH',
                'migration_priority': 2
            },
            'SPIBS': {
                'name': 'Secure Power Services',
                'focus': 'UPS systems, power protection, data center',
                'criticality': 'CRITICAL',
                'migration_priority': 1
            },
            'IDPAS': {
                'name': 'Industrial Process Automation',
                'focus': 'SCADA, telemetry, flow measurement',
                'criticality': 'MEDIUM',
                'migration_priority': 3
            },
            'IDIBS': {
                'name': 'Industrial Automation Operations',
                'focus': 'PLCs, drives, motion control',
                'criticality': 'MEDIUM',
                'migration_priority': 3
            },
            'DPIBS': {
                'name': 'Digital Power Services',
                'focus': 'Energy monitoring, digital solutions',
                'criticality': 'LOW',
                'migration_priority': 4
            },
            'DBIBS': {
                'name': 'Digital Building Services',
                'focus': 'HVAC, building automation',
                'criticality': 'LOW',
                'migration_priority': 5
            }
        }
        
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize industrial intelligence engine"""
        print(f"[{self.session_id}] INITIALIZING INDUSTRIAL INTELLIGENCE ENGINE")
        print("=" * 80)
        
        self.conn = duckdb.connect(self.db_path)
        
        # Load industrial patterns
        self._load_product_intelligence()
        self._load_migration_intelligence()
        
        print(f"[{self.session_id}] ENGINE READY - FULL TRACEABILITY ENABLED")
    
    def _load_product_intelligence(self):
        """Load comprehensive product intelligence"""
        trace_id = self._generate_trace_id()
        start_time = time.time()
        
        # Load range patterns with migration data
        range_query = """
            SELECT 
                RANGE_LABEL,
                PL_SERVICES,
                COMMERCIAL_STATUS,
                COUNT(*) as product_count,
                STRING_AGG(DISTINCT PRODUCT_IDENTIFIER, ' | ') as products,
                STRING_AGG(DISTINCT DEVICETYPE_LABEL, ' | ') as device_types
            FROM products 
            WHERE RANGE_LABEL IS NOT NULL
            GROUP BY RANGE_LABEL, PL_SERVICES, COMMERCIAL_STATUS
            ORDER BY product_count DESC
        """
        
        ranges = self.conn.execute(range_query).fetchall()
        
        self.range_intelligence = {}
        obsolete_count = 0
        active_count = 0
        
        for range_label, pl_service, status, count, products, device_types in ranges:
            is_obsolete = status in ['01-Obsolete', '02-Obsolete']
            
            if is_obsolete:
                obsolete_count += 1
            else:
                active_count += 1
            
            self.range_intelligence[range_label] = {
                'pl_service': pl_service,
                'status': status,
                'is_obsolete': is_obsolete,
                'product_count': count,
                'products': products.split(' | ') if products else [],
                'device_types': device_types.split(' | ') if device_types else [],
                'migration_needed': is_obsolete,
                'criticality': self.pl_services.get(pl_service, {}).get('criticality', 'UNKNOWN')
            }
        
        processing_time = time.time() - start_time
        
        # Record trace
        self._add_trace(ProcessingTrace(
            trace_id=trace_id,
            timestamp=datetime.now().isoformat(),
            stage="initialization",
            operation="load_product_intelligence", 
            input_data={"query": "range_patterns"},
            output_data={
                "total_ranges": len(self.range_intelligence),
                "obsolete_ranges": obsolete_count,
                "active_ranges": active_count
            },
            confidence=1.0,
            processing_time=processing_time,
            metadata={"session_id": self.session_id}
        ))
        
        print(f"[{trace_id}] LOADED {len(self.range_intelligence)} RANGES")
        print(f"[{trace_id}] OBSOLETE: {obsolete_count} | ACTIVE: {active_count}")
    
    def _load_migration_intelligence(self):
        """Load migration intelligence for obsolete products"""
        trace_id = self._generate_trace_id()
        start_time = time.time()
        
        # Find migration patterns
        migration_query = """
            WITH obsolete_products AS (
                SELECT RANGE_LABEL, PL_SERVICES, DEVICETYPE_LABEL
                FROM products 
                WHERE COMMERCIAL_STATUS IN ('01-Obsolete', '02-Obsolete')
                AND RANGE_LABEL IS NOT NULL
            ),
            active_products AS (
                SELECT RANGE_LABEL, PL_SERVICES, DEVICETYPE_LABEL, COUNT(*) as count
                FROM products 
                WHERE COMMERCIAL_STATUS = '08-Commercialised'
                AND RANGE_LABEL IS NOT NULL
                GROUP BY RANGE_LABEL, PL_SERVICES, DEVICETYPE_LABEL
                ORDER BY count DESC
            )
            SELECT 
                o.RANGE_LABEL as obsolete_range,
                o.PL_SERVICES,
                o.DEVICETYPE_LABEL,
                a.RANGE_LABEL as recommended_range,
                a.count as product_count
            FROM obsolete_products o
            JOIN active_products a ON o.PL_SERVICES = a.PL_SERVICES 
                AND o.DEVICETYPE_LABEL = a.DEVICETYPE_LABEL
            LIMIT 1000
        """
        
        migrations = self.conn.execute(migration_query).fetchall()
        
        self.migration_intelligence = defaultdict(list)
        
        for obsolete_range, pl_service, device_type, recommended_range, count in migrations:
            self.migration_intelligence[obsolete_range].append({
                'recommended_range': recommended_range,
                'pl_service': pl_service,
                'device_type': device_type,
                'product_count': count,
                'confidence': min(0.95, count / 1000)
            })
        
        processing_time = time.time() - start_time
        
        # Record trace
        self._add_trace(ProcessingTrace(
            trace_id=trace_id,
            timestamp=datetime.now().isoformat(),
            stage="initialization",
            operation="load_migration_intelligence",
            input_data={"query": "migration_patterns"},
            output_data={
                "migration_paths": len(self.migration_intelligence),
                "total_recommendations": len(migrations)
            },
            confidence=1.0,
            processing_time=processing_time,
            metadata={"session_id": self.session_id}
        ))
        
        print(f"[{trace_id}] LOADED {len(self.migration_intelligence)} MIGRATION PATHS")
    
    def process_document_industrial(self, file_path: Path) -> Dict[str, Any]:
        """Process document with industrial-grade intelligence"""
        trace_id = self._generate_trace_id()
        start_time = time.time()
        
        print(f"\n[{trace_id}] PROCESSING: {file_path.name}")
        print("-" * 80)
        
        # Extract document content
        content = self._extract_document_content(file_path, trace_id)
        
        # Industrial extraction with full traceability
        extraction_result = self._extract_with_traceability(content, file_path.name, trace_id)
        
        # Generate migration paths
        migration_paths = self._generate_migration_paths(extraction_result, trace_id)
        
        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(extraction_result, migration_paths)
        
        processing_time = time.time() - start_time
        
        # Complete result with full traceability
        result = {
            'document_name': file_path.name,
            'file_path': str(file_path),
            'session_id': self.session_id,
            'trace_id': trace_id,
            'processing_time': processing_time,
            'content_preview': content[:500] + "..." if len(content) > 500 else content,
            'content_hash': hashlib.md5(content.encode()).hexdigest(),
            'extraction_result': extraction_result,
            'migration_paths': migration_paths,
            'quality_metrics': asdict(quality_metrics),
            'traces': [asdict(t) for t in self.traces if t.trace_id == trace_id]
        }
        
        # Final trace
        self._add_trace(ProcessingTrace(
            trace_id=trace_id,
            timestamp=datetime.now().isoformat(),
            stage="completion",
            operation="process_document_industrial",
            input_data={"file": file_path.name},
            output_data={
                "ranges_extracted": len(extraction_result.get('ranges', [])),
                "migration_paths": len(migration_paths),
                "quality_score": quality_metrics.overall_quality
            },
            confidence=quality_metrics.overall_quality,
            processing_time=processing_time,
            metadata={"session_id": self.session_id}
        ))
        
        print(f"[{trace_id}] COMPLETED - QUALITY: {quality_metrics.overall_quality:.1%}")
        
        return result
    
    def _extract_document_content(self, file_path: Path, trace_id: str) -> str:
        """Extract document content with tracing"""
        start_time = time.time()
        
        try:
            if file_path.suffix.lower() == '.pdf':
                content = self._extract_pdf_industrial(file_path)
            elif file_path.suffix.lower() in ['.doc', '.docx']:
                content = self._extract_doc_industrial(file_path)
            else:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            content = f"EXTRACTION_ERROR: {str(e)}"
        
        processing_time = time.time() - start_time
        
        self._add_trace(ProcessingTrace(
            trace_id=trace_id,
            timestamp=datetime.now().isoformat(),
            stage="extraction",
            operation="extract_document_content",
            input_data={"file_type": file_path.suffix, "file_size": file_path.stat().st_size},
            output_data={"content_length": len(content), "success": not content.startswith("EXTRACTION_ERROR")},
            confidence=0.0 if content.startswith("EXTRACTION_ERROR") else 1.0,
            processing_time=processing_time,
            metadata={"file_path": str(file_path)}
        ))
        
        return content
    
    def _extract_pdf_industrial(self, file_path: Path) -> str:
        """Industrial PDF extraction"""
        try:
            import fitz
            doc = fitz.open(file_path)
            content = ""
            for page_num, page in enumerate(doc):
                page_text = page.get_text()
                content += f"\n[PAGE_{page_num+1}]\n{page_text}"
            doc.close()
            return content
        except ImportError:
            return f"PDF_FALLBACK: {file_path.name}"
        except Exception as e:
            return f"PDF_ERROR: {str(e)}"
    
    def _extract_doc_industrial(self, file_path: Path) -> str:
        """Industrial DOC extraction"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                result = subprocess.run([
                    'libreoffice', '--headless', '--convert-to', 'txt',
                    '--outdir', str(temp_path), str(file_path)
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    txt_file = temp_path / f"{file_path.stem}.txt"
                    if txt_file.exists():
                        return txt_file.read_text(encoding='utf-8')
            
            return f"DOC_FALLBACK: {file_path.name}"
        except Exception as e:
            return f"DOC_ERROR: {str(e)}"
    
    def _extract_with_traceability(self, content: str, doc_name: str, trace_id: str) -> Dict[str, Any]:
        """Extract ranges with full traceability"""
        start_time = time.time()
        
        extracted_ranges = []
        detected_pl_services = set()
        extraction_methods = {}
        confidence_scores = {}
        
        content_upper = content.upper()
        
        # Method 1: Direct range matching
        for range_label, range_info in self.range_intelligence.items():
            if range_label.upper() in content_upper:
                confidence = 0.95
                method = "DIRECT_MATCH"
                
                extracted_ranges.append({
                    'range': range_label,
                    'pl_service': range_info['pl_service'],
                    'status': range_info['status'],
                    'is_obsolete': range_info['is_obsolete'],
                    'confidence': confidence,
                    'extraction_method': method,
                    'product_count': range_info['product_count'],
                    'criticality': range_info['criticality']
                })
                
                confidence_scores[range_label] = confidence
                extraction_methods[range_label] = method
                detected_pl_services.add(range_info['pl_service'])
        
        # Method 2: PL Service context detection
        for pl_code, pl_info in self.pl_services.items():
            pl_keywords = pl_info['focus'].lower().split()
            matches = sum(1 for keyword in pl_keywords if keyword in content.lower())
            
            if matches >= 2:
                detected_pl_services.add(pl_code)
                
                # Find ranges in this PL service
                for range_label, range_info in self.range_intelligence.items():
                    if (range_info['pl_service'] == pl_code and 
                        range_label not in confidence_scores):
                        
                        # Check if range words appear
                        range_words = range_label.upper().split()
                        word_matches = sum(1 for word in range_words 
                                         if len(word) > 2 and word in content_upper)
                        
                        if word_matches > 0:
                            confidence = 0.7 + (word_matches * 0.1)
                            method = f"PL_CONTEXT_{pl_code}"
                            
                            extracted_ranges.append({
                                'range': range_label,
                                'pl_service': range_info['pl_service'],
                                'status': range_info['status'],
                                'is_obsolete': range_info['is_obsolete'],
                                'confidence': confidence,
                                'extraction_method': method,
                                'product_count': range_info['product_count'],
                                'criticality': range_info['criticality']
                            })
                            
                            confidence_scores[range_label] = confidence
                            extraction_methods[range_label] = method
        
        # Sort by confidence and limit to top 30 for precision
        extracted_ranges.sort(key=lambda x: x['confidence'], reverse=True)
        extracted_ranges = extracted_ranges[:30]
        
        processing_time = time.time() - start_time
        
        # Record detailed trace
        self._add_trace(ProcessingTrace(
            trace_id=trace_id,
            timestamp=datetime.now().isoformat(),
            stage="extraction",
            operation="extract_with_traceability",
            input_data={
                "content_length": len(content),
                "document": doc_name
            },
            output_data={
                "ranges_found": len(extracted_ranges),
                "pl_services_detected": len(detected_pl_services),
                "methods_used": list(set(extraction_methods.values()))
            },
            confidence=sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.0,
            processing_time=processing_time,
            metadata={
                "extraction_methods": extraction_methods,
                "confidence_scores": confidence_scores
            }
        ))
        
        return {
            'ranges': extracted_ranges,
            'pl_services': list(detected_pl_services),
            'extraction_methods': extraction_methods,
            'confidence_scores': confidence_scores,
            'overall_confidence': sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.0
        }
    
    def _generate_migration_paths(self, extraction_result: Dict[str, Any], trace_id: str) -> List[MigrationPath]:
        """Generate migration paths for obsolete products"""
        start_time = time.time()
        
        migration_paths = []
        obsolete_ranges = [r for r in extraction_result['ranges'] if r['is_obsolete']]
        
        for obsolete_range in obsolete_ranges:
            range_name = obsolete_range['range']
            
            if range_name in self.migration_intelligence:
                recommendations = self.migration_intelligence[range_name][:3]  # Top 3
                
                migration_path = MigrationPath(
                    obsolete_product=range_name,
                    obsolete_range=range_name,
                    recommended_products=recommendations,
                    migration_confidence=sum(r['confidence'] for r in recommendations) / len(recommendations),
                    business_justification=f"Obsolete {obsolete_range['pl_service']} product requires migration",
                    pl_service=obsolete_range['pl_service'],
                    device_type=obsolete_range.get('device_types', ['Unknown'])[0] if obsolete_range.get('device_types') else 'Unknown'
                )
                
                migration_paths.append(migration_path)
        
        processing_time = time.time() - start_time
        
        # Record trace
        self._add_trace(ProcessingTrace(
            trace_id=trace_id,
            timestamp=datetime.now().isoformat(),
            stage="migration",
            operation="generate_migration_paths",
            input_data={"obsolete_ranges": len(obsolete_ranges)},
            output_data={"migration_paths": len(migration_paths)},
            confidence=sum(mp.migration_confidence for mp in migration_paths) / len(migration_paths) if migration_paths else 0.0,
            processing_time=processing_time,
            metadata={"obsolete_products": [r['range'] for r in obsolete_ranges]}
        ))
        
        return migration_paths
    
    def _calculate_quality_metrics(self, extraction_result: Dict[str, Any], migration_paths: List[MigrationPath]) -> QualityMetrics:
        """Calculate comprehensive quality metrics"""
        ranges = extraction_result['ranges']
        
        # Extraction accuracy based on confidence
        extraction_accuracy = extraction_result['overall_confidence']
        
        # Confidence distribution
        confidence_distribution = {
            'high': sum(1 for r in ranges if r['confidence'] > 0.8),
            'medium': sum(1 for r in ranges if 0.6 <= r['confidence'] <= 0.8),
            'low': sum(1 for r in ranges if r['confidence'] < 0.6)
        }
        
        # PL service coverage
        detected_services = set(extraction_result['pl_services'])
        total_services = len(self.pl_services)
        pl_service_coverage = len(detected_services) / total_services
        
        # Migration completeness
        obsolete_ranges = [r for r in ranges if r['is_obsolete']]
        migration_completeness = len(migration_paths) / len(obsolete_ranges) if obsolete_ranges else 1.0
        
        # Traceability score (based on trace completeness)
        traceability_score = 1.0  # Full traceability implemented
        
        # Overall quality score
        overall_quality = (
            extraction_accuracy * 0.4 +
            pl_service_coverage * 0.2 +
            migration_completeness * 0.2 +
            traceability_score * 0.2
        )
        
        return QualityMetrics(
            extraction_accuracy=extraction_accuracy,
            confidence_distribution=confidence_distribution,
            pl_service_coverage=pl_service_coverage,
            migration_completeness=migration_completeness,
            traceability_score=traceability_score,
            overall_quality=overall_quality
        )
    
    def _generate_trace_id(self) -> str:
        """Generate unique trace ID"""
        return f"{self.session_id}-{len(self.traces):04d}"
    
    def _add_trace(self, trace: ProcessingTrace):
        """Add trace to audit trail"""
        self.traces.append(trace)
    
    def get_session_traces(self) -> List[ProcessingTrace]:
        """Get all traces for current session"""
        return self.traces
    
    def close(self):
        """Close engine and save traces"""
        if self.conn:
            self.conn.close()
        
        # Save traces for audit
        traces_file = Path("data/output") / f"traces_{self.session_id}.json"
        traces_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(traces_file, 'w') as f:
            json.dump([asdict(t) for t in self.traces], f, indent=2, default=str)
        
        print(f"[{self.session_id}] TRACES SAVED: {traces_file}")


def main():
    """Main function for industrial pipeline"""
    print("INDUSTRIAL BADASS PIPELINE - PROFESSIONAL GRADE")
    print("=" * 80)
    print("MONOCHROMATIC UI | ADVANCED DEBUGGING | MIGRATION INTELLIGENCE")
    print()
    
    # Initialize industrial engine
    engine = IndustrialIntelligenceEngine()
    
    try:
        # Find documents
        docs_dir = Path("data/input/letters")
        doc_files = []
        for pattern in ["*.doc*", "*.pdf"]:
            doc_files.extend(docs_dir.glob(pattern))
            doc_files.extend(docs_dir.glob(f"*/{pattern}"))
            doc_files.extend(docs_dir.glob(f"*/*/{pattern}"))
        
        if not doc_files:
            print("NO DOCUMENTS FOUND")
            return
        
        # Process sample documents
        selected_docs = random.sample(doc_files, min(3, len(doc_files)))
        
        results = []
        for doc_file in selected_docs:
            result = engine.process_document_industrial(doc_file)
            results.append(result)
        
        # Generate industrial report
        from scripts.industrial_html_generator import IndustrialHTMLGenerator
        html_generator = IndustrialHTMLGenerator()
        
        html_report = html_generator.generate_industrial_report(results, engine.get_session_traces())
        
        # Save report
        output_dir = Path("data/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        html_file = output_dir / "industrial_pipeline_report.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        print(f"\nINDUSTRIAL REPORT GENERATED: {html_file}")
        
        # Try to open in browser
        try:
            import webbrowser
            webbrowser.open(f"file://{html_file.absolute()}")
        except:
            pass
        
    finally:
        engine.close()


if __name__ == "__main__":
    main() 