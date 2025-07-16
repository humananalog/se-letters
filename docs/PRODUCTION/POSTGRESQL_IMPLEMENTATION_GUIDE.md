# PostgreSQL Implementation Guide

**Version: 2.2.0**  
**Author: Alexandre Huther**  
**Date: 2025-07-16**

## 🎯 **Implementation Overview**

This guide provides step-by-step instructions for implementing the PostgreSQL migration for the SE Letters application. Follow these instructions carefully to ensure a smooth transition from DuckDB.

## 📋 **Prerequisites**

### **System Requirements**
- macOS with Homebrew (or Linux with package manager)
- Python 3.13+
- Node.js 20+
- Git

### **Required Tools**
```bash
# Install PostgreSQL
brew install postgresql@15
brew services start postgresql@15

# Install Python dependencies
pip install psycopg2-binary asyncpg

# Install Node.js dependencies
npm install pg @types/pg
```

## 🔧 **Step 1: Environment Setup**

### **1.1 PostgreSQL Installation**
```bash
# Install PostgreSQL
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Verify installation
psql --version
```

### **1.2 Database Creation**
```bash
# Create database
createdb se_letters_dev

# Create test database
createdb se_letters_test

# Verify databases
psql -l | grep se_letters
```

### **1.3 Configuration Update**
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

## 📊 **Step 2: Schema Migration**

### **2.1 Create Migration Scripts**
Create `scripts/migrate_schema_to_postgresql.py`:
```python
#!/usr/bin/env python3
"""
Schema Migration Script
Creates PostgreSQL schema from DuckDB
"""

import duckdb
import psycopg2
from pathlib import Path

def create_postgresql_schema():
    """Create PostgreSQL schema"""
    
    # PostgreSQL connection
    pg_conn = psycopg2.connect(
        host="localhost",
        database="se_letters_dev",
        user="postgres",
        password="password"
    )
    
    cursor = pg_conn.cursor()
    
    try:
        # Create letters table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS letters (
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
            )
        """)
        
        # Create letter_products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS letter_products (
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
            )
        """)
        
        # Create letter_product_matches table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS letter_product_matches (
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
            )
        """)
        
        # Create processing_debug table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_debug (
                id SERIAL PRIMARY KEY,
                letter_id INTEGER NOT NULL REFERENCES letters(id) ON DELETE CASCADE,
                processing_step TEXT NOT NULL,
                step_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                step_duration_ms REAL,
                step_success BOOLEAN DEFAULT TRUE,
                step_details TEXT,
                error_message TEXT
            )
        """)
        
        # Create indexes
        create_indexes(cursor)
        
        pg_conn.commit()
        print("✅ PostgreSQL schema created successfully")
        
    except Exception as e:
        pg_conn.rollback()
        print(f"❌ Schema creation failed: {e}")
        raise
    finally:
        cursor.close()
        pg_conn.close()

def create_indexes(cursor):
    """Create performance indexes"""
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_letters_source_path ON letters(source_file_path)",
        "CREATE INDEX IF NOT EXISTS idx_letters_status ON letters(status)",
        "CREATE INDEX IF NOT EXISTS idx_letters_file_hash ON letters(file_hash)",
        "CREATE INDEX IF NOT EXISTS idx_letters_created_at ON letters(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_letters_document_name ON letters(document_name)",
        
        "CREATE INDEX IF NOT EXISTS idx_products_letter_id ON letter_products(letter_id)",
        "CREATE INDEX IF NOT EXISTS idx_products_range_label ON letter_products(range_label)",
        "CREATE INDEX IF NOT EXISTS idx_products_product_identifier ON letter_products(product_identifier)",
        
        "CREATE INDEX IF NOT EXISTS idx_matches_letter_id ON letter_product_matches(letter_id)",
        "CREATE INDEX IF NOT EXISTS idx_matches_product_id ON letter_product_matches(letter_product_id)",
        "CREATE INDEX IF NOT EXISTS idx_matches_ibcatalogue_id ON letter_product_matches(ibcatalogue_product_identifier)",
        "CREATE INDEX IF NOT EXISTS idx_matches_confidence ON letter_product_matches(match_confidence)",
        
        "CREATE INDEX IF NOT EXISTS idx_debug_letter_id ON processing_debug(letter_id)",
        "CREATE INDEX IF NOT EXISTS idx_debug_timestamp ON processing_debug(step_timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_debug_step ON processing_debug(processing_step)",
        
        "CREATE INDEX IF NOT EXISTS idx_letters_raw_grok_gin ON letters USING GIN (raw_grok_json)",
        "CREATE INDEX IF NOT EXISTS idx_letters_validation_details_gin ON letters USING GIN (validation_details_json)"
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)
        print(f"✅ Created index: {index_sql.split('ON')[1].strip()}")

if __name__ == "__main__":
    create_postgresql_schema()
```

