# PostgreSQL Migration Plan

**Version: 2.2.0**  
**Author: Alexandre Huther**  
**Date: 2025-07-16**

## 🎯 **Migration Overview**

This document outlines the comprehensive migration from DuckDB to PostgreSQL to resolve concurrent access issues while maintaining production reliability and AI/ML pipeline performance for the SE Letters application.

## 📋 **Phase 1: Pre-Migration Analysis & Preparation**

### **1.1 Current System Audit**

#### **Database Schema Analysis**
- Export current DuckDB schema from `data/letters.duckdb`
- Document all tables, indexes, constraints, sequences
- Identify DuckDB-specific features (sequences, data types, functions)
- Map table relationships and foreign keys

#### **Data Volume Assessment**
- Count records in each table:
  - `letters` table
  - `letter_products` table  
  - `letter_product_matches` table
  - `processing_debug` table
- Estimate storage requirements for PostgreSQL
- Identify data types that need conversion

#### **Query Performance Analysis**
- Document all SQL queries in Python and Node.js code
- Identify performance-critical queries
- Map query patterns and optimization opportunities

### **1.2 PostgreSQL Environment Setup**

#### **Development Environment**
```bash
# Install PostgreSQL locally
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb se_letters_dev

# Install Python dependencies
pip install psycopg2-binary asyncpg

# Install Node.js dependencies
npm install pg @types/pg
```

#### **Configuration Management**
Update `config/config.yaml`:
```yaml
database:
  postgresql:
    host: localhost
    port: 5432
    database: se_letters_dev
    user: postgres
    password: password
    pool_size: 20
    connection_timeout: 30
    idle_timeout: 300
```

### **1.3 Migration Tools Preparation**

#### **Schema Migration Scripts**
Create `scripts/migrate_schema_to_postgresql.py`:
```python
#!/usr/bin/env python3
"""
Schema Migration Script - DuckDB to PostgreSQL
Exports DuckDB schema and generates PostgreSQL-compatible DDL
"""

import duckdb
import psycopg2
from pathlib import Path

def export_duckdb_schema():
    """Export DuckDB schema and generate PostgreSQL DDL"""
    duck_conn = duckdb.connect("data/letters.duckdb")
    
    # Get table schemas
    tables = duck_conn.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'main'
    """).fetchall()
    
    for table in tables:
        table_name = table[0]
        print(f"Processing table: {table_name}")
        
        # Get column information
        columns = duck_conn.execute(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """).fetchall()
        
        # Generate PostgreSQL DDL
        generate_postgresql_ddl(table_name, columns)

def generate_postgresql_ddl(table_name: str, columns: list):
    """Generate PostgreSQL DDL for a table"""
    ddl = f"CREATE TABLE {table_name} (\n"
    
    for column in columns:
        col_name, data_type, is_nullable, default = column
        
        # Map DuckDB types to PostgreSQL
        pg_type = map_data_type(data_type)
        
        ddl += f"    {col_name} {pg_type}"
        
        if default and default != "NULL":
            ddl += f" DEFAULT {default}"
        
        if is_nullable == "NO":
            ddl += " NOT NULL"
        
        ddl += ",\n"
    
    ddl = ddl.rstrip(",\n") + "\n);"
    
    print(f"Generated DDL for {table_name}:")
    print(ddl)
    print()

def map_data_type(duckdb_type: str) -> str:
    """Map DuckDB data types to PostgreSQL"""
    type_mapping = {
        "INTEGER": "INTEGER",
        "BIGINT": "BIGINT", 
        "TEXT": "TEXT",
        "VARCHAR": "VARCHAR",
        "REAL": "REAL",
        "DOUBLE": "DOUBLE PRECISION",
        "BOOLEAN": "BOOLEAN",
        "TIMESTAMP": "TIMESTAMP",
        "DATE": "DATE",
        "JSON": "JSONB"
    }
    return type_mapping.get(duckdb_type.upper(), "TEXT")
```

## 🔄 **Phase 2: Schema Migration**

### **2.1 Database Schema Creation**

