#!/usr/bin/env python3
"""
Intelligent Modular Pipeline with Smart Pre-filtering
Uses document path/filename intelligence to reduce IBcatalogue search space
No hardcoded fallbacks - pure discovery-based processing
"""

import sys
import time
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
import random
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from migrate_to_duckdb import FastIBcatalogueService

@dataclass
class DocumentContext:
    """Document context with intelligent pre-filtering hints"""
    file_path: Path
    file_name: str
    voltage_level: Optional[str] = None  # 'MV', 'LV', 'HV'
    product_category: Optional[str] = None  # 'protection', 'switchgear', 'automation'
    pl_services_hint: Optional[str] = None  # 'PSIBS', 'PPIBS', 'DPIBS'
    business_context: List[str] = None
    confidence_score: float = 0.0

@dataclass
class ProcessingResult:
    """Structured processing result"""
    success: bool
    content: str = ""
    context: Optional[DocumentContext] = None
    ranges: List[str] = None
    products: List[Dict[str, Any]] = None
    product_count: int = 0
    processing_time_ms: float = 0.0
    search_space_reduction: float = 0.0  # Percentage of database pre-filtered

class IntelligentContextAnalyzer:
    """Analyzes document context to provide smart pre-filtering hints"""
    
    def __init__(self):
        # Voltage level indicators
        self.voltage_patterns = {
            'MV': [
                'switchgear', 'rmu', 'ring main', 'mv', 'medium voltage',
                '11kv', '12kv', '17.5kv', '24kv', '36kv', 'pix', 'sm6', 'rm6'
            ],
            'LV': [
                'acb', 'air circuit breaker', 'mccb', 'mcb', 'contactor',
                'overload', 'tesys', 'compact ns', 'masterpact', 'lv', 'low voltage',
                '400v', '690v', '230v'
            ],
            'HV': [
                'hv', 'high voltage', '72kv', '145kv', 'gas insulated',
                'gis', 'transmission'
            ]
        }
        
        # Product category patterns
        self.category_patterns = {
            'protection': [
                'relay', 'protection', 'sepam', 'micrologic', 'vigi',
                'differential', 'overcurrent', 'distance'
            ],
            'switchgear': [
                'switchgear', 'panel', 'cubicle', 'enclosure', 'cabinet',
                'mcc', 'motor control center', 'distribution board'
            ],
            'automation': [
                'plc', 'hmi', 'scada', 'controller', 'automation',
                'modicon', 'schneider electric ecosystem'
            ],
            'power_electronics': [
                'inverter', 'drive', 'ups', 'rectifier', 'converter',
                'altivar', 'galaxy', 'symmetra'
            ]
        }
        
        # PL_SERVICES mapping based on IBcatalogue analysis
        self.pl_services_mapping = {
            'PSIBS': ['MV', 'switchgear', 'transmission', 'power_systems'],
            'PPIBS': ['LV', 'protection', 'power_products'],
            'DPIBS': ['protection', 'relay', 'digital_protection'],
            'IDIBS': ['automation', 'industrial'],
            'SPIBS': ['ups', 'power_electronics', 'secure_power'],
            'IDPAS': ['automation', 'process'],
            'PPIBS': ['low_voltage', 'distribution']
        }
        
        # Business context indicators
        self.business_patterns = {
            'obsolescence': ['obsolet', 'discontinu', 'end', 'phase', 'withdraw', 'eol'],
            'modernization': ['modern', 'upgrade', 'migrat', 'replace', 'new'],
            'communication': ['communication', 'letter', 'notice', 'announcement'],
            'service': ['service', 'maintenance', 'support', 'repair']
        }
    
    def analyze_document_context(self, file_path: Path) -> DocumentContext:
        """Analyze document path and filename for intelligent context"""
        
        # Get full path components for analysis
        path_parts = [part.lower() for part in file_path.parts]
        filename_lower = file_path.name.lower()
        stem_lower = file_path.stem.lower()
        
        # Combine all text for analysis
        analysis_text = " ".join(path_parts + [filename_lower])
        
        context = DocumentContext(
            file_path=file_path,
            file_name=file_path.name,
            business_context=[]
        )
        
        # Analyze voltage level
        context.voltage_level = self._detect_voltage_level(analysis_text)
        
        # Analyze product category  
        context.product_category = self._detect_product_category(analysis_text)
        
        # Determine PL_SERVICES hint
        context.pl_services_hint = self._determine_pl_services(
            context.voltage_level, 
            context.product_category, 
            analysis_text
        )
        
        # Extract business context
        context.business_context = self._extract_business_context(analysis_text)
        
        # Calculate confidence score
        context.confidence_score = self._calculate_confidence(context)
        
        return context
    
    def _detect_voltage_level(self, text: str) -> Optional[str]:
        """Detect voltage level from text"""
        for voltage, patterns in self.voltage_patterns.items():
            if any(pattern in text for pattern in patterns):
                return voltage
        return None
    
    def _detect_product_category(self, text: str) -> Optional[str]:
        """Detect product category from text"""
        category_scores = {}
        
        for category, patterns in self.category_patterns.items():
            score = sum(1 for pattern in patterns if pattern in text)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            return max(category_scores, key=category_scores.get)
        return None
    
    def _determine_pl_services(self, voltage_level: str, product_category: str, text: str) -> Optional[str]:
        """Determine most likely PL_SERVICES category"""
        
        # Direct mapping based on voltage and category
        if voltage_level == 'MV' or 'switchgear' in text:
            return 'PSIBS'  # Power Systems IBS
        
        if voltage_level == 'LV' and product_category in ['protection', None]:
            return 'PPIBS'  # Power Products IBS
            
        if product_category == 'protection' or any(term in text for term in ['relay', 'sepam', 'protection']):
            return 'DPIBS'  # Digital Power IBS
            
        if product_category == 'automation' or any(term in text for term in ['plc', 'automation', 'scada']):
            return 'IDIBS'  # Industrial IBS
            
        if any(term in text for term in ['ups', 'galaxy', 'power', 'backup']):
            return 'SPIBS'  # Secure Power IBS
        
        # Default to most common if uncertain
        return 'PPIBS'  # Power Products IBS (largest category)
    
    def _extract_business_context(self, text: str) -> List[str]:
        """Extract business context indicators"""
        contexts = []
        for context_type, patterns in self.business_patterns.items():
            if any(pattern in text for pattern in patterns):
                contexts.append(context_type)
        return contexts
    
    def _calculate_confidence(self, context: DocumentContext) -> float:
        """Calculate confidence score for the context analysis"""
        score = 0.0
        
        if context.voltage_level:
            score += 0.3
        if context.product_category:
            score += 0.3
        if context.pl_services_hint:
            score += 0.2
        if context.business_context:
            score += 0.2
            
        return min(score, 1.0)