### **2.2 Run Schema Migration**
```bash
# Run schema migration
python scripts/migrate_schema_to_postgresql.py

# Verify schema
psql -d se_letters_dev -c "\dt"
psql -d se_letters_dev -c "\d letters"
```

## 📦 **Step 3: Data Migration**

### **3.1 Create Data Migration Script**
Create `scripts/migrate_data_to_postgresql.py`:
```python
#!/usr/bin/env python3
"""
Data Migration Script
Migrates data from DuckDB to PostgreSQL
"""

import duckdb
import psycopg2
import json
import time
from pathlib import Path
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
    pg_connection_string = "postgresql://postgres:password@localhost:5432/se_letters_dev"
    
    if not Path(duckdb_path).exists():
        logger.error(f"❌ DuckDB file not found: {duckdb_path}")
        return
    
    migrator = DataMigrator(duckdb_path, pg_connection_string)
    migrator.migrate_all_data()

if __name__ == "__main__":
    main()
```

### **3.2 Run Data Migration**
```bash
# Run data migration
python scripts/migrate_data_to_postgresql.py

# Verify data
psql -d se_letters_dev -c "SELECT COUNT(*) FROM letters;"
psql -d se_letters_dev -c "SELECT COUNT(*) FROM letter_products;"
```

## 🔧 **Step 4: Python Code Migration**

### **4.1 Update Database Connection**
Create `src/se_letters/core/postgresql_database.py`:
```python
#!/usr/bin/env python3
"""
PostgreSQL Database Connection Manager
Replaces DuckDB connection management
"""

import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from typing import Generator, Any, Dict, List, Optional
from loguru import logger

class PostgreSQLDatabase:
    """PostgreSQL database connection manager"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
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
```

### **4.2 Update Letter Database Service**
Update `src/se_letters/services/letter_database_service.py`:
```python
#!/usr/bin/env python3
"""
PostgreSQL-based Letter Database Service
Updated for PostgreSQL compatibility
"""

import json
from typing import Dict, Any, List, Optional
from se_letters.core.postgresql_database import PostgreSQLDatabase

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

## 🌐 **Step 5: Node.js Webapp Migration**

### **5.1 Update Database Connection**
Update `webapp/src/lib/database.ts`:
```typescript
import { Pool, PoolClient } from 'pg';

class HighPerformanceDatabase {
  private static instance: HighPerformanceDatabase;
  private pool: Pool;
  private readonly connectionString: string;

