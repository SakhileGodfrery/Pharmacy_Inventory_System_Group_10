import psycopg2
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a database connection using Django settings"""
    try:
        conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT']
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def execute_query(sql, params=None, fetch_all=False, fetch_one=False):
    """Execute a SQL query and return results"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Execute the query
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        
        # Check if this is a SELECT query (has results)
        if cursor.description:
            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            else:
                result = cursor.fetchall()
            conn.commit()
            return result
        else:
            # For INSERT, UPDATE, DELETE queries
            conn.commit()
            return cursor.rowcount
            
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Query execution error: {e}\nSQL: {sql}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_table_names():
    """Get all table names from the database"""
    sql = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """
    try:
        results = execute_query(sql, fetch_all=True)
        return results if results else []
    except Exception as e:
        logger.error(f"Error getting table names: {e}")
        return []

def get_table_data(table_name, limit=100):
    """Get data from a specific table"""
    sql = f'SELECT * FROM "{table_name}" LIMIT %s'
    try:
        results = execute_query(sql, [limit], fetch_all=True)
        return results if results else []
    except Exception as e:
        logger.error(f"Error getting table data for {table_name}: {e}")
        raise

def get_table_columns(table_name):
    """Get column information for a specific table"""
    sql = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = %s
        ORDER BY ordinal_position
    """
    try:
        results = execute_query(sql, [table_name], fetch_all=True)
        return results if results else []
    except Exception as e:
        logger.error(f"Error getting columns for {table_name}: {e}")
        raise