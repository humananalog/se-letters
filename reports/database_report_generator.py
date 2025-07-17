#!/usr/bin/env python3
"""
Database Report Generator for SE Letters Pipeline
================================================

Generates comprehensive reports from the letter database in various formats:
- Summary statistics
- Detailed letter information
- Product matching results
- Processing analytics
- Export to CSV/Excel

Author: Alexandre Huther
Date: 2025-07-17
Version: 1.0.0
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import psycopg2
import psycopg2.extras
import pandas as pd
from tabulate import tabulate
import argparse
from loguru import logger

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from se_letters.core.config import get_config


class DatabaseReportGenerator:
    """
    Comprehensive database report generator for SE Letters pipeline
    """
    
    def __init__(self, connection_string: str = None):
        """Initialize the report generator"""
        config = get_config()
        
        if connection_string:
            self.connection_string = connection_string
        else:
            # Use environment variable or default connection string
            self.connection_string = os.getenv(
                'DATABASE_URL', 
                'postgresql://ahuther:bender1980@localhost:5432/se_letters_dev'
            )
        
        self.report_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.reports_dir = Path(__file__).parent / "output"
        self.reports_dir.mkdir(exist_ok=True)
        
        logger.info(f"🚀 Database Report Generator initialized")
        logger.info(f"📊 Connection: {self.connection_string.split('@')[1] if '@' in self.connection_string else 'local'}")
        logger.info(f"📁 Reports directory: {self.reports_dir}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    
                    # Get table counts
                    cur.execute("""
                        SELECT 
                            (SELECT COUNT(*) FROM letters) as total_letters,
                            (SELECT COUNT(*) FROM letter_products) as total_products,
                            (SELECT COUNT(*) FROM letter_product_matches) as total_matches,
                            (SELECT COUNT(*) FROM processing_debug) as total_debug_records
                    """)
                    counts = cur.fetchone()
                    
                    # Get processing statistics
                    cur.execute("""
                        SELECT 
                            AVG(processing_time_ms) as avg_processing_time,
                            MIN(processing_time_ms) as min_processing_time,
                            MAX(processing_time_ms) as max_processing_time,
                            AVG(extraction_confidence) as avg_confidence,
                            MIN(extraction_confidence) as min_confidence,
                            MAX(extraction_confidence) as max_confidence
                        FROM letters 
                        WHERE processing_time_ms IS NOT NULL
                    """)
                    processing_stats = cur.fetchone()
                    
                    # Get status distribution
                    cur.execute("""
                        SELECT status, COUNT(*) as count
                        FROM letters 
                        GROUP BY status
                        ORDER BY count DESC
                    """)
                    status_distribution = cur.fetchall()
                    
                    # Get document type distribution
                    cur.execute("""
                        SELECT document_type, COUNT(*) as count
                        FROM letters 
                        WHERE document_type IS NOT NULL
                        GROUP BY document_type
                        ORDER BY count DESC
                    """)
                    doc_type_distribution = cur.fetchall()
                    
                    # Get date range
                    cur.execute("""
                        SELECT 
                            MIN(created_at) as earliest_letter,
                            MAX(created_at) as latest_letter
                        FROM letters
                    """)
                    date_range = cur.fetchone()
                    
                    return {
                        'counts': dict(counts),
                        'processing_stats': dict(processing_stats),
                        'status_distribution': [dict(row) for row in status_distribution],
                        'doc_type_distribution': [dict(row) for row in doc_type_distribution],
                        'date_range': dict(date_range)
                    }
                    
        except Exception as e:
            logger.error(f"❌ Failed to get database stats: {e}")
            return {}
    
    def get_letters_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all letters"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    
                    cur.execute("""
                        SELECT 
                            id,
                            document_name,
                            document_type,
                            document_title,
                            file_size,
                            processing_time_ms,
                            extraction_confidence,
                            status,
                            created_at,
                            updated_at
                        FROM letters
                        ORDER BY created_at DESC
                    """)
                    
                    return [dict(row) for row in cur.fetchall()]
                    
        except Exception as e:
            logger.error(f"❌ Failed to get letters summary: {e}")
            return []
    
    def get_products_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all products"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    
                    cur.execute("""
                        SELECT 
                            lp.id,
                            lp.letter_id,
                            l.document_name,
                            lp.product_identifier,
                            lp.range_label,
                            lp.subrange_label,
                            lp.product_line,
                            lp.product_description,
                            lp.obsolescence_status,
                            lp.confidence_score,
                            lp.validation_status,
                            l.created_at
                        FROM letter_products lp
                        JOIN letters l ON lp.letter_id = l.id
                        ORDER BY l.created_at DESC
                    """)
                    
                    return [dict(row) for row in cur.fetchall()]
                    
        except Exception as e:
            logger.error(f"❌ Failed to get products summary: {e}")
            return []
    
    def get_product_matches_summary(self) -> List[Dict[str, Any]]:
        """Get summary of product matches"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    
                    cur.execute("""
                        SELECT 
                            lpm.id,
                            l.document_name,
                            lp.product_identifier,
                            lpm.ibcatalogue_product_identifier,
                            lpm.match_confidence,
                            lpm.match_type,
                            lpm.created_at
                        FROM letter_product_matches lpm
                        JOIN letter_products lp ON lpm.letter_product_id = lp.id
                        JOIN letters l ON lp.letter_id = l.id
                        ORDER BY lpm.match_confidence DESC
                    """)
                    
                    return [dict(row) for row in cur.fetchall()]
                    
        except Exception as e:
            logger.error(f"❌ Failed to get product matches summary: {e}")
            return []
    
    def generate_summary_report(self) -> str:
        """Generate a comprehensive summary report"""
        stats = self.get_database_stats()
        
        if not stats:
            return "❌ Failed to generate summary report"
        
        report = []
        report.append("=" * 80)
        report.append("📊 SE LETTERS DATABASE SUMMARY REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Database Overview
        report.append("🗄️ DATABASE OVERVIEW")
        report.append("-" * 40)
        counts = stats['counts']
        report.append(f"Total Letters: {counts['total_letters']}")
        report.append(f"Total Products: {counts['total_products']}")
        report.append(f"Total Matches: {counts['total_matches']}")
        report.append(f"Debug Records: {counts['total_debug_records']}")
        report.append("")
        
        # Processing Statistics
        report.append("⚡ PROCESSING STATISTICS")
        report.append("-" * 40)
        proc_stats = stats['processing_stats']
        if proc_stats['avg_processing_time']:
            report.append(f"Average Processing Time: {proc_stats['avg_processing_time']:.2f} ms")
            report.append(f"Min Processing Time: {proc_stats['min_processing_time']:.2f} ms")
            report.append(f"Max Processing Time: {proc_stats['max_processing_time']:.2f} ms")
        else:
            report.append("No processing time data available")
        
        if proc_stats['avg_confidence']:
            report.append(f"Average Confidence: {proc_stats['avg_confidence']:.2%}")
            report.append(f"Min Confidence: {proc_stats['min_confidence']:.2%}")
            report.append(f"Max Confidence: {proc_stats['max_confidence']:.2%}")
        else:
            report.append("No confidence data available")
        report.append("")
        
        # Status Distribution
        report.append("📋 STATUS DISTRIBUTION")
        report.append("-" * 40)
        for status in stats['status_distribution']:
            report.append(f"{status['status']}: {status['count']}")
        report.append("")
        
        # Document Type Distribution
        report.append("📄 DOCUMENT TYPE DISTRIBUTION")
        report.append("-" * 40)
        for doc_type in stats['doc_type_distribution']:
            report.append(f"{doc_type['document_type']}: {doc_type['count']}")
        report.append("")
        
        # Date Range
        report.append("📅 DATE RANGE")
        report.append("-" * 40)
        date_range = stats['date_range']
        if date_range['earliest_letter']:
            report.append(f"Earliest Letter: {date_range['earliest_letter']}")
            report.append(f"Latest Letter: {date_range['latest_letter']}")
        else:
            report.append("No date data available")
        report.append("")
        
        return "\n".join(report)
    
    def generate_letters_table(self) -> str:
        """Generate a detailed letters table"""
        letters = self.get_letters_summary()
        
        if not letters:
            return "❌ No letters found"
        
        # Prepare data for tabulation
        table_data = []
        for letter in letters:
            table_data.append([
                letter['id'],
                letter['document_name'][:30] + "..." if len(letter['document_name']) > 30 else letter['document_name'],
                letter['document_type'] or "N/A",
                letter['document_title'][:25] + "..." if letter['document_title'] and len(letter['document_title']) > 25 else (letter['document_title'] or "N/A"),
                f"{letter['file_size']:,}" if letter['file_size'] else "N/A",
                f"{letter['processing_time_ms']:.1f}ms" if letter['processing_time_ms'] else "N/A",
                f"{letter['extraction_confidence']:.1%}" if letter['extraction_confidence'] else "N/A",
                letter['status'],
                letter['created_at'].strftime('%Y-%m-%d %H:%M') if letter['created_at'] else "N/A"
            ])
        
        headers = [
            "ID", "Document Name", "Type", "Title", 
            "Size (bytes)", "Processing Time", "Confidence", "Status", "Created"
        ]
        
        return tabulate(table_data, headers=headers, tablefmt="grid")
    
    def generate_products_table(self) -> str:
        """Generate a detailed products table"""
        products = self.get_products_summary()
        
        if not products:
            return "❌ No products found"
        
        # Prepare data for tabulation
        table_data = []
        for product in products:
            table_data.append([
                product['id'],
                product['document_name'][:20] + "..." if len(product['document_name']) > 20 else product['document_name'],
                product['product_identifier'] or "N/A",
                product['range_label'] or "N/A",
                product['subrange_label'] or "N/A",
                product['product_line'] or "N/A",
                product['product_description'][:30] + "..." if product['product_description'] and len(product['product_description']) > 30 else (product['product_description'] or "N/A"),
                product['obsolescence_status'] or "N/A",
                f"{product['confidence_score']:.1%}" if product['confidence_score'] else "N/A",
                product['validation_status']
            ])
        
        headers = [
            "ID", "Document", "Product ID", "Range", "Subrange", 
            "Product Line", "Description", "Status", "Confidence", "Validation"
        ]
        
        return tabulate(table_data, headers=headers, tablefmt="grid")
    
    def generate_matches_table(self) -> str:
        """Generate a detailed matches table"""
        matches = self.get_product_matches_summary()
        
        if not matches:
            return "❌ No matches found"
        
        # Prepare data for tabulation
        table_data = []
        for match in matches:
            table_data.append([
                match['id'],
                match['document_name'][:20] + "..." if len(match['document_name']) > 20 else match['document_name'],
                match['product_identifier'] or "N/A",
                match['ibcatalogue_product_identifier'] or "N/A",
                f"{match['match_confidence']:.3f}" if match['match_confidence'] else "N/A",
                match['match_type'] or "N/A",
                match['created_at'].strftime('%Y-%m-%d %H:%M') if match['created_at'] else "N/A"
            ])
        
        headers = [
            "ID", "Document", "Product ID", "Matched Product", 
            "Similarity", "Match Type", "Created"
        ]
        
        return tabulate(table_data, headers=headers, tablefmt="grid")
    
    def export_to_csv(self, filename_prefix: str = "database_report"):
        """Export all data to CSV files"""
        try:
            # Export letters
            letters_df = pd.DataFrame(self.get_letters_summary())
            letters_file = self.reports_dir / f"{filename_prefix}_letters_{self.report_timestamp}.csv"
            letters_df.to_csv(letters_file, index=False)
            logger.info(f"📄 Exported letters to: {letters_file}")
            
            # Export products
            products_df = pd.DataFrame(self.get_products_summary())
            products_file = self.reports_dir / f"{filename_prefix}_products_{self.report_timestamp}.csv"
            products_df.to_csv(products_file, index=False)
            logger.info(f"📄 Exported products to: {products_file}")
            
            # Export matches
            matches_df = pd.DataFrame(self.get_product_matches_summary())
            matches_file = self.reports_dir / f"{filename_prefix}_matches_{self.report_timestamp}.csv"
            matches_df.to_csv(matches_file, index=False)
            logger.info(f"📄 Exported matches to: {matches_file}")
            
            return {
                'letters': str(letters_file),
                'products': str(products_file),
                'matches': str(matches_file)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to export CSV files: {e}")
            return {}
    
    def export_to_excel(self, filename_prefix: str = "database_report"):
        """Export all data to Excel file with multiple sheets"""
        try:
            excel_file = self.reports_dir / f"{filename_prefix}_{self.report_timestamp}.xlsx"
            
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                # Summary sheet
                stats = self.get_database_stats()
                summary_data = []
                
                # Add counts
                for key, value in stats['counts'].items():
                    summary_data.append(['Counts', key.replace('_', ' ').title(), value])
                
                # Add processing stats
                for key, value in stats['processing_stats'].items():
                    if value is not None:
                        if 'confidence' in key:
                            summary_data.append(['Processing', key.replace('_', ' ').title(), f"{value:.2%}"])
                        elif 'time' in key:
                            summary_data.append(['Processing', key.replace('_', ' ').title(), f"{value:.2f} ms"])
                        else:
                            summary_data.append(['Processing', key.replace('_', ' ').title(), value])
                
                summary_df = pd.DataFrame(summary_data, columns=['Category', 'Metric', 'Value'])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Letters sheet
                letters_df = pd.DataFrame(self.get_letters_summary())
                letters_df.to_excel(writer, sheet_name='Letters', index=False)
                
                # Products sheet
                products_df = pd.DataFrame(self.get_products_summary())
                products_df.to_excel(writer, sheet_name='Products', index=False)
                
                # Matches sheet
                matches_df = pd.DataFrame(self.get_product_matches_summary())
                matches_df.to_excel(writer, sheet_name='Matches', index=False)
                
                # Status distribution sheet
                status_df = pd.DataFrame(stats['status_distribution'])
                status_df.to_excel(writer, sheet_name='Status Distribution', index=False)
                
                # Document type distribution sheet
                doc_type_df = pd.DataFrame(stats['doc_type_distribution'])
                doc_type_df.to_excel(writer, sheet_name='Document Types', index=False)
            
            logger.info(f"📊 Exported Excel report to: {excel_file}")
            return str(excel_file)
            
        except Exception as e:
            logger.error(f"❌ Failed to export Excel file: {e}")
            return None
    
    def generate_full_report(self, output_format: str = "console") -> str:
        """Generate a complete report in the specified format"""
        logger.info("🚀 Generating comprehensive database report...")
        
        # Generate summary report
        summary = self.generate_summary_report()
        
        # Generate detailed tables
        letters_table = self.generate_letters_table()
        products_table = self.generate_products_table()
        matches_table = self.generate_matches_table()
        
        # Combine all sections
        full_report = []
        full_report.append(summary)
        full_report.append("")
        full_report.append("=" * 80)
        full_report.append("📋 DETAILED LETTERS TABLE")
        full_report.append("=" * 80)
        full_report.append(letters_table)
        full_report.append("")
        full_report.append("=" * 80)
        full_report.append("🏷️ DETAILED PRODUCTS TABLE")
        full_report.append("=" * 80)
        full_report.append(products_table)
        full_report.append("")
        full_report.append("=" * 80)
        full_report.append("🎯 DETAILED MATCHES TABLE")
        full_report.append("=" * 80)
        full_report.append(matches_table)
        
        report_text = "\n".join(full_report)
        
        # Save to file if requested
        if output_format == "file":
            report_file = self.reports_dir / f"database_report_{self.report_timestamp}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            logger.info(f"📄 Report saved to: {report_file}")
            return str(report_file)
        
        return report_text


def main():
    """Main function to run the report generator"""
    parser = argparse.ArgumentParser(description="Generate database reports for SE Letters pipeline")
    parser.add_argument("--format", choices=["console", "file", "csv", "excel", "all"], 
                       default="console", help="Output format")
    parser.add_argument("--connection", help="Database connection string")
    parser.add_argument("--output-dir", help="Output directory for reports")
    
    args = parser.parse_args()
    
    # Initialize report generator
    generator = DatabaseReportGenerator(args.connection)
    
    if args.output_dir:
        generator.reports_dir = Path(args.output_dir)
        generator.reports_dir.mkdir(exist_ok=True)
    
    try:
        if args.format == "console":
            # Generate console report
            report = generator.generate_full_report("console")
            print(report)
            
        elif args.format == "file":
            # Generate file report
            report_file = generator.generate_full_report("file")
            print(f"📄 Report generated: {report_file}")
            
        elif args.format == "csv":
            # Export to CSV
            csv_files = generator.export_to_csv()
            print("📄 CSV files generated:")
            for file_type, file_path in csv_files.items():
                print(f"  - {file_type}: {file_path}")
                
        elif args.format == "excel":
            # Export to Excel
            excel_file = generator.export_to_excel()
            print(f"📊 Excel report generated: {excel_file}")
            
        elif args.format == "all":
            # Generate all formats
            print("🚀 Generating all report formats...")
            
            # Console report
            report = generator.generate_full_report("console")
            print(report)
            print("\n" + "="*80)
            
            # File report
            report_file = generator.generate_full_report("file")
            print(f"📄 Text report: {report_file}")
            
            # CSV files
            csv_files = generator.export_to_csv()
            print("📄 CSV files:")
            for file_type, file_path in csv_files.items():
                print(f"  - {file_type}: {file_path}")
            
            # Excel file
            excel_file = generator.export_to_excel()
            print(f"📊 Excel report: {excel_file}")
            
        logger.info("✅ Report generation completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Report generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 