#### **Core Tables Migration**
```sql
-- letters table
CREATE TABLE letters (
    id SERIAL PRIMARY KEY,
    document_name TEXT NOT NULL,
    document_type TEXT,
    document_title TEXT,
    source_file_path TEXT NOT NULL,
    file_size INTEGER,
    file_hash TEXT,
    processing_method TEXT DEFAULT 'production_pipeline',
    processing_time_ms REAL,
    extraction_confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'processed',
    raw_grok_json JSONB,
    ocr_supplementary_json JSONB,
    processing_steps_json JSONB,
    validation_details_json JSONB
);

-- letter_products table
CREATE TABLE letter_products (
    id SERIAL PRIMARY KEY,
    letter_id INTEGER NOT NULL REFERENCES letters(id) ON DELETE CASCADE,
    product_identifier TEXT,
    range_label TEXT,
    subrange_label TEXT,
    product_line TEXT,
    product_description TEXT,
    obsolescence_status TEXT,
    end_of_service_date TEXT,
    replacement_suggestions TEXT,
    confidence_score REAL DEFAULT 0.0,
    validation_status TEXT DEFAULT 'validated'
);

-- letter_product_matches table
CREATE TABLE letter_product_matches (
    id SERIAL PRIMARY KEY,
    letter_id INTEGER NOT NULL REFERENCES letters(id) ON DELETE CASCADE,
    letter_product_id INTEGER NOT NULL REFERENCES letter_products(id) ON DELETE CASCADE,
    ibcatalogue_product_identifier TEXT NOT NULL,
    match_confidence REAL NOT NULL,
    match_reason TEXT,
    technical_match_score REAL DEFAULT 0.0,
    nomenclature_match_score REAL DEFAULT 0.0,
    product_line_match_score REAL DEFAULT 0.0,
    match_type TEXT,
    range_based_matching BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- processing_debug table
CREATE TABLE processing_debug (
    id SERIAL PRIMARY KEY,
    letter_id INTEGER NOT NULL REFERENCES letters(id) ON DELETE CASCADE,
    processing_step TEXT NOT NULL,
    step_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    step_duration_ms REAL,
    step_success BOOLEAN DEFAULT TRUE,
    step_details TEXT,
    error_message TEXT
);
```

#### **Indexes and Constraints**
```sql
-- Performance indexes
CREATE INDEX idx_letters_source_path ON letters(source_file_path);
CREATE INDEX idx_letters_status ON letters(status);
CREATE INDEX idx_letters_file_hash ON letters(file_hash);
CREATE INDEX idx_letters_created_at ON letters(created_at);
CREATE INDEX idx_letters_document_name ON letters(document_name);

CREATE INDEX idx_products_letter_id ON letter_products(letter_id);
CREATE INDEX idx_products_range_label ON letter_products(range_label);
CREATE INDEX idx_products_product_identifier ON letter_products(product_identifier);

CREATE INDEX idx_matches_letter_id ON letter_product_matches(letter_id);
CREATE INDEX idx_matches_product_id ON letter_product_matches(letter_product_id);
CREATE INDEX idx_matches_ibcatalogue_id ON letter_product_matches(ibcatalogue_product_identifier);
CREATE INDEX idx_matches_confidence ON letter_product_matches(match_confidence);

CREATE INDEX idx_debug_letter_id ON processing_debug(letter_id);
CREATE INDEX idx_debug_timestamp ON processing_debug(step_timestamp);
CREATE INDEX idx_debug_step ON processing_debug(processing_step);

-- JSONB indexes for better performance
CREATE INDEX idx_letters_raw_grok_gin ON letters USING GIN (raw_grok_json);
CREATE INDEX idx_letters_validation_details_gin ON letters USING GIN (validation_details_json);
```

### **2.2 Data Type Mapping**
| DuckDB Type | PostgreSQL Type | Notes |
|-------------|----------------|-------|
| `INTEGER PRIMARY KEY DEFAULT nextval('sequence')` | `SERIAL PRIMARY KEY` | Auto-incrementing primary key |
| `TEXT` | `TEXT` | No change needed |
| `REAL` | `REAL` | No change needed |
| `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` | No change needed |
| `JSON` | `JSONB` | Better performance and indexing |

