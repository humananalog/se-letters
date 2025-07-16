#!/usr/bin/env python3
"""
PostgreSQL Performance Monitoring Script
"""

import psycopg2
from datetime import datetime

def monitor_performance():
    """Monitor database performance"""
    
    conn = psycopg2.connect("postgresql://alexandre@localhost:5432/se_letters_dev")
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
