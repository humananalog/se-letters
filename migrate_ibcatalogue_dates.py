#!/usr/bin/env python3
"""
SOTA Database Migration Script for IBcatalogue Date Fields
- Converts date fields to ISO format (YYYY-MM-DD)
- Replaces 4000-12-31 00:00:00 placeholders with NULL
- Maintains created_at as datetime with time
- Includes backup, validation, and rollback capabilities
"""

import duckdb
import datetime
import os
import shutil
from pathlib import Path


class IBcatalogueDateMigration:
    def __init__(self, db_path="data/IBcatalogue.duckdb"):
        self.db_path = Path(db_path)
        self.backup_path = self.db_path.with_suffix('.duckdb.backup')
        self.date_fields = [
            'end_of_production_date',
            'end_of_commercialisation', 
            'service_obsolescence_date',
            'end_of_service_date'
        ]
        self.placeholder = '4000-12-31 00:00:00'
        
    def create_backup(self):
        """Create a timestamped backup of the database."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{self.db_path.stem}_backup_{timestamp}.duckdb"
        backup_path = self.db_path.parent / backup_name
        
        print(f"📦 Creating backup: {backup_path}")
        shutil.copy2(self.db_path, backup_path)
        return backup_path
        
    def validate_database(self):
        """Validate database structure and data integrity."""
        print("🔍 Validating database structure...")
        
        with duckdb.connect(str(self.db_path)) as conn:
            # Check if table exists
            tables = conn.execute("SHOW TABLES").fetchall()
            if not tables or 'products' not in [t[0] for t in tables]:
                raise ValueError("Products table not found")
                
            # Check if date fields exist
            columns = conn.execute("PRAGMA table_info(products)").fetchall()
            column_names = [col[1] for col in columns]
            
            for field in self.date_fields:
                if field not in column_names:
                    raise ValueError(f"Date field {field} not found in products table")
                    
            # Count total records
            total = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            print(f"✅ Database validation passed: {total:,} records found")
            
    def analyze_before_migration(self):
        """Analyze current state before migration."""
        print("\n📊 Pre-migration Analysis:")
        
        with duckdb.connect(str(self.db_path)) as conn:
            for field in self.date_fields:
                total = conn.execute(f"SELECT COUNT(*) FROM products").fetchone()[0]
                placeholders = conn.execute(
                    f"SELECT COUNT(*) FROM products WHERE {field} = ?", 
                    [self.placeholder]
                ).fetchone()[0]
                
                print(f"  {field}: {placeholders:,}/{total:,} placeholders ({placeholders/total*100:.1f}%)")
                
    def migrate_dates(self, dry_run=True):
        """Migrate date fields to ISO format and replace placeholders with NULL."""
        print(f"\n{'🔬 DRY RUN' if dry_run else '🚀 MIGRATION'} - Converting date fields...")
        
        with duckdb.connect(str(self.db_path)) as conn:
            # Start transaction
            conn.execute("BEGIN TRANSACTION")
            
            try:
                for field in self.date_fields:
                    print(f"  Processing {field}...")
                    
                    # Update placeholders to NULL
                    placeholder_update = f"""
                        UPDATE products 
                        SET {field} = NULL 
                        WHERE {field} = ?
                    """
                    placeholder_count = conn.execute(
                        f"SELECT COUNT(*) FROM products WHERE {field} = ?", 
                        [self.placeholder]
                    ).fetchone()[0]
                    
                    if not dry_run:
                        conn.execute(placeholder_update, [self.placeholder])
                    print(f"    Placeholders → NULL: {placeholder_count:,} records")
                    
                    # Convert remaining dates to ISO format (YYYY-MM-DD)
                    iso_update = f"""
                        UPDATE products 
                        SET {field} = SUBSTR({field}, 1, 10)
                        WHERE {field} IS NOT NULL 
                          AND LENGTH({field}) = 19 
                          AND {field} LIKE '____-__-__ __:__:__'
                    """
                    
                    # Count records that will be updated
                    iso_count = conn.execute(f"""
                        SELECT COUNT(*) FROM products 
                        WHERE {field} IS NOT NULL 
                          AND LENGTH({field}) = 19 
                          AND {field} LIKE '____-__-__ __:__:__'
                    """).fetchone()[0]
                    
                    if not dry_run:
                        conn.execute(iso_update)
                    print(f"    ISO conversion: {iso_count:,} records")
                    
                if not dry_run:
                    conn.execute("COMMIT")
                    print("✅ Migration completed successfully")
                else:
                    conn.execute("ROLLBACK")
                    print("✅ Dry run completed - no changes made")
                    
            except Exception as e:
                conn.execute("ROLLBACK")
                print(f"❌ Migration failed: {e}")
                raise
                
    def validate_after_migration(self):
        """Validate data after migration."""
        print("\n🔍 Post-migration validation...")
        
        with duckdb.connect(str(self.db_path)) as conn:
            for field in self.date_fields:
                # Check for remaining placeholders
                remaining_placeholders = conn.execute(
                    f"SELECT COUNT(*) FROM products WHERE {field} = ?", 
                    [self.placeholder]
                ).fetchone()[0]
                
                # Check for proper ISO format
                invalid_format = conn.execute(f"""
                    SELECT COUNT(*) FROM products 
                    WHERE {field} IS NOT NULL 
                      AND (LENGTH({field}) != 10 OR {field} NOT LIKE '____-__-__')
                """).fetchone()[0]
                
                # Sample values
                sample_values = conn.execute(f"""
                    SELECT DISTINCT {field} FROM products 
                    WHERE {field} IS NOT NULL 
                    LIMIT 5
                """).fetchall()
                
                print(f"  {field}:")
                print(f"    Remaining placeholders: {remaining_placeholders}")
                print(f"    Invalid format: {invalid_format}")
                print(f"    Sample values: {[v[0] for v in sample_values]}")
                
    def run_migration(self, dry_run=True):
        """Run the complete migration process."""
        print("🗄️ IBcatalogue Date Migration")
        print("=" * 50)
        
        try:
            # Step 1: Validate database
            self.validate_database()
            
            # Step 2: Create backup (if not dry run)
            if not dry_run:
                backup_path = self.create_backup()
                print(f"✅ Backup created: {backup_path}")
            
            # Step 3: Analyze current state
            self.analyze_before_migration()
            
            # Step 4: Run migration
            self.migrate_dates(dry_run=dry_run)
            
            # Step 5: Validate results
            self.validate_after_migration()
            
            print(f"\n{'🔬 DRY RUN COMPLETED' if dry_run else '🚀 MIGRATION COMPLETED'}")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            raise


def main():
    """Main migration function."""
    db_path = "data/IBcatalogue.duckdb"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    print("=" * 60)
    print("🗄️  IBcatalogue Date Field Migration")
    print("=" * 60)
    
    # Auto-confirm for automated execution
    print(f"\n⚠️  This will modify the database at: {db_path}")
    print(f"   - Convert date fields to ISO format (YYYY-MM-DD)")
    print(f"   - Replace placeholder dates (4000-12-31) with NULL")
    print(f"   - Keep created_at as datetime with full timestamp")
    print(f"   - Create backup before changes")
    
    # Auto-confirm for automated execution
    print(f"\n🤖 Auto-confirming migration...")
    
    # Execute migration
    success = migrate_date_fields(db_path)
    
    if success:
        print(f"\n🎉 Migration completed successfully!")
        print(f"📊 Database is now using SOTA date management practices")
    else:
        print(f"\n❌ Migration failed - check logs above")
    
    return success


if __name__ == "__main__":
    import sys
    
    # Check command line arguments
    dry_run = '--dry-run' in sys.argv or len(sys.argv) == 1
    
    if '--execute' in sys.argv:
        dry_run = False
    
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    if not dry_run:
        response = input("⚠️  This will modify the database. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            sys.exit(0)
    
    # Run migration
    migrator = IBcatalogueDateMigration()
    migrator.run_migration(dry_run=dry_run) 