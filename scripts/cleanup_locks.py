#!/usr/bin/env python3
"""
Database Lock Cleanup Utility
Enhanced version to resolve DuckDB lock conflicts from concurrent processes

This script specifically handles:
1. Next.js webapp holding DuckDB connections
2. Python pipeline processes trying to access the same database
3. Stale processes that may be holding locks
"""

import os
import sys
import time
import psutil
from pathlib import Path

def find_processes_using_database():
    """Find processes that might be using the DuckDB database"""
    try:
        db_processes = []
        
        # Find all processes that might be using the database
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                
                # Check for relevant processes
                keywords = ['next', 'node', 'duckdb', 'production_pipeline', 
                           'se_letters']
                if any(keyword in cmdline.lower() for keyword in keywords):
                    db_processes.append((
                        proc.info['pid'],
                        f"{proc.info['name']}: {cmdline[:100]}..."
                    ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return db_processes
    except Exception as e:
        print(f"❌ Error finding processes: {e}")
        return []

def check_database_lock():
    """Check if database file exists and get info"""
    db_path = Path("data/letters.duckdb")
    
    if not db_path.exists():
        print("✅ Database file does not exist - no lock issues")
        return False
    
    print(f"📁 Database file found: {db_path}")
    print(f"📊 File size: {db_path.stat().st_size} bytes")
    print(f"🕒 Last modified: {time.ctime(db_path.stat().st_mtime)}")
    
    return True

def kill_process_safely(pid):
    """Kill process safely with proper error handling"""
    try:
        proc = psutil.Process(pid)
        print(f"💀 Terminating PID {pid} ({proc.name()})")
        
        # Try graceful termination first
        proc.terminate()
        
        # Wait for graceful shutdown
        try:
            proc.wait(timeout=5)
            print(f"✅ PID {pid} terminated gracefully")
        except psutil.TimeoutExpired:
            # Force kill if graceful termination fails
            print(f"⚠️ Force killing PID {pid}")
            proc.kill()
            proc.wait(timeout=2)
            print(f"✅ PID {pid} force killed")
            
    except psutil.NoSuchProcess:
        print(f"ℹ️ PID {pid} already terminated")
    except psutil.AccessDenied:
        print(f"❌ Access denied to PID {pid}")
    except Exception as e:
        print(f"❌ Error killing PID {pid}: {e}")

def test_database_connection():
    """Test if we can connect to the database"""
    try:
        import duckdb
        conn = duckdb.connect("data/letters.duckdb")
        conn.execute("SELECT 1")
        conn.close()
        print("✅ Database connection test successful")
        return True
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

def check_specific_lock_issue():
    """Check for the specific lock issue we're seeing"""
    print("\n🔍 Checking for specific lock issues...")
    
    # Check for Next.js processes holding DuckDB connections
    nextjs_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'next' in cmdline.lower() and 'duckdb' in cmdline.lower():
                nextjs_processes.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if nextjs_processes:
        print(f"⚠️ Found {len(nextjs_processes)} Next.js processes that may be holding DuckDB connections:")
        for pid in nextjs_processes:
            print(f"  - PID {pid}")
        return nextjs_processes
    
    return []

def main():
    print("🧹 SE LETTERS - ENHANCED DATABASE LOCK CLEANUP UTILITY")
    print("=" * 60)
    
    # Check current directory
    if not Path("data").exists():
        print("❌ Error: Not in project root directory")
        print("Please run this script from the SE_letters directory")
        sys.exit(1)
    
    print("📍 Current directory:", os.getcwd())
    
    # Check database file
    has_db = check_database_lock()
    
    # Check for specific lock issues
    nextjs_processes = check_specific_lock_issue()
    
    # Find all problematic processes
    print("\n🔍 Scanning for database-related processes...")
    processes = find_processes_using_database()
    
    if not processes and not nextjs_processes:
        print("✅ No database-related processes found")
    else:
        all_processes = processes + [(pid, f"Next.js process {pid}") for pid in nextjs_processes]
        print(f"⚠️  Found {len(all_processes)} database-related processes:")
        for pid, cmd in all_processes:
            print(f"  PID {pid}: {cmd}")
        
        # Ask user if they want to kill these processes
        response = input("\n🤔 Kill these processes? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            print("\n💀 Terminating processes...")
            for pid, cmd in all_processes:
                kill_process_safely(pid)
            
            # Wait a moment for processes to clean up
            print("⏳ Waiting for cleanup...")
            time.sleep(3)
        else:
            print("ℹ️  Processes left running")
    
    # Test database connection
    if has_db:
        print("\n🔌 Testing database connection...")
        if test_database_connection():
            print("✅ Database is accessible")
        else:
            print("❌ Database is still locked")
            print("💡 You may need to:")
            print("   1. Restart the webapp: ./scripts/stop_app.sh && ./scripts/start_app.sh")
            print("   2. Check for other Python processes")
            print("   3. Restart your terminal")
            print("   4. Reboot if the issue persists")
    
    print("\n✅ Cleanup completed")

if __name__ == "__main__":
    main() 