class DocumentProcessor:
    """Modular document processor"""
    
    def process_document(self, file_path: Path) -> Dict[str, Any]:
        """Process document with basic text extraction"""
        
        try:
            content = self._extract_text(file_path)
            
            if content and len(content.strip()) > 10:
                return {
                    'success': True,
                    'content': content,
                    'stats': {
                        'characters': len(content),
                        'words': len(content.split()),
                        'paragraphs': len([p for p in content.split('\n') if p.strip()])
                    }
                }
            else:
                return {'success': False, 'content': '', 'error': 'No meaningful content extracted'}
                
        except Exception as e:
            return {'success': False, 'content': '', 'error': str(e)}
    
    def _extract_text(self, file_path: Path) -> str:
        """Extract text using available methods"""
        file_ext = file_path.suffix.lower()
        
        if file_ext == '.docx':
            return self._extract_docx(file_path)
        elif file_ext == '.pdf':
            return self._extract_pdf(file_path)
        else:
            return ""
    
    def _extract_docx(self, file_path: Path) -> str:
        """Extract from DOCX"""
        try:
            import docx
            doc = docx.Document(file_path)
            content = ""
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text:
                    content += text + "\n"
            return content.strip()
        except:
            return ""
    
    def _extract_pdf(self, file_path: Path) -> str:
        """Extract from PDF"""
        try:
            import PyPDF2
            content = ""
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    content += page.extract_text() + "\n"
            return content.strip()
        except:
            return ""