### **2.3 IBcatalogue Integration**
- Keep IBcatalogue as separate DuckDB file (read-only access)
- Create PostgreSQL views or foreign data wrappers if needed
- Implement cross-database queries through application layer

## 📊 **Phase 3: Data Migration**

### **3.1 Data Export from DuckDB**
```python
# scripts/migrate_data_to_postgresql.py
#!/usr/bin/env python3
"""
Data Migration Script - DuckDB to PostgreSQL
Migrates all data while maintaining referential integrity
"""

import duckdb
import psycopg2
import json
import time
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger

class DataMigrator:
    """Handles data migration from DuckDB to PostgreSQL"""
    
    def __init__(self, duckdb_path: str, pg_connection_string: str):
        self.duckdb_path = duckdb_path
        self.pg_connection_string = pg_connection_string
        
    def migrate_all_data(self):
        """Migrate all data in dependency order"""
        logger.info("🚀 Starting data migration from DuckDB to PostgreSQL")
        
        # Connect to databases
        duck_conn = duckdb.connect(self.duckdb_path)
        pg_conn = psycopg2.connect(self.pg_connection_string)
        
        try:
            # Migrate tables in dependency order
            tables = ['letters', 'letter_products', 'letter_product_matches', 'processing_debug']
            
            for table in tables:
                logger.info(f"📊 Migrating table: {table}")
                self._migrate_table(duck_conn, pg_conn, table)
                
            logger.success("✅ Data migration completed successfully")
            
        finally:
            duck_conn.close()
            pg_conn.close()
    
    def _migrate_table(self, duck_conn, pg_conn, table: str):
        """Migrate a single table"""
        start_time = time.time()
        
        # Get data from DuckDB
        data = duck_conn.execute(f"SELECT * FROM {table}").fetchall()
        columns = [desc[0] for desc in duck_conn.description]
        
        if not data:
            logger.info(f"ℹ️ Table {table} is empty, skipping")
            return
        
        # Insert into PostgreSQL
        cursor = pg_conn.cursor()
        
        try:
            # Build INSERT statement
            placeholders = ','.join(['%s'] * len(columns))
            insert_sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
            
            # Execute batch insert
            cursor.executemany(insert_sql, data)
            pg_conn.commit()
            
            duration = time.time() - start_time
            logger.success(f"✅ Migrated {len(data)} records to {table} in {duration:.2f}s")
            
        except Exception as e:
            pg_conn.rollback()
            logger.error(f"❌ Failed to migrate {table}: {e}")
            raise
        finally:
            cursor.close()

def main():
    """Main migration function"""
    duckdb_path = "data/letters.duckdb"
    pg_connection_string = "postgresql://postgres:password@localhost:5432/se_letters"
    
    if not Path(duckdb_path).exists():
        logger.error(f"❌ DuckDB file not found: {duckdb_path}")
        return
    
    migrator = DataMigrator(duckdb_path, pg_connection_string)
    migrator.migrate_all_data()

if __name__ == "__main__":
    main()
```

### **3.2 Data Validation**
```python
# scripts/validate_migration.py
#!/usr/bin/env python3
"""
Migration Validation Script
Validates data integrity after migration
"""

import duckdb
import psycopg2
from typing import Dict, Any

def validate_migration():
    """Validate migration by comparing record counts and sample data"""
    logger.info("🔍 Validating migration...")
    
    # Connect to both databases
    duck_conn = duckdb.connect("data/letters.duckdb")
    pg_conn = psycopg2.connect("postgresql://postgres:password@localhost:5432/se_letters")
    
    tables = ['letters', 'letter_products', 'letter_product_matches', 'processing_debug']
    
    for table in tables:
        # Compare record counts
        duck_count = duck_conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        pg_count = pg_conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        
        if duck_count == pg_count:
            logger.success(f"✅ {table}: {duck_count} records match")
        else:
            logger.error(f"❌ {table}: DuckDB={duck_count}, PostgreSQL={pg_count}")
    
    # Validate foreign key relationships
    validate_foreign_keys(pg_conn)
    
    duck_conn.close()
    pg_conn.close()

def validate_foreign_keys(pg_conn):
    """Validate foreign key relationships"""
    logger.info("🔗 Validating foreign key relationships...")
    
    # Check for orphaned records
    orphaned_products = pg_conn.execute("""
        SELECT COUNT(*) FROM letter_products lp
        LEFT JOIN letters l ON lp.letter_id = l.id
        WHERE l.id IS NULL
    """).fetchone()[0]
    
    if orphaned_products == 0:
        logger.success("✅ No orphaned letter_products records")
    else:
        logger.error(f"❌ Found {orphaned_products} orphaned letter_products records")
```

