#!/usr/bin/env python3
"""
Comprehensive DuckDB Database Analysis
Analyzes structure, content, hierarchies, and patterns for better semantic search
"""

import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter
import pandas as pd
import duckdb
import numpy as np

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))


class ComprehensiveDatabaseAnalyzer:
    """Comprehensive analyzer for IBcatalogue DuckDB database"""
    
    def __init__(self, db_path: str = "data/IBcatalogue.duckdb"):
        """Initialize analyzer with database path"""
        self.db_path = db_path
        self.conn = None
        self.analysis_results = {}
        
    def connect(self):
        """Connect to DuckDB database"""
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"DuckDB file not found: {self.db_path}")
        
        self.conn = duckdb.connect(self.db_path)
        print(f"✅ Connected to DuckDB: {self.db_path}")
        
    def analyze_database_structure(self) -> Dict[str, Any]:
        """Analyze database structure and schema"""
        print("\n🏗️ ANALYZING DATABASE STRUCTURE")
        print("=" * 60)
        
        structure_analysis = {}
        
        # Get tables
        tables = self.conn.execute("SHOW TABLES").fetchall()
        structure_analysis['tables'] = [table[0] for table in tables]
        print(f"📊 Tables found: {structure_analysis['tables']}")
        
        # Analyze products table schema
        schema = self.conn.execute("DESCRIBE products").fetchall()
        structure_analysis['schema'] = []
        
        print(f"\n📋 PRODUCTS TABLE SCHEMA ({len(schema)} columns):")
        print("-" * 80)
        print(f"{'#':<3} {'Column Name':<30} {'Data Type':<15} {'Nullable':<8} {'Key':<5}")
        print("-" * 80)
        
        for i, (col_name, data_type, nullable, key, default, extra) in enumerate(schema):
            structure_analysis['schema'].append({
                'column_name': col_name,
                'data_type': data_type,
                'nullable': nullable,
                'key': key,
                'default': default,
                'extra': extra
            })
            print(f"{i+1:<3} {col_name:<30} {data_type:<15} {nullable:<8} {key or '':<5}")
        
        # Get indexes
        try:
            indexes_query = """
                SELECT name, sql 
                FROM sqlite_master 
                WHERE type = 'index' AND tbl_name = 'products'
            """
            indexes = self.conn.execute(indexes_query).fetchall()
            structure_analysis['indexes'] = [{'name': idx[0], 'sql': idx[1]} for idx in indexes]
            
            print(f"\n🔍 INDEXES ({len(indexes)} found):")
            for idx_name, idx_sql in indexes:
                print(f"  - {idx_name}")
                if idx_sql:
                    print(f"    SQL: {idx_sql}")
        except Exception as e:
            print(f"⚠️ Could not retrieve index information: {e}")
            structure_analysis['indexes'] = []
        
        # Database statistics
        db_size = Path(self.db_path).stat().st_size / (1024 * 1024)  # MB
        structure_analysis['database_size_mb'] = round(db_size, 2)
        
        row_count = self.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        structure_analysis['total_rows'] = row_count
        
        print(f"\n📊 DATABASE STATISTICS:")
        print(f"  - Database Size: {db_size:.2f} MB")
        print(f"  - Total Products: {row_count:,}")
        
        self.analysis_results['structure'] = structure_analysis
        return structure_analysis
    
    def analyze_data_content(self) -> Dict[str, Any]:
        """Analyze data content and distributions"""
        print("\n📊 ANALYZING DATA CONTENT & DISTRIBUTIONS")
        print("=" * 60)
        
        content_analysis = {}
        
        # Get sample data
        sample_data = self.conn.execute("SELECT * FROM products LIMIT 5").fetchdf()
        content_analysis['sample_data'] = sample_data.to_dict('records')
        
        print("📝 SAMPLE DATA (first 5 rows):")
        # Display key columns only for readability
        key_cols = ['PRODUCT_IDENTIFIER', 'RANGE_LABEL', 'BRAND_LABEL', 'COMMERCIAL_STATUS']
        available_cols = [col for col in key_cols if col in sample_data.columns]
        if available_cols:
            print(sample_data[available_cols].to_string())
        else:
            print("First few columns:")
            print(sample_data.iloc[:, :5].to_string())
        
        # Analyze key columns
        key_columns = [
            'RANGE_LABEL', 'SUBRANGE_LABEL', 'PRODUCT_IDENTIFIER', 
            'PRODUCT_DESCRIPTION', 'COMMERCIAL_STATUS', 'BRAND_LABEL',
            'BU_LABEL', 'PL_SERVICES', 'DEVICETYPE_LABEL'
        ]
        
        content_analysis['column_analysis'] = {}
        
        for column in key_columns:
            try:
                print(f"\n🔍 ANALYZING COLUMN: {column}")
                print("-" * 40)
                
                # Basic stats
                total_count = self.conn.execute(f"SELECT COUNT(*) FROM products").fetchone()[0]
                non_null_count = self.conn.execute(f"SELECT COUNT({column}) FROM products WHERE {column} IS NOT NULL").fetchone()[0]
                unique_count = self.conn.execute(f"SELECT COUNT(DISTINCT {column}) FROM products WHERE {column} IS NOT NULL").fetchone()[0]
                
                null_percentage = ((total_count - non_null_count) / total_count) * 100
                uniqueness = (unique_count / non_null_count) * 100 if non_null_count > 0 else 0
                
                # Top values
                top_values_query = f"""
                    SELECT {column}, COUNT(*) as count 
                    FROM products 
                    WHERE {column} IS NOT NULL 
                    GROUP BY {column} 
                    ORDER BY count DESC 
                    LIMIT 10
                """
                top_values = self.conn.execute(top_values_query).fetchall()
                
                column_stats = {
                    'total_count': total_count,
                    'non_null_count': non_null_count,
                    'unique_count': unique_count,
                    'null_percentage': round(null_percentage, 2),
                    'uniqueness_percentage': round(uniqueness, 2),
                    'top_values': [{'value': val, 'count': count} for val, count in top_values]
                }
                
                content_analysis['column_analysis'][column] = column_stats
                
                print(f"  Total Count: {total_count:,}")
                print(f"  Non-null: {non_null_count:,} ({100-null_percentage:.1f}%)")
                print(f"  Unique Values: {unique_count:,} ({uniqueness:.1f}% unique)")
                print(f"  Top 5 Values:")
                for val, count in top_values[:5]:
                    percentage = (count / non_null_count) * 100
                    print(f"    {val}: {count:,} ({percentage:.1f}%)")
                    
            except Exception as e:
                print(f"  ⚠️ Error analyzing {column}: {e}")
                content_analysis['column_analysis'][column] = {'error': str(e)}
        
        self.analysis_results['content'] = content_analysis
        return content_analysis
    
    def analyze_product_hierarchies(self) -> Dict[str, Any]:
        """Analyze product hierarchies and relationships"""
        print("\n🌳 ANALYZING PRODUCT HIERARCHIES & RELATIONSHIPS")
        print("=" * 60)
        
        hierarchy_analysis = {}
        
        # Brand hierarchy
        print("\n🏢 BRAND HIERARCHY:")
        brand_hierarchy_query = """
            SELECT 
                BRAND_LABEL,
                COUNT(*) as product_count,
                COUNT(DISTINCT RANGE_LABEL) as range_count,
                COUNT(DISTINCT BU_LABEL) as bu_count
            FROM products 
            WHERE BRAND_LABEL IS NOT NULL
            GROUP BY BRAND_LABEL 
            ORDER BY product_count DESC
        """
        brand_hierarchy = self.conn.execute(brand_hierarchy_query).fetchall()
        hierarchy_analysis['brand_hierarchy'] = [
            {
                'brand': brand,
                'product_count': prod_count,
                'range_count': range_count,
                'bu_count': bu_count
            }
            for brand, prod_count, range_count, bu_count in brand_hierarchy
        ]
        
        print(f"{'Brand':<30} {'Products':<10} {'Ranges':<8} {'BUs':<5}")
        print("-" * 55)
        for brand, prod_count, range_count, bu_count in brand_hierarchy[:10]:
            print(f"{brand:<30} {prod_count:<10,} {range_count:<8} {bu_count:<5}")
        
        # Range hierarchy
        print("\n📦 RANGE HIERARCHY (Top 20):")
        range_hierarchy_query = """
            SELECT 
                RANGE_LABEL,
                COUNT(*) as product_count,
                COUNT(DISTINCT SUBRANGE_LABEL) as subrange_count,
                COUNT(DISTINCT COMMERCIAL_STATUS) as status_count,
                BRAND_LABEL
            FROM products 
            WHERE RANGE_LABEL IS NOT NULL
            GROUP BY RANGE_LABEL, BRAND_LABEL
            ORDER BY product_count DESC
            LIMIT 20
        """
        range_hierarchy = self.conn.execute(range_hierarchy_query).fetchall()
        hierarchy_analysis['range_hierarchy'] = [
            {
                'range': range_name,
                'product_count': prod_count,
                'subrange_count': sub_count,
                'status_count': status_count,
                'brand': brand
            }
            for range_name, prod_count, sub_count, status_count, brand in range_hierarchy
        ]
        
        print(f"{'Range':<25} {'Products':<10} {'Subranges':<10} {'Brand':<20}")
        print("-" * 70)
        for range_name, prod_count, sub_count, status_count, brand in range_hierarchy:
            print(f"{range_name:<25} {prod_count:<10,} {sub_count:<10} {brand or 'N/A':<20}")
        
        # Business Unit hierarchy
        print("\n🏭 BUSINESS UNIT HIERARCHY:")
        bu_hierarchy_query = """
            SELECT 
                BU_LABEL,
                COUNT(*) as product_count,
                COUNT(DISTINCT RANGE_LABEL) as range_count,
                COUNT(DISTINCT PL_SERVICES) as pl_services_count
            FROM products 
            WHERE BU_LABEL IS NOT NULL
            GROUP BY BU_LABEL 
            ORDER BY product_count DESC
        """
        bu_hierarchy = self.conn.execute(bu_hierarchy_query).fetchall()
        hierarchy_analysis['bu_hierarchy'] = [
            {
                'business_unit': bu,
                'product_count': prod_count,
                'range_count': range_count,
                'pl_services_count': pl_count
            }
            for bu, prod_count, range_count, pl_count in bu_hierarchy
        ]
        
        print(f"{'Business Unit':<30} {'Products':<10} {'Ranges':<8} {'PL Services':<12}")
        print("-" * 65)
        for bu, prod_count, range_count, pl_count in bu_hierarchy:
            print(f"{bu:<30} {prod_count:<10,} {range_count:<8} {pl_count:<12}")
        
        self.analysis_results['hierarchies'] = hierarchy_analysis
        return hierarchy_analysis
    
    def analyze_semantic_patterns(self) -> Dict[str, Any]:
        """Analyze patterns for semantic search optimization"""
        print("\n🔍 ANALYZING SEMANTIC PATTERNS FOR SEARCH OPTIMIZATION")
        print("=" * 60)
        
        semantic_analysis = {}
        
        # Product naming patterns
        print("\n📝 PRODUCT NAMING PATTERNS:")
        naming_patterns_query = """
            SELECT 
                SUBSTR(PRODUCT_IDENTIFIER, 1, 3) as prefix,
                COUNT(*) as count,
                COUNT(DISTINCT RANGE_LABEL) as range_count
            FROM products 
            WHERE PRODUCT_IDENTIFIER IS NOT NULL AND LENGTH(PRODUCT_IDENTIFIER) >= 3
            GROUP BY SUBSTR(PRODUCT_IDENTIFIER, 1, 3)
            ORDER BY count DESC
            LIMIT 15
        """
        naming_patterns = self.conn.execute(naming_patterns_query).fetchall()
        semantic_analysis['naming_patterns'] = [
            {'prefix': prefix, 'count': count, 'range_count': range_count}
            for prefix, count, range_count in naming_patterns
        ]
        
        print(f"{'Prefix':<8} {'Count':<8} {'Ranges':<8}")
        print("-" * 25)
        for prefix, count, range_count in naming_patterns:
            print(f"{prefix:<8} {count:<8,} {range_count:<8}")
        
        # Description word analysis
        print("\n📖 DESCRIPTION WORD ANALYSIS:")
        # Get common words in descriptions
        descriptions_query = """
            SELECT PRODUCT_DESCRIPTION
            FROM products 
            WHERE PRODUCT_DESCRIPTION IS NOT NULL
            LIMIT 1000
        """
        descriptions = self.conn.execute(descriptions_query).fetchall()
        
        # Simple word frequency analysis
        word_freq = Counter()
        for (desc,) in descriptions:
            if desc:
                words = desc.upper().split()
                for word in words:
                    # Clean word (remove punctuation)
                    clean_word = ''.join(c for c in word if c.isalnum())
                    if len(clean_word) > 2:  # Only words longer than 2 chars
                        word_freq[clean_word] += 1
        
        top_words = word_freq.most_common(20)
        semantic_analysis['common_description_words'] = [
            {'word': word, 'frequency': freq} for word, freq in top_words
        ]
        
        print(f"{'Word':<15} {'Frequency':<10}")
        print("-" * 26)
        for word, freq in top_words[:10]:
            print(f"{word:<15} {freq:<10}")
        
        # Commercial status patterns
        print("\n📊 COMMERCIAL STATUS PATTERNS:")
        status_patterns_query = """
            SELECT 
                COMMERCIAL_STATUS,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM products), 2) as percentage
            FROM products 
            WHERE COMMERCIAL_STATUS IS NOT NULL
            GROUP BY COMMERCIAL_STATUS 
            ORDER BY count DESC
        """
        status_patterns = self.conn.execute(status_patterns_query).fetchall()
        semantic_analysis['status_patterns'] = [
            {'status': status, 'count': count, 'percentage': percentage}
            for status, count, percentage in status_patterns
        ]
        
        print(f"{'Status':<40} {'Count':<10} {'Percentage':<10}")
        print("-" * 65)
        for status, count, percentage in status_patterns:
            print(f"{status:<40} {count:<10,} {percentage:<10}%")
        
        self.analysis_results['semantic_patterns'] = semantic_analysis
        return semantic_analysis
    
    def analyze_search_optimization_opportunities(self) -> Dict[str, Any]:
        """Analyze opportunities for search optimization"""
        print("\n🎯 SEARCH OPTIMIZATION OPPORTUNITIES")
        print("=" * 60)
        
        optimization_analysis = {}
        
        # Identify key search fields
        search_fields = {
            'RANGE_LABEL': 'Primary range identifier',
            'SUBRANGE_LABEL': 'Secondary range identifier', 
            'PRODUCT_IDENTIFIER': 'Unique product code',
            'PRODUCT_DESCRIPTION': 'Full text description',
            'DEVICETYPE_LABEL': 'Device type classification',
            'BRAND_LABEL': 'Brand information'
        }
        
        optimization_analysis['recommended_search_fields'] = {}
        
        print("🔍 RECOMMENDED SEARCH FIELD ANALYSIS:")
        print("-" * 50)
        
        for field, description in search_fields.items():
            try:
                # Calculate field quality metrics
                total_rows = self.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
                non_null = self.conn.execute(f"SELECT COUNT({field}) FROM products WHERE {field} IS NOT NULL AND {field} != ''").fetchone()[0]
                unique_values = self.conn.execute(f"SELECT COUNT(DISTINCT {field}) FROM products WHERE {field} IS NOT NULL AND {field} != ''").fetchone()[0]
                
                coverage = (non_null / total_rows) * 100
                uniqueness = (unique_values / non_null) * 100 if non_null > 0 else 0
                
                # Get average length for text fields
                avg_length_query = f"SELECT AVG(LENGTH({field})) FROM products WHERE {field} IS NOT NULL"
                avg_length = self.conn.execute(avg_length_query).fetchone()[0] or 0
                
                field_quality = {
                    'description': description,
                    'coverage_percentage': round(coverage, 2),
                    'uniqueness_percentage': round(uniqueness, 2),
                    'average_length': round(avg_length, 2),
                    'non_null_count': non_null,
                    'unique_count': unique_values
                }
                
                optimization_analysis['recommended_search_fields'][field] = field_quality
                
                print(f"\n{field}:")
                print(f"  {description}")
                print(f"  Coverage: {coverage:.1f}% ({non_null:,} non-null)")
                print(f"  Uniqueness: {uniqueness:.1f}% ({unique_values:,} unique)")
                print(f"  Avg Length: {avg_length:.1f} chars")
                
            except Exception as e:
                print(f"  ⚠️ Error analyzing {field}: {e}")
        
        # Embedding optimization recommendations
        print("\n🚀 EMBEDDING OPTIMIZATION RECOMMENDATIONS:")
        print("-" * 50)
        
        recommendations = [
            "1. PRIMARY SEARCH FIELDS (High Priority):",
            "   - RANGE_LABEL: Primary product range identification",
            "   - PRODUCT_DESCRIPTION: Rich semantic content",
            "   - PRODUCT_IDENTIFIER: Exact product matching",
            "",
            "2. SECONDARY SEARCH FIELDS (Medium Priority):",
            "   - SUBRANGE_LABEL: Detailed range classification",
            "   - DEVICETYPE_LABEL: Functional categorization",
            "   - BRAND_LABEL: Brand-based filtering",
            "",
            "3. EMBEDDING STRATEGY:",
            "   - Combine RANGE_LABEL + PRODUCT_DESCRIPTION for rich embeddings",
            "   - Use hierarchical embeddings: Brand -> Range -> Product",
            "   - Include commercial status for lifecycle-aware search",
            "",
            "4. VECTOR SPACE OPTIMIZATION:",
            "   - Create separate embedding spaces for different product categories",
            "   - Use business unit clustering for domain-specific search",
            "   - Implement multi-modal embeddings (text + metadata)"
        ]
        
        optimization_analysis['recommendations'] = recommendations
        
        for rec in recommendations:
            print(rec)
        
        self.analysis_results['optimization'] = optimization_analysis
        return optimization_analysis
    
    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive database analysis report"""
        print("\n📋 GENERATING COMPREHENSIVE REPORT")
        print("=" * 60)
        
        # Create output directory
        output_dir = Path("docs/reports")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate report
        report_content = self._create_report_content()
        
        # Save report
        report_path = output_dir / "DUCKDB_COMPREHENSIVE_ANALYSIS.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        # Save raw analysis data
        analysis_path = output_dir / "duckdb_analysis_data.json"
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, indent=2, default=str)
        
        print(f"✅ Report saved: {report_path}")
        print(f"✅ Analysis data saved: {analysis_path}")
        
        return str(report_path)
    
    def _create_report_content(self) -> str:
        """Create comprehensive report content"""
        from datetime import datetime
        
        report = f"""# DuckDB Comprehensive Database Analysis Report
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Executive Summary

