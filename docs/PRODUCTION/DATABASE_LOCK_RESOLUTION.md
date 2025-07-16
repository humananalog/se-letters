# Database Lock Resolution Guide

**Version: 2.2.0**  
**Author: Alexandre Huther**  
**Date: 2025-07-16**

## 🚨 **ISSUE OVERVIEW**

The SE Letters application experiences database lock conflicts when multiple processes try to access the DuckDB database simultaneously. This is a common issue in production environments where the webapp and pipeline processes need concurrent database access.

## 🔍 **ROOT CAUSE ANALYSIS**

### **Primary Issue: Concurrent DuckDB Connections**
- **Next.js Webapp**: Holds persistent DuckDB connections via Node.js DuckDB driver
- **Python Pipeline**: Tries to establish new DuckDB connections during document processing
- **DuckDB Limitation**: DuckDB doesn't allow multiple write connections to the same database file

### **Error Pattern**
```
IO Error: Could not set lock on file "/Users/alexandre/workshop/devApp/SE_letters/data/letters.duckdb": 
Conflicting lock is held in /opt/homebrew/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/Resources/Python.app/Contents/MacOS/Python (PID 8420) by user alexandre.
```

### **Process Identification**
```bash
# Check which processes are holding database locks
lsof data/letters.duckdb

# Typical output:
COMMAND  PID      USER   FD   TYPE DEVICE SIZE/OFF      NODE NAME
node    8069 alexandre   31u   REG   1,16  9973760 189987503 data/letters.duckdb
```

## 🛠️ **SOLUTIONS**

### **Solution 1: Connection Pooling (Implemented)**

**File**: `webapp/src/lib/database.ts`

**Changes Made**:
- Implemented connection pooling with max 5 connections
- Added connection reuse mechanism
- Proper connection release after each query
- Graceful connection management

**Benefits**:
- Prevents connection exhaustion
- Reduces lock conflicts
- Better resource management
- Improved performance

### **Solution 2: Enhanced Lock Cleanup (Implemented)**

**File**: `scripts/cleanup_locks.py`

**Enhancements**:
- Better process detection using `psutil`
- Specific handling of Next.js processes
- Graceful process termination
- Comprehensive error handling

**Usage**:
```bash
python scripts/cleanup_locks.py
```

### **Solution 3: Database Mutex in Webapp APIs (Implemented)**

**Files**: 
- `webapp/src/app/api/letter-database/[id]/route.ts`
- `webapp/src/app/api/letters/route.ts`

**Implementation**:
```typescript
class DatabaseMutex {
  private queue: Array<() => void> = [];
  private locked = false;

  async acquire(): Promise<void> {
    return new Promise((resolve) => {
      if (!this.locked) {
        this.locked = true;
        resolve();
      } else {
        this.queue.push(resolve);
      }
    });
  }

  release(): void {
    if (this.queue.length > 0) {
      const next = this.queue.shift()!;
      next();
    } else {
      this.locked = false;
    }
  }
}
```

## 🔧 **IMMEDIATE RESOLUTION STEPS**

### **Step 1: Stop All Processes**
```bash
./scripts/stop_app.sh
```

### **Step 2: Clean Up Locks**
```bash
python scripts/cleanup_locks.py
```

### **Step 3: Restart Application**
```bash
./scripts/start_app.sh
```

### **Step 4: Test Database Access**
```bash
python -c "import duckdb; conn = duckdb.connect('data/letters.duckdb'); print('✅ Database accessible'); conn.close()"
```

## 📋 **PREVENTION STRATEGIES**

### **1. Connection Management**
- Use connection pooling in webapp
- Implement proper connection cleanup
- Avoid persistent connections when possible

### **2. Process Coordination**
- Use database mutex for critical operations
- Implement retry logic with exponential backoff
- Add proper error handling for lock conflicts

### **3. Monitoring**
- Monitor database connections
- Track lock conflicts
- Implement health checks

### **4. Development Workflow**
- Always use `./scripts/stop_app.sh` before restarting
- Run `cleanup_locks.py` if issues persist
- Test database connectivity after changes

## 🚀 **PRODUCTION DEPLOYMENT CONSIDERATIONS**

### **1. Environment Setup**
- Ensure proper file permissions
- Configure connection limits
- Set up monitoring and alerting

### **2. Scaling Considerations**
- Use read replicas for heavy read workloads
- Implement connection pooling at application level
- Consider database sharding for large datasets

### **3. Backup and Recovery**
- Regular database backups
- Test recovery procedures
- Document lock resolution procedures

## 📊 **MONITORING AND ALERTING**

### **Key Metrics to Monitor**
- Database connection count
- Lock conflict frequency
- Query response times
- Process memory usage

### **Alerting Rules**
- Lock conflicts > 5 per hour
- Database connection count > 80% of limit
- Query response time > 5 seconds
- Process memory usage > 1GB

## 🔄 **TROUBLESHOOTING WORKFLOW**

### **When Lock Issues Occur**

1. **Check Current State**
   ```bash
   lsof data/letters.duckdb
   ps aux | grep -E "(next|python|duckdb)"
   ```

2. **Identify Problematic Processes**
   ```bash
   python scripts/cleanup_locks.py
   ```

3. **Graceful Shutdown**
   ```bash
   ./scripts/stop_app.sh
   ```

4. **Force Cleanup (if needed)**
   ```bash
   python scripts/cleanup_locks.py
   # Answer 'y' to kill processes
   ```

5. **Restart Application**
   ```bash
   ./scripts/start_app.sh
   ```

6. **Verify Resolution**
   ```bash
   python -c "import duckdb; conn = duckdb.connect('data/letters.duckdb'); conn.close(); print('✅ Fixed')"
   ```

## 📈 **PERFORMANCE OPTIMIZATION**

### **1. Query Optimization**
- Use proper indexes
- Implement query caching
- Optimize database schema

### **2. Connection Optimization**
- Tune connection pool size
- Implement connection timeouts
- Use connection pooling effectively

### **3. Process Optimization**
- Minimize database connections per process
- Implement proper cleanup procedures
- Use async/await for database operations

## 🎯 **SUCCESS CRITERIA**

### **Immediate Goals**
- ✅ No database lock conflicts during normal operation
- ✅ Successful document processing without interruptions
- ✅ Stable webapp performance
- ✅ Proper error handling and recovery

### **Long-term Goals**
- 📊 99.9% uptime for database operations
- 📊 < 100ms average query response time
- 📊 < 1 lock conflict per day
- 📊 Comprehensive monitoring and alerting

## 📚 **REFERENCES**

- [DuckDB Concurrency Documentation](https://duckdb.org/docs/stable/connect/concurrency)
- [Node.js DuckDB Driver](https://github.com/duckdb/duckdb-nodejs)
- [Python DuckDB Documentation](https://duckdb.org/docs/api/python/overview)

---

**Status**: ✅ **IMPLEMENTED**  
**Last Updated**: 2025-07-16  
**Next Review**: 2025-08-16 