## 🔧 **Phase 4: Application Code Migration**

### **4.1 Python Services Migration**

#### **4.1.1 Database Connection Layer**
```python
# src/se_letters/core/database.py
import psycopg2
import psycopg2.extras
import asyncpg
from contextlib import contextmanager
from typing import Generator, Any, Dict, List, Optional
from loguru import logger

class PostgreSQLDatabase:
    """PostgreSQL database connection manager"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._pool = None
    
    @contextmanager
    def get_connection(self) -> Generator[psycopg2.extensions.connection, None, None]:
        """Get database connection with automatic cleanup"""
        conn = None
        try:
            conn = psycopg2.connect(self.connection_string)
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute query and return results as list of dictionaries"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(sql, params)
                return [dict(row) for row in cursor.fetchall()]
    
    def execute_command(self, sql: str, params: tuple = None) -> int:
        """Execute command and return affected row count"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                conn.commit()
                return cursor.rowcount
    
    def execute_scalar(self, sql: str, params: tuple = None) -> Any:
        """Execute query and return single value"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                result = cursor.fetchone()
                return result[0] if result else None

class AsyncPostgreSQLDatabase:
    """Async PostgreSQL database connection manager"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._pool = None
    
    async def get_pool(self):
        """Get or create connection pool"""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self.connection_string)
        return self._pool
    
    async def execute_query(self, sql: str, *args) -> List[Dict[str, Any]]:
        """Execute query and return results"""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, *args)
            return [dict(row) for row in rows]
    
    async def execute_command(self, sql: str, *args) -> str:
        """Execute command and return result"""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            return await conn.execute(sql, *args)
    
    async def close(self):
        """Close connection pool"""
        if self._pool:
            await self._pool.close()
```

#### **4.1.2 Letter Database Service Update**
```python
# src/se_letters/services/letter_database_service.py
import json
from typing import Dict, Any, List, Optional
from se_letters.core.database import PostgreSQLDatabase

class LetterDatabaseService:
    """PostgreSQL-based letter database service"""
    
    def __init__(self, connection_string: str):
        self.db = PostgreSQLDatabase(connection_string)
    
    def store_letter(self, letter_data: Dict[str, Any]) -> int:
        """Store letter and return ID"""
        sql = """
            INSERT INTO letters (
                document_name, document_type, document_title, source_file_path,
                file_size, file_hash, processing_method, processing_time_ms,
                extraction_confidence, raw_grok_json, validation_details_json
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        params = (
            letter_data['document_name'],
            letter_data.get('document_type'),
            letter_data.get('document_title'),
            letter_data['source_file_path'],
            letter_data.get('file_size'),
            letter_data.get('file_hash'),
            letter_data.get('processing_method', 'production_pipeline'),
            letter_data.get('processing_time_ms'),
            letter_data.get('extraction_confidence'),
            json.dumps(letter_data.get('raw_grok_json')) if letter_data.get('raw_grok_json') else None,
            json.dumps(letter_data.get('validation_details_json')) if letter_data.get('validation_details_json') else None
        )
        
        return self.db.execute_scalar(sql, params)
    
    def get_letter(self, letter_id: int) -> Optional[Dict[str, Any]]:
        """Get letter by ID"""
        sql = "SELECT * FROM letters WHERE id = %s"
        results = self.db.execute_query(sql, (letter_id,))
        return results[0] if results else None
    
    def search_letters(self, search_query: str = "", page: int = 1, limit: int = 25) -> Dict[str, Any]:
        """Search letters with pagination"""
        offset = (page - 1) * limit
        
        # Build WHERE clause
        where_clause = ""
        params = []
        
        if search_query:
            where_clause = "WHERE document_name ILIKE %s OR document_title ILIKE %s"
            search_pattern = f"%{search_query}%"
            params = [search_pattern, search_pattern]
        
        # Count query
        count_sql = f"SELECT COUNT(*) FROM letters {where_clause}"
        total = self.db.execute_scalar(count_sql, tuple(params))
        
        # Data query
        data_sql = f"""
            SELECT * FROM letters {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        data_params = params + [limit, offset]
        data = self.db.execute_query(data_sql, tuple(data_params))
        
        return {
            "data": data,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
```

