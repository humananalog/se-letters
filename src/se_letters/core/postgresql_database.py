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
    
    def execute_query(self, sql: str, params: tuple = None, commit: bool = False) -> List[Dict[str, Any]]:
        """Execute query and return results as list of dictionaries"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(sql, params)
                result = [dict(row) for row in cursor.fetchall()]
                if commit:
                    conn.commit()
                return result
    
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
            import asyncpg
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