This comprehensive analysis of the IBcatalogue DuckDB database provides insights into data structure, content patterns, hierarchies, and optimization opportunities for enhanced semantic search and vector embeddings.

**Database Overview:**
- **Database Size**: {self.analysis_results.get('structure', {}).get('database_size_mb', 'N/A')} MB
- **Total Products**: {self.analysis_results.get('structure', {}).get('total_rows', 'N/A'):,}
- **Columns**: {len(self.analysis_results.get('structure', {}).get('schema', []))}
- **Tables**: {len(self.analysis_results.get('structure', {}).get('tables', []))}

## 🏗️ Database Structure Analysis

### Schema Overview
"""
        
        # Add schema details
        if 'structure' in self.analysis_results:
            schema = self.analysis_results['structure'].get('schema', [])
            report += f"\nThe database contains {len(schema)} columns with the following structure:\n\n"
            report += "| # | Column Name | Data Type | Nullable | Key |\n"
            report += "|---|-------------|-----------|----------|-----|\n"
            
            for i, col in enumerate(schema):
                report += f"| {i+1} | {col['column_name']} | {col['data_type']} | {col['nullable']} | {col.get('key', '')} |\n"
        
        # Add content analysis
        if 'content' in self.analysis_results:
            report += "\n## 📊 Data Content Analysis\n\n"
            
            column_analysis = self.analysis_results['content'].get('column_analysis', {})
            
            report += "### Key Column Statistics\n\n"
            report += "| Column | Coverage | Uniqueness | Unique Values |\n"
            report += "|--------|----------|------------|---------------|\n"
            
            for col_name, stats in column_analysis.items():
                if 'error' not in stats:
                    coverage = stats.get('null_percentage', 0)
                    coverage_pct = 100 - coverage
                    uniqueness = stats.get('uniqueness_percentage', 0)
                    unique_count = stats.get('unique_count', 0)
                    report += f"| {col_name} | {coverage_pct:.1f}% | {uniqueness:.1f}% | {unique_count:,} |\n"
        
        # Add hierarchy analysis
        if 'hierarchies' in self.analysis_results:
            report += "\n## 🌳 Product Hierarchies\n\n"
            
            hierarchies = self.analysis_results['hierarchies']
            
            # Brand hierarchy
            if 'brand_hierarchy' in hierarchies:
                report += "### Brand Distribution\n\n"
                report += "| Brand | Products | Ranges | Business Units |\n"
                report += "|-------|----------|--------|----------------|\n"
                
                for brand_info in hierarchies['brand_hierarchy'][:10]:
                    report += f"| {brand_info['brand']} | {brand_info['product_count']:,} | {brand_info['range_count']} | {brand_info['bu_count']} |\n"
            
            # Top ranges
            if 'range_hierarchy' in hierarchies:
                report += "\n### Top Product Ranges\n\n"
                report += "| Range | Products | Subranges | Brand |\n"
                report += "|-------|----------|-----------|-------|\n"
                
                for range_info in hierarchies['range_hierarchy'][:15]:
                    report += f"| {range_info['range']} | {range_info['product_count']:,} | {range_info['subrange_count']} | {range_info['brand'] or 'N/A'} |\n"
        
        # Add semantic patterns
        if 'semantic_patterns' in self.analysis_results:
            report += "\n## 🔍 Semantic Patterns Analysis\n\n"
            
            patterns = self.analysis_results['semantic_patterns']
            
            # Product naming patterns
            if 'naming_patterns' in patterns:
                report += "### Product Identifier Patterns\n\n"
                report += "| Prefix | Count | Ranges |\n"
                report += "|--------|-------|--------|\n"
                
                for pattern in patterns['naming_patterns'][:10]:
                    report += f"| {pattern['prefix']} | {pattern['count']:,} | {pattern['range_count']} |\n"
            
            # Commercial status
            if 'status_patterns' in patterns:
                report += "\n### Commercial Status Distribution\n\n"
                report += "| Status | Count | Percentage |\n"
                report += "|--------|-------|------------|\n"
                
                for status in patterns['status_patterns']:
                    report += f"| {status['status']} | {status['count']:,} | {status['percentage']}% |\n"
        
        # Add optimization recommendations
        if 'optimization' in self.analysis_results:
            report += "\n## 🎯 Search Optimization Recommendations\n\n"
            
            optimization = self.analysis_results['optimization']
            
            if 'recommended_search_fields' in optimization:
                report += "### Field Quality Analysis\n\n"
                report += "| Field | Coverage | Uniqueness | Avg Length | Recommendation |\n"
                report += "|-------|----------|------------|------------|----------------|\n"
                
                for field, stats in optimization['recommended_search_fields'].items():
                    coverage = stats.get('coverage_percentage', 0)
                    uniqueness = stats.get('uniqueness_percentage', 0)
                    avg_length = stats.get('average_length', 0)
                    
                    # Determine recommendation
                    if coverage > 90 and uniqueness > 50:
                        rec = "🟢 Excellent for embeddings"
                    elif coverage > 70 and uniqueness > 20:
                        rec = "🟡 Good for search"
                    else:
                        rec = "🔴 Limited utility"
                    
                    report += f"| {field} | {coverage:.1f}% | {uniqueness:.1f}% | {avg_length:.1f} | {rec} |\n"
            
            if 'recommendations' in optimization:
                report += "\n### Implementation Recommendations\n\n"
                for rec in optimization['recommendations']:
                    if rec.strip():
                        report += f"{rec}\n"
                    else:
                        report += "\n"
        
        report += f"""

