import psycopg2
from psycopg2 import pool
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class DatabasePool:
    _instance = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabasePool, cls).__new__(cls)
            cls._instance._initialize_pool()
        return cls._instance

    def _initialize_pool(self):
        try:
            self._pool = psycopg2.pool.SimpleConnectionPool(
                1, 20,
                database=settings.DATABASES['default']['NAME'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                host=settings.DATABASES['default']['HOST'],
                port=settings.DATABASES['default']['PORT']
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise

    def get_connection(self):
        if self._pool:
            return self._pool.getconn()
        raise Exception("Connection pool not initialized")

    def return_connection(self, conn):
        if self._pool and conn:
            self._pool.putconn(conn)

    def close_all_connections(self):
        if self._pool:
            self._pool.closeall()

# Global database pool instance
db_pool = DatabasePool()

def get_db_connection():
    """Get a database connection from the pool"""
    return db_pool.get_connection()

def return_db_connection(conn):
    """Return a database connection to the pool"""
    db_pool.return_connection(conn)

def execute_query(sql, params=None, fetch_one=False, fetch_all=False):
    """Execute a query and return results"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.rowcount
        
        return result
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Query execution error: {e}\nSQL: {sql}")
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            return_db_connection(conn)

def get_table_data(table_name, limit=100, offset=0, order_by=None):
    """Get data from a specific table"""
    order_clause = f"ORDER BY {order_by}" if order_by else ""
    sql = f"SELECT * FROM {table_name} {order_clause} LIMIT %s OFFSET %s"
    return execute_query(sql, [limit, offset], fetch_all=True)

def get_table_columns(table_name):
    """Get column names for a table"""
    sql = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
    """
    return execute_query(sql, [table_name], fetch_all=True)

def get_table_names():
    """Get all table names in the database"""
    sql = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """
    return execute_query(sql, fetch_all=True)