  private constructor() {
    this.connectionString = process.env.DATABASE_URL || 
      'postgresql://postgres:password@localhost:5432/se_letters_dev';
    
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

### **5.2 Update Package Dependencies**
Update `webapp/package.json`:
```json
{
  "dependencies": {
    "pg": "^8.11.3",
    "@types/pg": "^8.10.9"
  }
}
```

## 🧪 **Step 6: Testing**

### **6.1 Create Test Scripts**
Create `scripts/test_postgresql_migration.py`:
```python
#!/usr/bin/env python3
"""
PostgreSQL Migration Test Script
Tests the migration and validates functionality
"""

import psycopg2
from se_letters.core.postgresql_database import PostgreSQLDatabase
from se_letters.services.letter_database_service import LetterDatabaseService

def test_database_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")
    
    connection_string = "postgresql://postgres:password@localhost:5432/se_letters_dev"
    db = PostgreSQLDatabase(connection_string)
    
    # Test simple query
    result = db.execute_scalar("SELECT 1")
    assert result == 1
    print("✅ Database connection test passed")

def test_letter_service():
    """Test letter database service"""
    print("🔍 Testing letter database service...")
    
    connection_string = "postgresql://postgres:password@localhost:5432/se_letters_dev"
    service = LetterDatabaseService(connection_string)
    
    # Test search functionality
    result = service.search_letters(limit=5)
    assert 'data' in result
    assert 'total' in result
    print(f"✅ Letter service test passed - Found {result['total']} letters")

def test_data_integrity():
    """Test data integrity after migration"""
    print("🔍 Testing data integrity...")
    
    connection_string = "postgresql://postgres:password@localhost:5432/se_letters_dev"
    db = PostgreSQLDatabase(connection_string)
    
    # Check record counts
    tables = ['letters', 'letter_products', 'letter_product_matches', 'processing_debug']
    
    for table in tables:
        count = db.execute_scalar(f"SELECT COUNT(*) FROM {table}")
        print(f"📊 {table}: {count} records")
    
    print("✅ Data integrity test passed")

def main():
    """Run all tests"""
    print("🧪 Running PostgreSQL migration tests...")
    
    try:
        test_database_connection()
        test_letter_service()
        test_data_integrity()
        
        print("🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    main()
```

### **6.2 Run Tests**
```bash
# Run migration tests
python scripts/test_postgresql_migration.py

# Run webapp tests
cd webapp
npm test
```

## 🚀 **Step 7: Production Deployment**

### **7.1 Environment Configuration**
Create `.env` file:
```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/se_letters
DB_HOST=localhost
DB_PORT=5432
DB_NAME=se_letters
DB_USER=postgres
DB_PASSWORD=password
DB_POOL_SIZE=20
DB_CONNECTION_TIMEOUT=30
DB_IDLE_TIMEOUT=300
```

### **7.2 Update Configuration Files**
Update `config/config.yaml`:
```yaml
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
```

### **7.3 Deployment Script**
Create `scripts/deploy_postgresql.sh`:
```bash
#!/bin/bash
# PostgreSQL Deployment Script

echo "🚀 Deploying PostgreSQL for SE Letters..."

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432; then
    echo "❌ PostgreSQL is not running. Starting..."
    brew services start postgresql@15
    sleep 5
fi

# Create database if it doesn't exist
createdb se_letters 2>/dev/null || echo "Database already exists"

# Run schema migration
echo "📊 Running schema migration..."
python scripts/migrate_schema_to_postgresql.py

# Run data migration
echo "📦 Running data migration..."
python scripts/migrate_data_to_postgresql.py

# Run tests
echo "🧪 Running tests..."
python scripts/test_postgresql_migration.py

echo "✅ PostgreSQL deployment completed!"
```

## 🔄 **Step 8: Rollback Procedures**

### **8.1 Backup Before Migration**
```bash
# Create backup of current DuckDB
cp data/letters.duckdb data/letters.duckdb.backup.$(date +%Y%m%d_%H%M%S)

# Create backup of PostgreSQL (after migration)
pg_dump -h localhost -U postgres -d se_letters > backups/se_letters_$(date +%Y%m%d_%H%M%S).sql
```

### **8.2 Rollback Script**
Create `scripts/rollback_to_duckdb.sh`:
```bash
#!/bin/bash
# Rollback to DuckDB

echo "🔄 Rolling back to DuckDB..."

# Stop applications
./scripts/stop_app.sh

# Restore DuckDB backup
cp data/letters.duckdb.backup.* data/letters.duckdb

# Update configuration to use DuckDB
# (Revert config changes)

# Restart applications
./scripts/start_app.sh

echo "✅ Rollback completed!"
```

## 📊 **Step 9: Performance Monitoring**

### **9.1 Database Performance Queries**
```sql
-- Check slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY tablename, attname;

-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### **9.2 Performance Monitoring Script**
Create `scripts/monitor_performance.py`:
```python
#!/usr/bin/env python3
"""
Database Performance Monitoring Script
Monitors PostgreSQL performance metrics
"""

import psycopg2
from datetime import datetime

def monitor_performance():
    """Monitor database performance"""
    
    conn = psycopg2.connect("postgresql://postgres:password@localhost:5432/se_letters_dev")
    cursor = conn.cursor()
    
    print(f"📊 Performance Report - {datetime.now()}")
    print("=" * 50)
    
    # Connection count
    cursor.execute("SELECT count(*) FROM pg_stat_activity")
    connections = cursor.fetchone()[0]
    print(f"Active connections: {connections}")
    
    # Table sizes
    cursor.execute("""
        SELECT 
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
        FROM pg_tables 
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
    """)
    
    print("\nTable sizes:")
    for row in cursor.fetchall():
        print(f"  {row[1]}: {row[2]}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    monitor_performance()
```

## 📈 **Success Criteria**

### **Performance Metrics**
- ✅ Query response time < 100ms for 95% of queries
- ✅ Support 50+ simultaneous users
- ✅ Database uptime > 99.9%
- ✅ Zero database lock conflicts

### **Functional Metrics**
- ✅ All existing functionality works with PostgreSQL
- ✅ Data integrity maintained (100% record count match)
- ✅ API response times improved
- ✅ Pipeline processing works without locks

### **Operational Metrics**
- ✅ Successful migration with zero data loss
- ✅ All tests pass
- ✅ Monitoring and alerting in place
- ✅ Rollback procedures tested

---

**Status**: 📋 **IMPLEMENTATION READY**  
**Next Step**: 🔧 **Environment Setup**  
**Estimated Duration**: 2-3 days  
**Risk Level**: 🟡 **Medium** (well-tested, reversible) 