### **4.2 Node.js Webapp Migration**

#### **4.2.1 Database Connection Update**
```typescript
// webapp/src/lib/database.ts
import { Pool, PoolClient, QueryResult } from 'pg';

class HighPerformanceDatabase {
  private static instance: HighPerformanceDatabase;
  private pool: Pool;
  private readonly connectionString: string;

  private constructor() {
    this.connectionString = process.env.DATABASE_URL || 
      'postgresql://postgres:password@localhost:5432/se_letters';
    
    this.pool = new Pool({
      connectionString: this.connectionString,
      max: 20,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 2000,
    });

    // Handle pool errors
    this.pool.on('error', (err) => {
      console.error('❌ Unexpected error on idle client', err);
    });
  }

  public static getInstance(): HighPerformanceDatabase {
    if (!HighPerformanceDatabase.instance) {
      HighPerformanceDatabase.instance = new HighPerformanceDatabase();
    }
    return HighPerformanceDatabase.instance;
  }

  public async query<T = any>(sql: string, params: any[] = []): Promise<T[]> {
    const client = await this.pool.connect();
    try {
      const startTime = Date.now();
      const result = await client.query(sql, params);
      const queryTime = Date.now() - startTime;
      
      console.log(`✅ Query completed (${queryTime}ms): ${result.rows.length} rows`);
      return result.rows;
    } finally {
      client.release();
    }
  }

  public async queryOne<T = any>(sql: string, params: any[] = []): Promise<T | null> {
    const results = await this.query<T>(sql, params);
    return results.length > 0 ? results[0] : null;
  }

  public async execute(sql: string, params: any[] = []): Promise<void> {
    const client = await this.pool.connect();
    try {
      const startTime = Date.now();
      await client.query(sql, params);
      const queryTime = Date.now() - startTime;
      
      console.log(`✅ Execute completed (${queryTime}ms)`);
    } finally {
      client.release();
    }
  }

  public async close(): Promise<void> {
    await this.pool.end();
    console.log('✅ Database connection pool closed');
  }

  // High-performance optimized queries
  public async getLetterStatistics(): Promise<any> {
    const sql = `
      SELECT 
        COUNT(*) as total_letters,
        COUNT(CASE WHEN status = 'processed' THEN 1 END) as processed_count,
        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count,
        AVG(extraction_confidence) as avg_confidence,
        AVG(processing_time_ms) as avg_processing_time
      FROM letters
    `;
    return this.queryOne(sql);
  }

  public async searchLetters(searchParams: {
    page: number;
    limit: number;
    search?: string;
    sortBy?: string;
    sortOrder?: string;
  }): Promise<{ data: any[]; total: number }> {
    const { page, limit, search = '', sortBy = 'created_at', sortOrder = 'desc' } = searchParams;
    
    // Build WHERE clause for search
    let whereClause = '';
    let queryParams: any[] = [];
    
    if (search.trim()) {
      whereClause = `
        WHERE document_name ILIKE $1 
           OR document_title ILIKE $1 
           OR source_file_path ILIKE $1
      `;
      queryParams = [`%${search}%`];
    }
    
    // Count query
    const countSql = `
      SELECT COUNT(*) as total
      FROM letters
      ${whereClause}
    `;
    
    const countResult = await this.queryOne<{ total: number }>(countSql, queryParams);
    const total = countResult?.total || 0;
    
    // Data query with pagination
    const offset = (page - 1) * limit;
    const dataSql = `
      SELECT 
        id,
        document_name,
        document_title,
        source_file_path,
        processing_time_ms,
        extraction_confidence,
        created_at,
        status
      FROM letters
      ${whereClause}
      ORDER BY ${sortBy} ${sortOrder.toUpperCase()}
      LIMIT $${queryParams.length + 1} OFFSET $${queryParams.length + 2}
    `;
    
    const dataParams = [...queryParams, limit, offset];
    const data = await this.query(dataSql, dataParams);
    
    return { data, total };
  }
}

// Export singleton instance
export const db = HighPerformanceDatabase.getInstance();
```