class IntelligentXAIService:
    """XAI service with context-aware prompting"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def extract_ranges(self, content: str, context: DocumentContext) -> List[str]:
        """Extract ranges with context-aware prompting"""
        
        try:
            import requests
            
            # Build context-aware prompt
            prompt = self._build_context_prompt(content, context)
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messages": [{"role": "user", "content": prompt}],
                "model": "grok-beta",
                "temperature": 0.1,
                "max_tokens": 500
            }
            
            response = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content_resp = result['choices'][0]['message']['content']
                
                try:
                    ranges = json.loads(content_resp)
                    if isinstance(ranges, list):
                        return [r.strip() for r in ranges if r and r.strip()]
                except:
                    # Try to extract ranges from text response
                    return self._extract_ranges_from_text(content_resp)
                    
        except Exception as e:
            print(f"    ⚠️  AI extraction failed: {e}")
        
        return []  # No fallback - pure discovery
    
    def _build_context_prompt(self, content: str, context: DocumentContext) -> str:
        """Build context-aware prompt"""
        
        context_hints = []
        if context.voltage_level:
            context_hints.append(f"This appears to be a {context.voltage_level} (voltage level) document")
        if context.product_category:
            context_hints.append(f"Product category seems to be {context.product_category}")
        if context.business_context:
            context_hints.append(f"Business context: {', '.join(context.business_context)}")
        
        context_info = "\n".join(context_hints) if context_hints else "No specific context detected"
        
        return f"""
Analyze this Schneider Electric document and extract the specific product ranges mentioned.

DOCUMENT CONTEXT ANALYSIS:
{context_info}

DOCUMENT: {context.file_name}
CONTENT: {content}

INSTRUCTIONS:
1. Extract ONLY product ranges that are explicitly mentioned in the document text
2. Focus on actual product family names, not generic terms
3. Do NOT infer or assume ranges based on filename or context
4. Return a JSON array of range names

EXAMPLES of valid ranges: ["PIX", "SEPAM", "TeSys D", "Galaxy", "Masterpact"]