## 🚀 Next Steps for Implementation

### 1. Enhanced Document Processor
- Implement field-aware extraction targeting high-coverage columns
- Use RANGE_LABEL and PRODUCT_DESCRIPTION as primary extraction targets
- Leverage commercial status patterns for lifecycle-aware processing

### 2. Optimized Embedding Strategy
- Create multi-level embeddings: Brand → Range → Product → Description
- Implement hierarchical vector spaces for better semantic clustering
- Use business unit information for domain-specific search optimization

### 3. Improved Vector Search
- Build separate FAISS indices for different product categories
- Implement hybrid search combining exact matches and semantic similarity
- Use commercial status for filtering and relevance scoring

### 4. Enhanced Semantic Search
- Leverage product identifier patterns for exact matching
- Use description word analysis for query expansion
- Implement brand and business unit aware search ranking

---

*This analysis provides the foundation for implementing a significantly improved document processor with better understanding of the database structure, content patterns, and optimization opportunities.*
"""
        
        return report
    
    def run_complete_analysis(self) -> str:
        """Run complete database analysis"""
        print("🚀 STARTING COMPREHENSIVE DUCKDB ANALYSIS")
        print("=" * 80)
        
        start_time = time.time()
        
        try:
            # Connect to database
            self.connect()
            
            # Run all analyses
            self.analyze_database_structure()
            self.analyze_data_content()
            self.analyze_product_hierarchies()
            self.analyze_semantic_patterns()
            self.analyze_search_optimization_opportunities()
            
            # Generate report
            report_path = self.generate_comprehensive_report()
            
            analysis_time = time.time() - start_time
            
            print(f"\n🎉 ANALYSIS COMPLETE!")
            print(f"⏱️ Total time: {analysis_time:.2f} seconds")
            print(f"📋 Report: {report_path}")
            
            return report_path
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            raise
        finally:
            if self.conn:
                self.conn.close()


def main():
    """Main function"""
    analyzer = ComprehensiveDatabaseAnalyzer()
    
    try:
        report_path = analyzer.run_complete_analysis()
        print(f"\n✅ Comprehensive analysis complete!")
        print(f"📄 Report available at: {report_path}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 