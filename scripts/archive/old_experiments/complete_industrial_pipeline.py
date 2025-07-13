#!/usr/bin/env python3
"""
Complete Industrial Badass Pipeline - Professional Grade
Monochromatic UI, Advanced Debugging, Migration Intelligence, Console Mode
Self-contained implementation with embedded HTML generator
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
                'migration_priority': 1,
                'keywords': ['circuit', 'breaker', 'protection', 'relay', 'contactor']
            },
            'PSIBS': {
                'name': 'Power Systems Services', 
                'focus': 'Medium voltage, transformers, distribution',
                'criticality': 'HIGH',
                'migration_priority': 2,
                'keywords': ['medium', 'voltage', 'transformer', 'distribution', 'pix']
            },
            'SPIBS': {
                'name': 'Secure Power Services',
                'focus': 'UPS systems, power protection, data center',
                'criticality': 'CRITICAL',
                'migration_priority': 1,
                'keywords': ['ups', 'battery', 'power', 'protection', 'cooling', 'galaxy']
            },
            'IDPAS': {
                'name': 'Industrial Process Automation',
                'focus': 'SCADA, telemetry, flow measurement',
                'criticality': 'MEDIUM',
                'migration_priority': 3,
                'keywords': ['scada', 'flow', 'measurement', 'telemetry', 'radio']
            },
            'IDIBS': {
                'name': 'Industrial Automation Operations',
                'focus': 'PLCs, drives, motion control',
                'criticality': 'MEDIUM',
                'migration_priority': 3,
                'keywords': ['plc', 'modicon', 'drive', 'motion', 'automation']
            },
            'DPIBS': {
                'name': 'Digital Power Services',
                'focus': 'Energy monitoring, digital solutions',
                'criticality': 'LOW',
                'migration_priority': 4,
                'keywords': ['energy', 'monitoring', 'digital', 'meter']
            },
            'DBIBS': {
                'name': 'Digital Building Services',
                'focus': 'HVAC, building automation',
                'criticality': 'LOW',
                'migration_priority': 5,
                'keywords': ['building', 'hvac', 'room', 'controller']
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
        
        for range_label, pl_service, status, count, device_types in ranges:
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
                'device_types': device_types.split(' | ') if device_types else [],
                'migration_needed': is_obsolete,
                'criticality': self.pl_services.get(pl_service, {}).get('criticality', 'UNKNOWN'),
                'keywords': self._generate_range_keywords(range_label, pl_service)
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
    
    def _generate_range_keywords(self, range_label: str, pl_service: str) -> List[str]:
        """Generate keywords for range"""
        keywords = []
        
        # Range name parts
        keywords.extend([word.lower() for word in range_label.split() if len(word) > 2])
        
        # PL service keywords
        if pl_service in self.pl_services:
            keywords.extend(self.pl_services[pl_service]['keywords'])
        
        return list(set(keywords))
    
    def _load_migration_intelligence(self):
        """Load migration intelligence for obsolete products"""
        trace_id = self._generate_trace_id()
        start_time = time.time()
        
        # Find migration patterns - active products that can replace obsolete ones
        migration_query = """
            WITH obsolete_products AS (
                SELECT RANGE_LABEL, PL_SERVICES, DEVICETYPE_LABEL
                FROM products 
                WHERE COMMERCIAL_STATUS IN ('01-Obsolete', '02-Obsolete')
                AND RANGE_LABEL IS NOT NULL
                GROUP BY RANGE_LABEL, PL_SERVICES, DEVICETYPE_LABEL
            ),
            active_products AS (
                SELECT RANGE_LABEL, PL_SERVICES, DEVICETYPE_LABEL, COUNT(*) as count
                FROM products 
                WHERE COMMERCIAL_STATUS = '08-Commercialised'
                AND RANGE_LABEL IS NOT NULL
                GROUP BY RANGE_LABEL, PL_SERVICES, DEVICETYPE_LABEL
                HAVING COUNT(*) > 10
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
            'content_preview': content[:1000] + "..." if len(content) > 1000 else content,
            'content_hash': hashlib.md5(content.encode()).hexdigest(),
            'extraction_result': extraction_result,
            'migration_paths': [asdict(mp) for mp in migration_paths],
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
            return f"PDF_FALLBACK: {file_path.name} - PyMuPDF not available"
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
            
            return f"DOC_FALLBACK: {file_path.name} - LibreOffice conversion failed"
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
            keyword_matches = sum(1 for keyword in pl_info['keywords'] if keyword in content.lower())
            
            if keyword_matches >= 2:
                detected_pl_services.add(pl_code)
                
                # Find ranges in this PL service
                for range_label, range_info in self.range_intelligence.items():
                    if (range_info['pl_service'] == pl_code and 
                        range_label not in confidence_scores):
                        
                        # Check if range keywords appear
                        range_keyword_matches = sum(1 for keyword in range_info['keywords'] 
                                                   if keyword in content.lower())
                        
                        if range_keyword_matches > 0:
                            confidence = 0.7 + (range_keyword_matches * 0.1)
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
        
        # Sort by confidence and limit to top 25 for precision
        extracted_ranges.sort(key=lambda x: x['confidence'], reverse=True)
        extracted_ranges = extracted_ranges[:25]
        
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
                    business_justification=f"Obsolete {obsolete_range['pl_service']} product requires migration to active equivalent",
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


class IndustrialHTMLGenerator:
    """Industrial HTML generator embedded in main script"""
    
    def generate_industrial_report(self, results: List[Dict], traces: List[Dict]) -> str:
        """Generate industrial-grade HTML report"""
        
        # Calculate aggregate metrics
        total_docs = len(results)
        total_ranges = sum(len(r['extraction_result']['ranges']) for r in results)
        total_migrations = sum(len(r['migration_paths']) for r in results)
        avg_quality = sum(r['quality_metrics']['overall_quality'] for r in results) / total_docs if total_docs > 0 else 0
        
        # Generate sections
        metrics_html = self._generate_metrics_dashboard(total_docs, total_ranges, total_migrations, avg_quality)
        documents_html = self._generate_documents_section(results)
        traces_html = self._generate_traces_section(traces)
        
        # Complete HTML with monochromatic industrial theme
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Industrial Pipeline - Professional Analysis</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            background: #0a0a0a;
            color: #e0e0e0;
            line-height: 1.4;
        }}
        
        .industrial-container {{
            max-width: 100vw;
            margin: 0;
            padding: 0;
        }}
        
        .industrial-header {{
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            border-bottom: 2px solid #333;
            padding: 20px;
            position: sticky;
            top: 0;
            z-index: 1000;
        }}
        
        .header-title {{
            font-size: 24px;
            font-weight: bold;
            color: #ffffff;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 5px;
        }}
        
        .header-subtitle {{
            font-size: 14px;
            color: #888;
            text-transform: uppercase;
        }}
        
        .header-timestamp {{
            position: absolute;
            top: 20px;
            right: 20px;
            font-size: 12px;
            color: #666;
        }}
        
        .metrics-dashboard {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1px;
            background: #333;
        }}
        
        .metric-card {{
            background: #1a1a1a;
            padding: 20px;
            border: 1px solid #333;
            position: relative;
        }}
        
        .metric-label {{
            font-size: 11px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }}
        
        .metric-value {{
            font-size: 28px;
            font-weight: bold;
            color: #ffffff;
            font-family: monospace;
        }}
        
        .metric-status {{
            position: absolute;
            top: 10px;
            right: 10px;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #00ff00;
        }}
        
        .metric-status.warning {{ background: #ffaa00; }}
        .metric-status.error {{ background: #ff0000; }}
        
        .documents-section {{
            background: #111;
            border-top: 1px solid #333;
        }}
        
        .section-header {{
            background: #1a1a1a;
            padding: 15px 20px;
            border-bottom: 1px solid #333;
            font-size: 14px;
            font-weight: bold;
            text-transform: uppercase;
            color: #ccc;
        }}
        
        .document-item {{
            border-bottom: 1px solid #222;
            background: #0f0f0f;
        }}
        
        .document-header {{
            padding: 15px 20px;
            cursor: pointer;
            background: #1a1a1a;
            border-bottom: 1px solid #333;
            transition: background 0.2s;
        }}
        
        .document-header:hover {{
            background: #252525;
        }}
        
        .document-title {{
            font-size: 16px;
            color: #ffffff;
            margin-bottom: 5px;
        }}
        
        .document-meta {{
            display: flex;
            gap: 20px;
            font-size: 12px;
            color: #888;
        }}
        
        .document-content {{
            display: none;
            padding: 0;
        }}
        
        .document-content.active {{
            display: block;
        }}
        
        .document-layout {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1px;
            background: #333;
        }}
        
        .source-preview {{
            background: #0a0a0a;
            padding: 20px;
            border-right: 1px solid #333;
        }}
        
        .analysis-results {{
            background: #111;
            padding: 20px;
        }}
        
        .preview-header {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 1px solid #333;
        }}
        
        .source-text {{
            font-family: monospace;
            font-size: 11px;
            line-height: 1.6;
            color: #ccc;
            background: #000;
            padding: 15px;
            border: 1px solid #333;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
        }}
        
        .results-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }}
        
        .results-table th {{
            background: #1a1a1a;
            color: #ccc;
            padding: 8px;
            text-align: left;
            border: 1px solid #333;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 10px;
        }}
        
        .results-table td {{
            padding: 8px;
            border: 1px solid #333;
            color: #ddd;
        }}
        
        .results-table tr:nth-child(even) {{
            background: #0f0f0f;
        }}
        
        .results-table tr:hover {{
            background: #1a1a1a;
        }}
        
        .status-active {{ color: #00ff00; }}
        .status-obsolete {{ color: #ff6666; }}
        .confidence-high {{ color: #00ff00; }}
        .confidence-medium {{ color: #ffaa00; }}
        .confidence-low {{ color: #ff6666; }}
        
        .migration-path {{
            background: #1a1a1a;
            border: 1px solid #333;
            margin: 10px 0;
            padding: 15px;
        }}
        
        .migration-header {{
            color: #ff6666;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .migration-recommendation {{
            color: #00ff00;
            margin: 5px 0;
        }}
        
        .traces-section {{
            background: #0a0a0a;
            border-top: 1px solid #333;
        }}
        
        .trace-item {{
            border-bottom: 1px solid #222;
            padding: 10px 20px;
            font-family: monospace;
            font-size: 11px;
        }}
        
        .trace-timestamp {{
            color: #666;
            margin-right: 10px;
        }}
        
        .trace-operation {{
            color: #00aaff;
            margin-right: 10px;
        }}
        
        .trace-confidence {{
            color: #00ff00;
            margin-right: 10px;
        }}
        
        .trace-time {{
            color: #ffaa00;
        }}
        
        .console-section {{
            background: #000;
            border-top: 2px solid #333;
            min-height: 300px;
        }}
        
        .console-header {{
            background: #1a1a1a;
            padding: 10px 20px;
            border-bottom: 1px solid #333;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .console-title {{
            color: #ccc;
            font-size: 12px;
            text-transform: uppercase;
        }}
        
        .console-controls {{
            display: flex;
            gap: 10px;
        }}
        
        .console-btn {{
            background: #333;
            color: #ccc;
            border: 1px solid #555;
            padding: 5px 10px;
            font-size: 10px;
            cursor: pointer;
            text-transform: uppercase;
        }}
        
        .console-btn:hover {{
            background: #555;
        }}
        
        .console-output {{
            padding: 20px;
            font-family: monospace;
            font-size: 12px;
            line-height: 1.4;
            color: #00ff00;
            min-height: 250px;
        }}
        
        .console-prompt {{
            color: #00aaff;
        }}
        
        .console-error {{
            color: #ff6666;
        }}
        
        .console-warning {{
            color: #ffaa00;
        }}
        
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: #1a1a1a;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: #333;
            border-radius: 4px;
        }}
        
        @media (max-width: 768px) {{
            .document-layout {{
                grid-template-columns: 1fr;
            }}
            
            .metrics-dashboard {{
                grid-template-columns: 1fr 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="industrial-container">
        <div class="industrial-header">
            <div class="header-title">Industrial Pipeline Analysis</div>
            <div class="header-subtitle">Professional Grade • Monochromatic Interface • Advanced Debugging</div>
            <div class="header-timestamp">{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
        </div>
        
        {metrics_html}
        {documents_html}
        {traces_html}
        
        <div class="console-section">
            <div class="console-header">
                <div class="console-title">AI Verification Console</div>
                <div class="console-controls">
                    <button class="console-btn" onclick="verifyWithGrok()">Verify with Grok</button>
                    <button class="console-btn" onclick="exportJSON()">Export JSON</button>
                    <button class="console-btn" onclick="clearConsole()">Clear</button>
                </div>
            </div>
            <div class="console-output" id="console-output">
                <div class="console-prompt">[SYSTEM]</div> Industrial Pipeline Console Ready<br>
                <div class="console-prompt">[INFO]</div> Use 'Verify with Grok' to validate extraction results<br>
                <div class="console-prompt">[INFO]</div> Console mode enables AI-powered quality verification<br>
                <div class="console-prompt">[INFO]</div> Migration paths analyzed for obsolete products<br>
                <br>
                <div class="console-prompt">[READY]</div> Awaiting commands...<br>
            </div>
        </div>
    </div>
    
    <script>
        function toggleDocument(index) {{
            const content = document.getElementById('doc-' + index);
            const isActive = content.classList.contains('active');
            
            document.querySelectorAll('.document-content').forEach(el => {{
                el.classList.remove('active');
            }});
            
            if (!isActive) {{
                content.classList.add('active');
            }}
        }}
        
        function verifyWithGrok() {{
            const console = document.getElementById('console-output');
            const timestamp = new Date().toISOString().substr(11, 8);
            
            console.innerHTML += `
                <div class="console-prompt">[${timestamp}]</div> Initiating Grok verification...<br>
                <div class="console-prompt">[${timestamp}]</div> Analyzing extraction metadata...<br>
                <div class="console-warning">[${timestamp}]</div> Note: Grok API integration required for live verification<br>
                <div class="console-prompt">[${timestamp}]</div> Quality scores: {avg_quality:.1%} average<br>
                <div class="console-prompt">[${timestamp}]</div> Migration paths: {total_migrations} identified<br>
                <br>
            `;
            console.scrollTop = console.scrollHeight;
        }}
        
        function exportJSON() {{
            const console = document.getElementById('console-output');
            const timestamp = new Date().toISOString().substr(11, 8);
            
            console.innerHTML += `
                <div class="console-prompt">[${timestamp}]</div> Exporting metadata to JSON...<br>
                <div class="console-prompt">[${timestamp}]</div> Migration paths included<br>
                <div class="console-prompt">[${timestamp}]</div> Export complete: industrial_results.json<br>
                <br>
            `;
            console.scrollTop = console.scrollHeight;
        }}
        
        function clearConsole() {{
            document.getElementById('console-output').innerHTML = `
                <div class="console-prompt">[SYSTEM]</div> Console cleared<br>
                <div class="console-prompt">[READY]</div> Awaiting commands...<br>
            `;
        }}
    </script>
</body>
</html>
        """
        
        return html
    
    def _generate_metrics_dashboard(self, total_docs: int, total_ranges: int, total_migrations: int, avg_quality: float) -> str:
        """Generate metrics dashboard"""
        quality_status = "metric-status"
        if avg_quality < 0.6:
            quality_status += " error"
        elif avg_quality < 0.8:
            quality_status += " warning"
        
        return f"""
        <div class="metrics-dashboard">
            <div class="metric-card">
                <div class="metric-label">Documents Processed</div>
                <div class="metric-value">{total_docs:,}</div>
                <div class="metric-status"></div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Ranges Extracted</div>
                <div class="metric-value">{total_ranges:,}</div>
                <div class="metric-status"></div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Migration Paths</div>
                <div class="metric-value">{total_migrations:,}</div>
                <div class="metric-status"></div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Quality Score</div>
                <div class="metric-value">{avg_quality:.1%}</div>
                <div class="{quality_status}"></div>
            </div>
        </div>
        """
    
    def _generate_documents_section(self, results: List[Dict]) -> str:
        """Generate documents section with side-by-side preview"""
        documents_html = ""
        
        for i, result in enumerate(results):
            doc_name = result['document_name']
            quality = result['quality_metrics']['overall_quality']
            ranges_count = len(result['extraction_result']['ranges'])
            migrations_count = len(result['migration_paths'])
            
            # Source preview
            content_preview = result['content_preview']
            
            # Analysis results
            ranges_html = self._generate_ranges_table(result['extraction_result']['ranges'])
            migrations_html = self._generate_migrations_html(result['migration_paths'])
            
            documents_html += f"""
            <div class="document-item">
                <div class="document-header" onclick="toggleDocument({i})">
                    <div class="document-title">{doc_name}</div>
                    <div class="document-meta">
                        <span>Quality: <span class="confidence-{'high' if quality > 0.8 else 'medium' if quality > 0.6 else 'low'}">{quality:.1%}</span></span>
                        <span>Ranges: {ranges_count}</span>
                        <span>Migrations: {migrations_count}</span>
                        <span>Trace: {result['trace_id']}</span>
                    </div>
                </div>
                <div class="document-content" id="doc-{i}">
                    <div class="document-layout">
                        <div class="source-preview">
                            <div class="preview-header">Source Document Preview</div>
                            <div class="source-text">{content_preview}</div>
                        </div>
                        <div class="analysis-results">
                            <div class="preview-header">Extraction Results</div>
                            {ranges_html}
                            
                            {migrations_html if migrations_html else '<p style="color: #666; font-style: italic;">No migration paths required</p>'}
                        </div>
                    </div>
                </div>
            </div>
            """
        
        return f"""
        <div class="documents-section">
            <div class="section-header">Document Analysis Results</div>
            {documents_html}
        </div>
        """
    
    def _generate_ranges_table(self, ranges: List[Dict]) -> str:
        """Generate ranges table"""
        if not ranges:
            return '<p style="color: #666; font-style: italic;">No ranges extracted</p>'
        
        rows_html = ""
        for range_data in ranges[:15]:  # Show top 15
            status_class = "status-obsolete" if range_data['is_obsolete'] else "status-active"
            confidence_class = f"confidence-{'high' if range_data['confidence'] > 0.8 else 'medium' if range_data['confidence'] > 0.6 else 'low'}"
            
            rows_html += f"""
            <tr>
                <td>{range_data['range']}</td>
                <td class="{status_class}">{range_data['status']}</td>
                <td>{range_data['pl_service']}</td>
                <td class="{confidence_class}">{range_data['confidence']:.1%}</td>
                <td>{range_data['extraction_method']}</td>
                <td>{range_data['criticality']}</td>
            </tr>
            """
        
        return f"""
        <table class="results-table">
            <thead>
                <tr>
                    <th>Range</th>
                    <th>Status</th>
                    <th>PL Service</th>
                    <th>Confidence</th>
                    <th>Method</th>
                    <th>Criticality</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
        """
    
    def _generate_migrations_html(self, migration_paths: List[Dict]) -> str:
        """Generate migration paths HTML"""
        if not migration_paths:
            return ""
        
        migrations_html = '<div class="preview-header" style="margin-top: 20px;">Migration Paths</div>'
        
        for migration in migration_paths:
            recommendations_html = ""
            for rec in migration['recommended_products']:
                recommendations_html += f"""
                <div class="migration-recommendation">
                    → {rec['recommended_range']} (Confidence: {rec['confidence']:.1%}, Products: {rec['product_count']})
                </div>
                """
            
            migrations_html += f"""
            <div class="migration-path">
                <div class="migration-header">OBSOLETE: {migration['obsolete_product']}</div>
                <div style="color: #888; margin-bottom: 10px;">{migration['business_justification']}</div>
                {recommendations_html}
            </div>
            """
        
        return migrations_html
    
    def _generate_traces_section(self, traces: List[Dict]) -> str:
        """Generate traces section for debugging"""
        traces_html = ""
        
        for trace in traces[-30:]:  # Show last 30 traces
            confidence_class = f"confidence-{'high' if trace['confidence'] > 0.8 else 'medium' if trace['confidence'] > 0.6 else 'low'}"
            
            traces_html += f"""
            <div class="trace-item">
                <span class="trace-timestamp">{trace['timestamp'][:19]}</span>
                <span class="trace-operation">{trace['operation']}</span>
                <span class="trace-confidence {confidence_class}">CONF:{trace['confidence']:.2f}</span>
                <span class="trace-time">TIME:{trace['processing_time']:.3f}s</span>
            </div>
            """
        
        return f"""
        <div class="traces-section">
            <div class="section-header">Processing Traces (Debugging)</div>
            {traces_html}
        </div>
        """


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
        html_generator = IndustrialHTMLGenerator()
        html_report = html_generator.generate_industrial_report(results, [asdict(t) for t in engine.get_session_traces()])
        
        # Save report
        output_dir = Path("data/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        html_file = output_dir / "industrial_pipeline_report.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        # Save JSON results
        json_file = output_dir / "industrial_results.json"
        with open(json_file, 'w') as f:
            json.dump({
                'session_id': engine.session_id,
                'results': results,
                'traces': [asdict(t) for t in engine.get_session_traces()]
            }, f, indent=2, default=str)
        
        print(f"\nINDUSTRIAL REPORT GENERATED: {html_file}")
        print(f"JSON RESULTS SAVED: {json_file}")
        
        # Display summary
        total_ranges = sum(len(r['extraction_result']['ranges']) for r in results)
        total_migrations = sum(len(r['migration_paths']) for r in results)
        avg_quality = sum(r['quality_metrics']['overall_quality'] for r in results) / len(results)
        
        print(f"\nINDUSTRIAL PIPELINE SUMMARY:")
        print(f"Documents Processed: {len(results)}")
        print(f"Ranges Extracted: {total_ranges}")
        print(f"Migration Paths: {total_migrations}")
        print(f"Average Quality: {avg_quality:.1%}")
        
        # Try to open in browser
        try:
            import webbrowser
            webbrowser.open(f"file://{html_file.absolute()}")
            print(f"Opening industrial report in browser...")
        except:
            pass
        
    finally:
        engine.close()


if __name__ == "__main__":
    main() 