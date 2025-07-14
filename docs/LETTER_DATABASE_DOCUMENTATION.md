# Letter Database Documentation

**Version: 2.1.0**  
**Last Updated: 2025-01-27**  
**Database Engine: DuckDB**  
**Schema Version: 2.1.0**

## 📋 Table of Contents

1. [Overview](#overview)
2. [Database Architecture](#database-architecture)
3. [Schema Definitions](#schema-definitions)
4. [Relationships](#relationships)
5. [Indexes and Performance](#indexes-and-performance)
6. [Data Flow](#data-flow)
7. [API Integration](#api-integration)
8. [Migration Guide](#migration-guide)
9. [Troubleshooting](#troubleshooting)
10. [Version History](#version-history)

## 🎯 Overview

The Letter Database is the core data storage system for the Schneider Electric Obsolescence Letter Matching Pipeline. It stores comprehensive metadata extracted from obsolescence letters, including product information, technical specifications, and processing details.

### Key Features
- **Multi-Environment Support**: Production and staging databases
- **Comprehensive Metadata**: Complete letter and product information
- **Processing Audit Trail**: Full traceability of processing steps
- **JSON Storage**: Flexible storage for complex metadata structures
- **High Performance**: Optimized with proper indexing and DuckDB

### Database Files
- **Production**: `data/letters.duckdb`
- **Staging**: `data/staging.duckdb`
- **Document Metadata**: `data/document_metadata.duckdb`

## 🏗️ Database Architecture

### Environment Separation
```
Production Database (letters.duckdb)
├── letters (main letter records)
├── letter_products (product information)
└── processing_debug (audit trail)

Staging Database (staging.duckdb)
├── raw_processing_staging (raw processing results)
└── document_staging (document metadata staging)

Document Metadata Database (document_metadata.duckdb)
├── documents (document metadata)
├── document_products (product details)
└── business_information (business context)
```

### Database Services
- **LetterDatabaseService**: Main production database operations
- **RawFileLetterDatabaseService**: Raw file processing storage
- **DocumentMetadataService**: Document metadata management
- **SOTAGrokService**: SOTA processing staging

## 📊 Schema Definitions

### Production Database Schema (v2.1.0)

#### Letters Table
```sql
CREATE TABLE letters (
    id INTEGER PRIMARY KEY DEFAULT nextval('letters_id_seq'),
    document_name TEXT NOT NULL,
    document_type TEXT,
    document_title TEXT,
    source_file_path TEXT NOT NULL,
    file_size INTEGER,
    processing_method TEXT DEFAULT 'raw_file_grok',
    processing_time_ms REAL,
    extraction_confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'processed',
    raw_grok_json TEXT,
    ocr_supplementary_json TEXT,
    processing_steps_json TEXT
);
```

**Field Descriptions:**
- `id`: Auto-incrementing primary key
- `document_name`: Original filename
- `document_type`: Document type (PDF, DOCX, DOC)
- `document_title`: Extracted document title
- `source_file_path`: Full path to source file
- `file_size`: File size in bytes
- `processing_method`: Processing method used
- `processing_time_ms`: Processing time in milliseconds
- `extraction_confidence`: Confidence score (0.0-1.0)
- `created_at`: Processing timestamp
- `status`: Processing status (processed, failed, pending)
- `raw_grok_json`: Complete Grok extraction results (JSON)
- `ocr_supplementary_json`: OCR supplementary data (JSON)
- `processing_steps_json`: Processing step details (JSON)

#### Letter Products Table
```sql
CREATE TABLE letter_products (
    id INTEGER PRIMARY KEY DEFAULT nextval('products_id_seq'),
    letter_id INTEGER NOT NULL,
    product_identifier TEXT,
    range_label TEXT,
    subrange_label TEXT,
    product_line TEXT,
    product_description TEXT,
    obsolescence_status TEXT,
    end_of_service_date TEXT,
    replacement_suggestions TEXT,
    FOREIGN KEY (letter_id) REFERENCES letters(id)
);
```

**Field Descriptions:**
- `id`: Auto-incrementing primary key
- `letter_id`: Foreign key to letters table
- `product_identifier`: Product identifier/code
- `range_label`: Product range name
- `subrange_label`: Product subrange name
- `product_line`: Product line classification
- `product_description`: Product description
- `obsolescence_status`: Obsolescence status
- `end_of_service_date`: End of service date
- `replacement_suggestions`: Replacement product suggestions

#### Processing Debug Table
```sql
CREATE TABLE processing_debug (
    id INTEGER PRIMARY KEY DEFAULT nextval('debug_id_seq'),
    letter_id INTEGER NOT NULL,
    processing_step TEXT NOT NULL,
    step_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    step_duration_ms REAL,
    step_success BOOLEAN DEFAULT TRUE,
    step_details TEXT,
    FOREIGN KEY (letter_id) REFERENCES letters(id)
);
```

**Field Descriptions:**
- `id`: Auto-incrementing primary key
- `letter_id`: Foreign key to letters table
- `processing_step`: Name of processing step
- `step_timestamp`: Step execution timestamp
- `step_duration_ms`: Step duration in milliseconds
- `step_success`: Step success status
- `step_details`: Detailed step information

### Staging Database Schema (v2.1.0)

#### Raw Processing Staging Table
```sql
CREATE TABLE raw_processing_staging (
    id INTEGER PRIMARY KEY DEFAULT nextval('raw_staging_id_seq'),
    source_file_path TEXT NOT NULL,
    document_name TEXT NOT NULL,
    file_size INTEGER,
    file_type TEXT,
    processing_method TEXT,
    raw_grok_json TEXT NOT NULL,
    ocr_text TEXT,
    processing_confidence REAL DEFAULT 0.0,
    processing_time_ms REAL,
    model_used TEXT DEFAULT 'grok-3-latest',
    prompt_version TEXT DEFAULT '2.0.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT
);
```

#### Document Staging Table
```sql
CREATE TABLE document_staging (
    source_file_path TEXT NOT NULL,
    document_name TEXT NOT NULL,
    raw_json TEXT NOT NULL,
    metadata_extracted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_confidence REAL DEFAULT 0.0,
    model_used TEXT DEFAULT 'grok-3-latest',
    prompt_version TEXT DEFAULT '2.0.0'
);
```

### Document Metadata Database Schema (v2.1.0)

#### Documents Table
```sql
CREATE TABLE documents (
    id INTEGER,
    source_file_path VARCHAR,
    document_name VARCHAR,
    document_type VARCHAR,
    language VARCHAR,
    document_number VARCHAR,
    total_products INTEGER,
    has_tables BOOLEAN,
    has_technical_specs BOOLEAN,
    extraction_complexity VARCHAR,
    extraction_confidence FLOAT,
    processing_timestamp VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Document Products Table
```sql
CREATE TABLE document_products (
    document_id INTEGER,
    product_identifier TEXT,
    range_label TEXT,
    subrange_label TEXT,
    product_line TEXT,
    product_description TEXT,
    voltage_level TEXT,
    current_rating TEXT,
    power_rating TEXT,
    frequency TEXT,
    part_number TEXT,
    obsolescence_status TEXT,
    last_order_date TEXT,
    end_of_service_date TEXT,
    replacement_suggestions TEXT,
    migration_path TEXT
);
```

## 🔗 Relationships

### Primary Relationships
```
letters (1) ←→ (N) letter_products
letters (1) ←→ (N) processing_debug
```

### Foreign Key Constraints
- `letter_products.letter_id` → `letters.id`
- `processing_debug.letter_id` → `letters.id`

### Data Integrity
- **Cascade Delete**: When a letter is deleted, related products and debug records are automatically removed
- **Referential Integrity**: All foreign key relationships are enforced
- **Unique Constraints**: `source_file_path` must be unique in letters table

## ⚡ Indexes and Performance

### Production Database Indexes
```sql
-- Primary indexes
CREATE INDEX idx_letters_source_path ON letters(source_file_path);
CREATE INDEX idx_letters_document_name ON letters(document_name);
CREATE INDEX idx_products_letter_id ON letter_products(letter_id);
CREATE INDEX idx_debug_letter_id ON processing_debug(letter_id);

-- Performance indexes
CREATE INDEX idx_letters_created_at ON letters(created_at);
CREATE INDEX idx_letters_status ON letters(status);
CREATE INDEX idx_letters_confidence ON letters(extraction_confidence);
```

### Staging Database Indexes
```sql
-- Staging indexes
CREATE INDEX idx_raw_staging_source_path ON raw_processing_staging(source_file_path);
CREATE INDEX idx_staging_source_path ON document_staging(source_file_path);
```

### Query Optimization
- **Composite Indexes**: For complex queries involving multiple columns
- **Covering Indexes**: Include frequently accessed columns
- **Partial Indexes**: For filtered queries (e.g., successful processing only)

## 🔄 Data Flow

### 1. Document Processing Flow
```
Input Document → Raw Processing → Staging → Production → Web Interface
```

### 2. Database Operations Flow
```
1. Document Upload
   ↓
2. Raw Processing (staging.duckdb)
   ↓
3. Metadata Extraction (document_metadata.duckdb)
   ↓
4. Production Storage (letters.duckdb)
   ↓
5. Web Interface Display
```

### 3. Error Handling Flow
```
Processing Error → Debug Table → Error Logging → Retry Logic
```

## 🔌 API Integration

### Web Application API
The database integrates with the Next.js web application through RESTful APIs:

#### Get All Letters
```typescript
GET /api/letters
Response: LetterData[]
```

#### Get Letter by ID
```typescript
GET /api/letters/{id}
Response: LetterData
```

#### Process Document
```typescript
POST /api/pipeline/execute
Request: FormData (file)
Response: ProcessingResult
```

### Python Service Integration
```python
from se_letters.services import LetterDatabaseService

# Initialize service
db_service = LetterDatabaseService("data/letters.duckdb")

# Store letter metadata
letter_id = db_service.store_letter_metadata(metadata)

# Retrieve letter
letter_data = db_service.get_letter_by_id(letter_id)

# Get all letters
all_letters = db_service.get_all_letters()
```

## 🔄 Migration Guide

### Version 2.0.0 to 2.1.0
1. **Database Schema Updates**
   ```sql
   -- Add new columns to existing tables
   ALTER TABLE letters ADD COLUMN processing_steps_json TEXT;
   ALTER TABLE raw_processing_staging ADD COLUMN prompt_version TEXT DEFAULT '2.0.0';
   ```

2. **Sequence Updates**
   ```sql
   -- Recreate sequences for proper auto-increment
   DROP SEQUENCE IF EXISTS letters_id_seq;
   CREATE SEQUENCE letters_id_seq START 1;
   ```

3. **Index Updates**
   ```sql
   -- Add new performance indexes
   CREATE INDEX idx_letters_processing_steps ON letters(processing_steps_json);
   ```

### Migration Scripts
```bash
# Run migration script
python scripts/fix_database_storage_issues.py

# Verify migration
python tests/integration/test_database_storage.py
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Auto-increment Issues
**Problem**: `last_insert_rowid()` not supported in DuckDB
**Solution**: Use `currval('sequence_name')` instead

```python
# Incorrect (SQLite syntax)
letter_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

# Correct (DuckDB syntax)
letter_id = conn.execute("SELECT currval('letters_id_seq')").fetchone()[0]
```

#### 2. Foreign Key Constraint Violations
**Problem**: Referential integrity errors
**Solution**: Ensure parent records exist before inserting child records

```python
# Insert parent first
conn.execute("INSERT INTO letters (...) VALUES (...)")
letter_id = conn.execute("SELECT currval('letters_id_seq')").fetchone()[0]

# Then insert child records
conn.execute("INSERT INTO letter_products (letter_id, ...) VALUES (?, ...)", [letter_id, ...])
```

#### 3. JSON Storage Issues
**Problem**: Invalid JSON data
**Solution**: Validate JSON before storage

```python
import json

# Validate JSON before storage
try:
    json_data = json.dumps(metadata, indent=2)
    conn.execute("INSERT INTO letters (raw_grok_json) VALUES (?)", [json_data])
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON data: {e}")
```

### Performance Optimization

#### 1. Query Optimization
```sql
-- Use specific columns instead of SELECT *
SELECT id, document_name, status FROM letters WHERE status = 'processed';

-- Use LIMIT for large result sets
SELECT * FROM letters ORDER BY created_at DESC LIMIT 100;
```

#### 2. Batch Operations
```python
# Batch insert for better performance
with conn.begin():
    for product in products:
        conn.execute("INSERT INTO letter_products (...) VALUES (...)", product_data)
```

#### 3. Connection Management
```python
# Use context managers for proper connection handling
with duckdb.connect(db_path) as conn:
    # Database operations
    pass
```

## 📈 Version History

### Version 2.1.0 (Current)
- **Date**: 2025-01-27
- **Changes**:
  - Fixed DuckDB compatibility issues
  - Added proper auto-increment sequences
  - Enhanced error handling and logging
  - Added processing steps tracking
  - Improved web application integration
  - Added comprehensive testing suite

### Version 2.0.0
- **Date**: 2025-01-20
- **Changes**:
  - Migrated from SQLite to DuckDB
  - Added staging database support
  - Enhanced metadata extraction
  - Added document metadata service
  - Improved performance with indexing

### Version 1.0.0
- **Date**: 2025-01-10
- **Changes**:
  - Initial database implementation
  - Basic letter storage
  - Product information tracking
  - Simple web interface

## 📞 Support

### Database Issues
- Check logs in `logs/` directory
- Run database validation tests
- Review error messages in processing_debug table

### Performance Issues
- Monitor query execution times
- Check index usage with EXPLAIN
- Optimize slow queries

### Schema Changes
- Follow migration guide
- Test changes in staging environment
- Update documentation

---

**Database Version**: 2.1.0  
**Last Updated**: 2025-01-27  
**Maintainer**: SE Letters Team  
**Documentation Version**: 2.1.0 