#!/usr/bin/env python3
"""
Database Lock Cleanup Utility
Helps resolve DuckDB lock conflicts by identifying and cleaning up stale processes
"""

import os
import sys
import signal
import subprocess
import time
from pathlib import Path

def find_processes_using_database():
    """Find processes that might be using the DuckDB database"""
    try:
        # Find Python processes that might be using the database
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        db_processes = []
        for line in lines:
            if ('python' in line.lower() and 
                ('production_pipeline' in line or 'se_letters' in line or 'duckdb' in line)):
                parts = line.split()
                if len(parts) > 1:
                    try:
                        pid = int(parts[1])
                        db_processes.append((pid, line.strip()))
                    except ValueError:
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
    """Safely kill a process"""
    try:
        # First try graceful termination
        os.kill(pid, signal.SIGTERM)
        time.sleep(2)
        
        # Check if process is still running
        try:
            os.kill(pid, 0)  # This doesn't kill, just checks if process exists
            print(f"⚠️  Process {pid} still running, using SIGKILL")
            os.kill(pid, signal.SIGKILL)
            time.sleep(1)
        except ProcessLookupError:
            print(f"✅ Process {pid} terminated gracefully")
            return True
            
    except ProcessLookupError:
        print(f"✅ Process {pid} was already terminated")
        return True
    except PermissionError:
        print(f"❌ Permission denied to kill process {pid}")
        return False
    except Exception as e:
        print(f"❌ Error killing process {pid}: {e}")
        return False
    
    return True

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

def main():
    print("🧹 SE LETTERS - DATABASE LOCK CLEANUP UTILITY")
    print("=" * 50)
    
    # Check current directory
    if not Path("data").exists():
        print("❌ Error: Not in project root directory")
        print("Please run this script from the SE_letters directory")
        sys.exit(1)
    
    print("📍 Current directory:", os.getcwd())
    
    # Check database file
    has_db = check_database_lock()
    
    # Find problematic processes
    print("\n🔍 Scanning for database-related processes...")
    processes = find_processes_using_database()
    
    if not processes:
        print("✅ No database-related processes found")
    else:
        print(f"⚠️  Found {len(processes)} database-related processes:")
        for pid, cmd in processes:
            print(f"  PID {pid}: {cmd[:100]}...")
        
        # Ask user if they want to kill these processes
        response = input("\n🤔 Kill these processes? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            print("\n💀 Terminating processes...")
            for pid, cmd in processes:
                print(f"Killing PID {pid}...")
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
            print("   1. Check for other Python processes")
            print("   2. Restart your terminal")
            print("   3. Reboot if the issue persists")
    
    print("\n✅ Cleanup completed")

if __name__ == "__main__":
    main() 