## 🧪 **Phase 5: Testing & Validation**

### **5.1 Unit Testing**
```python
# tests/unit/test_postgresql_database.py
import pytest
import psycopg2
from se_letters.core.database import PostgreSQLDatabase

class TestPostgreSQLDatabase:
    """Test PostgreSQL database functionality"""
    
    @pytest.fixture
    def db(self):
        """Create test database connection"""
        connection_string = "postgresql://postgres:password@localhost:5432/se_letters_test"
        return PostgreSQLDatabase(connection_string)
    
    def test_connection(self, db):
        """Test database connection"""
        result = db.execute_scalar("SELECT 1")
        assert result == 1
    
    def test_insert_and_query(self, db):
        """Test insert and query operations"""
        # Insert test data
        insert_sql = "INSERT INTO letters (document_name, source_file_path) VALUES (%s, %s) RETURNING id"
        letter_id = db.execute_scalar(insert_sql, ("test.pdf", "/test/test.pdf"))
        
        # Query test data
        query_sql = "SELECT * FROM letters WHERE id = %s"
        result = db.execute_query(query_sql, (letter_id,))
        
        assert len(result) == 1
        assert result[0]['document_name'] == "test.pdf"
```

### **5.2 Integration Testing**
```python
# tests/integration/test_postgresql_integration.py
import pytest
from se_letters.services.letter_database_service import LetterDatabaseService

class TestPostgreSQLIntegration:
    """Test PostgreSQL integration with services"""
    
    @pytest.fixture
    def service(self):
        """Create test service"""
        connection_string = "postgresql://postgres:password@localhost:5432/se_letters_test"
        return LetterDatabaseService(connection_string)
    
    def test_store_and_retrieve_letter(self, service):
        """Test storing and retrieving letters"""
        # Store letter
        letter_data = {
            'document_name': 'test.pdf',
            'source_file_path': '/test/test.pdf',
            'processing_time_ms': 1000,
            'extraction_confidence': 0.95
        }
        
        letter_id = service.store_letter(letter_data)
        assert letter_id is not None
        
        # Retrieve letter
        letter = service.get_letter(letter_id)
        assert letter is not None
        assert letter['document_name'] == 'test.pdf'
        assert letter['extraction_confidence'] == 0.95
```

## 🚀 **Phase 6: Production Deployment**

### **6.1 Environment Configuration**
```yaml
# config/production.yaml
database:
  postgresql:
    host: ${DB_HOST}
    port: ${DB_PORT:-5432}
    database: ${DB_NAME}
    user: ${DB_USER}
    password: ${DB_PASSWORD}
    pool_size: ${DB_POOL_SIZE:-20}
    connection_timeout: ${DB_CONNECTION_TIMEOUT:-30}
    idle_timeout: ${DB_IDLE_TIMEOUT:-300}
    ssl_mode: ${DB_SSL_MODE:-require}
```

### **6.2 Docker Configuration**
```dockerfile
# Dockerfile.postgresql
FROM postgres:15

# Install extensions
RUN apt-get update && apt-get install -y \
    postgresql-15-postgis-3 \
    && rm -rf /var/lib/apt/lists/*

# Copy initialization scripts
COPY scripts/init-db.sql /docker-entrypoint-initdb.d/
COPY scripts/migrate-schema.sql /docker-entrypoint-initdb.d/

# Environment variables
ENV POSTGRES_DB=se_letters
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=password

# Expose port
EXPOSE 5432
```

