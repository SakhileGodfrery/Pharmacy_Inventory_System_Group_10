import psycopg2
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# Valid table names cache
VALID_TABLES_CACHE = None

def get_db_connection():
    """Get a database connection using DATABASE_URL from environment"""
    try:
        return psycopg2.connect(os.getenv('DATABASE_URL'))
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def get_valid_tables():
    """Get and cache valid table names to prevent SQL injection"""
    global VALID_TABLES_CACHE
    if VALID_TABLES_CACHE is None:
        sql = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """
        results = execute_query(sql, fetch_all=True)
        VALID_TABLES_CACHE = [row[0] for row in results] if results else []
    return VALID_TABLES_CACHE

def validate_table_name(table_name):
    """Validate table name against existing tables"""
    valid_tables = get_valid_tables()
    if table_name not in valid_tables:
        raise ValueError(f"Invalid table name: {table_name}")
    return table_name

def execute_query(sql, params=None, fetch_all=False, fetch_one=False):
    """Execute a SQL query and return results"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
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

def get_table_data(table_name, limit=100, offset=0):
    """Get data from a specific table with pagination"""
    validate_table_name(table_name)
    sql = f'SELECT * FROM "{table_name}" LIMIT %s OFFSET %s'
    try:
        results = execute_query(sql, [limit, offset], fetch_all=True)
        return results if results else []
    except Exception as e:
        logger.error(f"Error getting table data for {table_name}: {e}")
        raise

def get_table_columns(table_name):
    """Get column information for a specific table"""
    validate_table_name(table_name)
    sql = """
        SELECT column_name, data_type, is_nullable, 
               column_default, is_identity
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

def get_primary_key(table_name):
    """Get the primary key column name for a table"""
    validate_table_name(table_name)
    sql = """
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        WHERE tc.constraint_type = 'PRIMARY KEY'
            AND tc.table_schema = 'public'
            AND tc.table_name = %s
        LIMIT 1
    """
    try:
        result = execute_query(sql, [table_name], fetch_one=True)
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error getting primary key for {table_name}: {e}")
        return None

def get_foreign_keys(table_name):
    """Get foreign key relationships for a table"""
    validate_table_name(table_name)
    sql = """
        SELECT
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
            AND tc.table_name = %s
    """
    try:
        results = execute_query(sql, [table_name], fetch_all=True)
        return results if results else []
    except Exception as e:
        logger.error(f"Error getting foreign keys for {table_name}: {e}")
        return []