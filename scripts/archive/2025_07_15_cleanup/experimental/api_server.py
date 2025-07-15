#!/usr/bin/env python3
"""
Simple Flask API server to serve document metadata from DuckDB
"""

import json
import duckdb
from flask import Flask, jsonify, request
from flask_cors import CORS
from pathlib import Path

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

DB_PATH = 'data/document_metadata.duckdb'

def get_db_connection():
    """Get DuckDB connection"""
    return duckdb.connect(DB_PATH)

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Get all documents or specific document details"""
    document_id = request.args.get('id')
    
    try:
        conn = get_db_connection()
        
        if document_id:
            # Get specific document details
            document = conn.execute("""
                SELECT * FROM documents WHERE id = ?
            """, [int(document_id)]).fetchone()
            
            if not document:
                return jsonify({'error': 'Document not found'}), 404
            
            # Convert to dict
            doc_columns = [desc[0] for desc in conn.description]
            document_dict = dict(zip(doc_columns, document))
            
            # Get products
            products = conn.execute("""
                SELECT * FROM document_products WHERE document_id = ?
            """, [int(document_id)]).fetchall()
            
            product_columns = [desc[0] for desc in conn.description]
            products_list = [dict(zip(product_columns, row)) for row in products]
            
            # Get business info
            business_info = conn.execute("""
                SELECT * FROM document_business_info WHERE document_id = ?
            """, [int(document_id)]).fetchone()
            
            business_dict = None
            if business_info:
                business_columns = [desc[0] for desc in conn.description]
                business_dict = dict(zip(business_columns, business_info))
            
            conn.close()
            
            return jsonify({
                'document': document_dict,
                'products': products_list,
                'businessInfo': business_dict
            })
        
        else:
            # Get all documents summary
            documents = conn.execute("""
                SELECT 
                  d.id,
                  d.document_name,
                  d.document_type,
                  d.language,
                  d.total_products,
                  d.extraction_confidence,
                  d.extraction_complexity,
                  d.has_technical_specs,
                  d.processing_timestamp,
                  COUNT(p.product_identifier) as actual_products,
                  STRING_AGG(DISTINCT p.product_line, ', ') as product_lines
                FROM documents d
                LEFT JOIN document_products p ON d.id = p.document_id
                GROUP BY d.id, d.document_name, d.document_type, d.language, 
                         d.total_products, d.extraction_confidence, d.extraction_complexity,
                         d.has_technical_specs, d.processing_timestamp
                ORDER BY d.id
            """).fetchall()
            
            doc_columns = [desc[0] for desc in conn.description]
            documents_list = [dict(zip(doc_columns, row)) for row in documents]
            
            # Get statistics
            stats = conn.execute("""
                SELECT 
                  COUNT(DISTINCT d.id) as total_documents,
                  COUNT(p.product_identifier) as total_products,
                  AVG(d.extraction_confidence) as avg_confidence,
                  COUNT(DISTINCT p.product_line) as unique_product_lines
                FROM documents d
                LEFT JOIN document_products p ON d.id = p.document_id
            """).fetchone()
            
            stats_columns = [desc[0] for desc in conn.description]
            stats_dict = dict(zip(stats_columns, stats))
            
            conn.close()
            
            return jsonify({
                'documents': documents_list,
                'statistics': stats_dict
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Document metadata API is running'})

if __name__ == '__main__':
    # Check if database exists
    if not Path(DB_PATH).exists():
        print(f"❌ Database not found at {DB_PATH}")
        print("Please run scripts/convert_json_to_duckdb.py first")
        exit(1)
    
    print(f"🚀 Starting Document Metadata API server...")
    print(f"📊 Database: {DB_PATH}")
    print(f"🌐 API will be available at: http://localhost:5001")
    
    app.run(host='0.0.0.0', port=5001, debug=True) 