### **6.3 Deployment Scripts**
```bash
#!/bin/bash
# scripts/deploy_postgresql.sh

echo "🚀 Deploying PostgreSQL for SE Letters..."

# Start PostgreSQL container
docker-compose up -d postgresql

# Wait for database to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Run schema migration
echo "📊 Running schema migration..."
python scripts/migrate_schema_to_postgresql.py

# Run data migration
echo "📦 Running data migration..."
python scripts/migrate_data_to_postgresql.py

# Validate migration
echo "🔍 Validating migration..."
python scripts/validate_migration.py

echo "✅ PostgreSQL deployment completed!"
```

## 📊 **Phase 7: Performance Optimization**

### **7.1 Connection Pooling**
```python
# src/se_letters/core/connection_pool.py
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager

class ConnectionPool:
    """PostgreSQL connection pool manager"""
    
    def __init__(self, connection_string: str, min_connections: int = 5, max_connections: int = 20):
        self.pool = psycopg2.pool.ThreadedConnectionPool(
            min_connections,
            max_connections,
            connection_string
        )
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool"""
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)
    
    def close(self):
        """Close all connections in pool"""
        self.pool.closeall()
```

### **7.2 Query Optimization**
```sql
-- Add performance indexes
CREATE INDEX CONCURRENTLY idx_letters_created_at_status ON letters(created_at, status);
CREATE INDEX CONCURRENTLY idx_products_letter_range ON letter_products(letter_id, range_label);
CREATE INDEX CONCURRENTLY idx_matches_confidence_type ON letter_product_matches(match_confidence, match_type);

-- Add partial indexes for common queries
CREATE INDEX CONCURRENTLY idx_letters_processed ON letters(id) WHERE status = 'processed';
CREATE INDEX CONCURRENTLY idx_letters_failed ON letters(id) WHERE status = 'failed';

-- Add covering indexes for frequently accessed columns
CREATE INDEX CONCURRENTLY idx_letters_covering ON letters(id, document_name, created_at, status);
```

## 🔄 **Phase 8: Rollback Plan**

### **8.1 Backup Strategy**
```python
# scripts/backup_postgresql.py
#!/usr/bin/env python3
"""
PostgreSQL Backup Script
Creates backups before major changes
"""

import subprocess
import datetime
from pathlib import Path

def backup_postgresql():
    """Create PostgreSQL backup"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backups/se_letters_postgresql_{timestamp}.sql"
    
    # Create backup directory
    Path("backups").mkdir(exist_ok=True)
    
    # Create backup
    cmd = [
        "pg_dump",
        "-h", "localhost",
        "-U", "postgres",
        "-d", "se_letters",
        "-f", backup_file,
        "--verbose"
    ]
    
    subprocess.run(cmd, check=True)
    print(f"✅ Backup created: {backup_file}")

def restore_postgresql(backup_file: str):
    """Restore PostgreSQL from backup"""
    cmd = [
        "psql",
        "-h", "localhost",
        "-U", "postgres",
        "-d", "se_letters",
        "-f", backup_file
    ]
    
    subprocess.run(cmd, check=True)
    print(f"✅ Database restored from: {backup_file}")
```

### **8.2 Rollback Procedures**
1. **Stop all applications** using the database
2. **Restore from backup** using `restore_postgresql()`
3. **Revert configuration** to use DuckDB
4. **Restart applications** with DuckDB configuration
5. **Validate system** is working correctly

## 📈 **Success Metrics**

### **Performance Metrics**
- **Query Response Time**: < 100ms for 95% of queries
- **Concurrent Connections**: Support 50+ simultaneous users
- **Database Uptime**: 99.9% availability
- **Migration Success Rate**: 100% data integrity

### **Operational Metrics**
- **Zero Database Lock Conflicts**: Eliminate concurrent access issues
- **Improved Pipeline Performance**: Faster document processing
- **Better Error Handling**: Graceful failure recovery
- **Enhanced Monitoring**: Real-time database performance tracking

---

**Status**: 📋 **PLANNING COMPLETE**  
**Next Phase**: 🔄 **Schema Migration**  
**Estimated Duration**: 1-2 weeks  
**Risk Level**: 🟡 **Medium** (well-planned, reversible) 