Return only the JSON array, nothing else.
"""
    
    def _extract_ranges_from_text(self, text: str) -> List[str]:
        """Extract ranges from text response if JSON parsing fails"""
        ranges = []
        
        # Look for quoted strings
        import re
        quoted_matches = re.findall(r'["\']([^"\']+)["\']', text)
        ranges.extend(quoted_matches)
        
        # Look for bracketed lists
        bracket_matches = re.findall(r'\[(.*?)\]', text)
        for match in bracket_matches:
            items = [item.strip().strip('"\'') for item in match.split(',')]
            ranges.extend(items)
        
        return [r.strip() for r in ranges if r and r.strip() and len(r) > 1]

class IntelligentDuckDBService:
    """Intelligent DuckDB service with pre-filtering"""
    
    def __init__(self, db_path: str = "data/IBcatalogue.duckdb"):
        self.fast_service = FastIBcatalogueService(db_path)
    
    def find_products_with_context(self, ranges: List[str], context: DocumentContext) -> List[Dict[str, Any]]:
        """Find products with intelligent pre-filtering"""
        
        if not ranges:
            return []
        
        # Build pre-filter conditions based on context
        where_conditions = []
        params = []
        
        # Add PL_SERVICES filter if we have a hint
        if context.pl_services_hint:
            where_conditions.append("PL_SERVICES = ?")
            params.append(context.pl_services_hint)
        
        # Add voltage level hints through device type filtering
        if context.voltage_level == 'MV':
            where_conditions.append("(UPPER(DEVICETYPE_LABEL) LIKE '%MV%' OR UPPER(RANGE_LABEL) LIKE '%MV%')")
        elif context.voltage_level == 'LV':
            where_conditions.append("(UPPER(DEVICETYPE_LABEL) LIKE '%LV%' OR UPPER(RANGE_LABEL) LIKE '%LV%')")
        
        # Build the query with pre-filtering
        base_query = "SELECT * FROM products"
        pre_filter_query = ""
        
        if where_conditions:
            pre_filter_query = " WHERE " + " AND ".join(where_conditions)
        
        # Add range matching
        range_conditions = []
        for range_name in ranges:
            range_conditions.extend([
                "UPPER(RANGE_LABEL) = UPPER(?)",
                "UPPER(RANGE_LABEL) LIKE UPPER(?)",
                "UPPER(RANGE_LABEL) LIKE UPPER(?)"
            ])
            params.extend([range_name, f'%{range_name}%', f'{range_name}%'])
        
        if range_conditions:
            range_filter = " (" + " OR ".join(range_conditions) + ")"
            if pre_filter_query:
                pre_filter_query += " AND" + range_filter
            else:
                pre_filter_query = " WHERE" + range_filter
        
        final_query = base_query + pre_filter_query + " ORDER BY RANGE_LABEL, PRODUCT_IDENTIFIER"
        
        return self.fast_service.conn.execute(final_query, params).fetchdf().to_dict('records')
    
    def calculate_search_space_reduction(self, context: DocumentContext) -> float:
        """Calculate how much we reduced the search space"""
        
        # Total products
        total_products = self.fast_service.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        
        # Build pre-filter query
        where_conditions = []
        params = []
        
        if context.pl_services_hint:
            where_conditions.append("PL_SERVICES = ?")
            params.append(context.pl_services_hint)
        
        if context.voltage_level == 'MV':
            where_conditions.append("(UPPER(DEVICETYPE_LABEL) LIKE '%MV%' OR UPPER(RANGE_LABEL) LIKE '%MV%')")
        elif context.voltage_level == 'LV':
            where_conditions.append("(UPPER(DEVICETYPE_LABEL) LIKE '%LV%' OR UPPER(RANGE_LABEL) LIKE '%LV%')")
        
        if where_conditions:
            filtered_query = "SELECT COUNT(*) FROM products WHERE " + " AND ".join(where_conditions)
            filtered_products = self.fast_service.conn.execute(filtered_query, params).fetchone()[0]
            reduction = (1 - filtered_products / total_products) * 100
            return reduction
        
        return 0.0
    
    def close(self):
        """Close connections"""
        self.fast_service.close()

class IntelligentModularPipeline:
    """Main intelligent modular pipeline"""
    
    def __init__(self):
        self.context_analyzer = IntelligentContextAnalyzer()
        self.doc_processor = DocumentProcessor()
        self.xai_service = IntelligentXAIService("xai-RPhTjf3SzTbm11ZKcpFV0hsOqVTSj8QUbTFUhUrrQWaE")
        self.db_service = IntelligentDuckDBService()
        self.output_dir = Path("data/output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def process_documents(self, num_docs: int = 5) -> List[ProcessingResult]:
        """Process documents with intelligent modular approach"""
        
        print("🧠 INTELLIGENT MODULAR PIPELINE WITH SMART PRE-FILTERING")
        print("=" * 80)
        
        # Find documents
        docs_dir = Path("data/input/letters")
        doc_files = []
        for pattern in ["*.doc*", "*.pdf"]:
            doc_files.extend(docs_dir.glob(pattern))
            doc_files.extend(docs_dir.glob(f"*/{pattern}"))
            doc_files.extend(docs_dir.glob(f"*/*/{pattern}"))
        
        if not doc_files:
            print("❌ No documents found")
            return []
        
        # Select random documents
        selected_docs = random.sample(doc_files, min(num_docs, len(doc_files)))
        print(f"📄 Processing {len(selected_docs)} documents with intelligent pre-filtering")
        
        results = []
        
        for i, doc_file in enumerate(selected_docs, 1):
            print(f"\n🔄 Document {i}/{len(selected_docs)}")
            start_time = time.time()
            
            # 1. Analyze document context
            print(f"  🧠 Context analysis...")
            context = self.context_analyzer.analyze_document_context(doc_file)
            print(f"    📊 Voltage: {context.voltage_level or 'Unknown'}")
            print(f"    🏷️  Category: {context.product_category or 'Unknown'}")
            print(f"    🎯 PL_SERVICES hint: {context.pl_services_hint or 'None'}")
            print(f"    📈 Confidence: {context.confidence_score:.2f}")
            
            # 2. Process document
            print(f"  📄 Text extraction...")
            doc_result = self.doc_processor.process_document(doc_file)
            
            if not doc_result['success']:
                print(f"    ❌ Failed: {doc_result.get('error', 'Unknown error')}")
                results.append(ProcessingResult(
                    success=False,
                    context=context,
                    ranges=[],
                    products=[],
                    processing_time_ms=(time.time() - start_time) * 1000
                ))
                continue
            
            print(f"    ✅ Extracted: {len(doc_result['content'])} characters")
            
            # 3. Extract ranges with context
            print(f"  🤖 AI range extraction...")
            ranges = self.xai_service.extract_ranges(doc_result['content'], context)
            print(f"    ✅ Ranges found: {ranges}")
            
            # 4. Intelligent database search
            print(f"  🚀 Intelligent DuckDB search...")
            search_reduction = self.db_service.calculate_search_space_reduction(context)
            print(f"    📉 Search space reduced by: {search_reduction:.1f}%")
            
            products = self.db_service.find_products_with_context(ranges, context)
            processing_time = time.time() - start_time
            
            print(f"    ✅ Products found: {len(products)}")
            print(f"    ⏱️  Total time: {processing_time*1000:.1f}ms")
            
            # Create result
            result = ProcessingResult(
                success=True,
                content=doc_result['content'],
                context=context,
                ranges=ranges,
                products=products,
                product_count=len(products),
                processing_time_ms=processing_time * 1000,
                search_space_reduction=search_reduction
            )
            
            results.append(result)
        
        return results
    
    def generate_intelligence_report(self, results: List[ProcessingResult]) -> str:
        """Generate intelligent analysis report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Calculate intelligence metrics
        total_docs = len(results)
        successful_docs = len([r for r in results if r.success])
        total_products = sum(r.product_count for r in results if r.success)
        avg_reduction = sum(r.search_space_reduction for r in results if r.success) / max(successful_docs, 1)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Intelligent Modular Pipeline - {timestamp}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .intelligence-metrics {{
            background: #f8f9fa;
            padding: 30px;
            border-bottom: 1px solid #e9ecef;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            border-left: 4px solid #3498db;
        }}
        .metric-card h3 {{
            margin: 0;
            color: #3498db;
            font-size: 2em;
        }}
        .metric-card p {{
            margin: 5px 0 0 0;
            color: #6c757d;
        }}
        .results-section {{
            padding: 30px;
        }}
        .document-card {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 4px solid #27ae60;
        }}
        .context-analysis {{
            background: #e3f2fd;
            padding: 15px;
            border-radius: 6px;
            margin: 15px 0;
        }}
        .intelligence-score {{
            background: #e8f5e8;
            color: #155724;
            padding: 5px 10px;
            border-radius: 15px;
            font-weight: bold;
            display: inline-block;
        }}
        .products-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            font-size: 0.9em;
        }}
        .products-table th,
        .products-table td {{
            padding: 10px;
            border: 1px solid #ddd;
            text-align: left;
        }}
        .products-table th {{
            background: #3498db;
            color: white;
        }}
        .products-table tr:hover {{
            background: #f8f9fa;
        }}
        .reduction-badge {{
            background: #28a745;
            color: white;
            padding: 3px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 Intelligent Modular Pipeline</h1>
            <p>Smart Pre-filtering with Context Analysis</p>
            <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        
        <div class="intelligence-metrics">
            <h2>🎯 Intelligence Metrics</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <h3>{total_docs}</h3>
                    <p>Documents Analyzed</p>
                </div>
                <div class="metric-card">
                    <h3>{successful_docs}</h3>
                    <p>Successful Extractions</p>
                </div>
                <div class="metric-card">
                    <h3>{total_products:,}</h3>
                    <p>Products Found</p>
                </div>
                <div class="metric-card">
                    <h3>{avg_reduction:.1f}%</h3>
                    <p>Avg Search Reduction</p>
                </div>
            </div>
        </div>
        
        <div class="results-section">
            <h2>📊 Intelligent Processing Results</h2>"""
        
        for i, result in enumerate(results, 1):
            if result.success:
                context = result.context
                html += f"""
            <div class="document-card">
                <h3>📄 Document {i}: {context.file_name}</h3>
                
                <div class="context-analysis">
                    <h4>🧠 Context Intelligence Analysis</h4>
                    <p><strong>Voltage Level:</strong> {context.voltage_level or 'Not detected'}</p>
                    <p><strong>Product Category:</strong> {context.product_category or 'Not detected'}</p>
                    <p><strong>PL_SERVICES Hint:</strong> {context.pl_services_hint or 'None'}</p>
                    <p><strong>Business Context:</strong> {', '.join(context.business_context) if context.business_context else 'None'}</p>
                    <p><strong>Intelligence Score:</strong> 
                        <span class="intelligence-score">{context.confidence_score:.2f}</span>
                    </p>
                    <p><strong>Search Space Reduction:</strong> 
                        <span class="reduction-badge">{result.search_space_reduction:.1f}%</span>
                    </p>
                </div>
                
                <p><strong>AI-Extracted Ranges:</strong> {', '.join(result.ranges) if result.ranges else 'None'}</p>
                <p><strong>Products Found:</strong> {result.product_count:,}</p>
                <p><strong>Processing Time:</strong> {result.processing_time_ms:.1f}ms</p>
                
                {self._generate_products_table(result.products, i) if result.products else '<p><em>No products found</em></p>'}
            </div>"""
            else:
                html += f"""
            <div class="document-card" style="border-left-color: #e74c3c;">
                <h3>📄 Document {i}: {result.context.file_name}</h3>
                <p style="color: #e74c3c;"><strong>❌ Processing failed</strong></p>
            </div>"""
        
        html += """
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def _generate_products_table(self, products: List[Dict[str, Any]], doc_index: int) -> str:
        """Generate products table HTML"""
        if not products:
            return ""
        
        # Show first 20 products
        display_products = products[:20]
        
        html = f"""
                <table class="products-table">
                    <thead>
                        <tr>
                            <th>Product Code</th>
                            <th>Description</th>
                            <th>Range</th>
                            <th>PL_SERVICES</th>
                            <th>Status</th>
                            <th>Business Unit</th>
                        </tr>
                    </thead>
                    <tbody>"""
        
        for product in display_products:
            html += f"""
                        <tr>
                            <td><strong>{product.get('PRODUCT_IDENTIFIER', '')}</strong></td>
                            <td>{product.get('PRODUCT_DESCRIPTION', '')[:50]}...</td>
                            <td>{product.get('RANGE_LABEL', '')}</td>
                            <td>{product.get('PL_SERVICES', '')}</td>
                            <td>{product.get('COMMERCIAL_STATUS', '')}</td>
                            <td>{product.get('BU_LABEL', '')}</td>
                        </tr>"""
        
        if len(products) > 20:
            html += f"""
                        <tr>
                            <td colspan="6" style="text-align: center; font-style: italic; color: #666;">
                                ... and {len(products) - 20} more products
                            </td>
                        </tr>"""
        
        html += """
                    </tbody>
                </table>"""
        
        return html
    
    def run_intelligent_pipeline(self):
        """Run the intelligent modular pipeline"""
        # Process documents
        results = self.process_documents(5)
        
        # Generate report
        html_content = self.generate_intelligence_report(results)
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"Intelligent_Modular_Pipeline_{timestamp}.html"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n🏆 INTELLIGENT MODULAR PIPELINE COMPLETE")
        print(f"📊 Documents processed: {len(results)}")
        print(f"✅ Successful extractions: {len([r for r in results if r.success])}")
        print(f"🎯 Total products found: {sum(r.product_count for r in results if r.success):,}")
        
        if results:
            avg_reduction = sum(r.search_space_reduction for r in results if r.success) / max(len([r for r in results if r.success]), 1)
            print(f"📉 Average search space reduction: {avg_reduction:.1f}%")
        
        print(f"📁 Report saved: {report_path}")
        
        return report_path
    
    def close(self):
        """Close connections"""
        self.db_service.close()

if __name__ == "__main__":
    pipeline = IntelligentModularPipeline()
    try:
        pipeline.run_intelligent_pipeline()
    finally:
        pipeline.close() 