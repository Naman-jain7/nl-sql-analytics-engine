import sqlite3
import pandas as pd
import os
from loguru import logger
from app.schemas.table import TableSchema
from typing import List, Dict, Any, Tuple, Optional

# Constants
DB_DIR = "data"
DB_NAME = "querysight.db"
DB_PATH = os.path.join(DB_DIR, DB_NAME)

# Ensure DB directory exists
os.makedirs(DB_DIR, exist_ok=True)

def get_db_connection():
    """Create and return a database connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Critical error connecting to SQLite database at {DB_PATH}: {e}")
        return None

def create_table(schema: TableSchema) -> bool:
    """
    Creates a table in the database based on the provided TableSchema object.
    Supports Primary Keys, Nullable constraints, and Default values.
    """
    col_defs = []
    for col in schema.columns:
        # Use quoted identifiers for safety
        col_def = f'"{col.name}" {col.dtype}'
        
        if col.pk:
            col_def += " PRIMARY KEY"
        
        if not col.nullable:
            col_def += " NOT NULL"
            
        if col.default_value:
            # Simple heuristic for default value quoting
            # If it's a dynamic function like CURRENT_TIMESTAMP or a number, don't quote
            val = col.default_value.strip()
            is_func = val.upper().startswith("CURRENT_")
            is_num = val.replace('.', '', 1).isdigit()
            
            if is_func or is_num:
                col_def += f" DEFAULT {val}"
            else:
                col_def += f" DEFAULT '{val}'"
                
        col_defs.append(col_def)
    
    # Construct the SQL statement
    sql = f"CREATE TABLE IF NOT EXISTS \"{schema.table_name}\" (\n    " + ",\n    ".join(col_defs) + "\n);"
    
    try:
        with get_db_connection() as conn:
            conn.execute(sql)
            conn.commit()
            logger.info(f"Database: Created table '{schema.table_name}'")
            return True
    except sqlite3.Error as e:
        logger.error(f"Database: Failed to create table '{schema.table_name}': {e}")
        return False

def drop_table(table_name: str) -> bool:
    """Drops a table from the database."""
    sql = f'DROP TABLE IF EXISTS "{table_name}";'
    try:
        with get_db_connection() as conn:
            conn.execute(sql)
            conn.commit()
            logger.info(f"Database: Dropped table '{table_name}'")
            return True
    except sqlite3.Error as e:
        logger.error(f"Database: Failed to drop table '{table_name}': {e}")
        return False

def list_tables() -> List[str]:
    """Returns a list of all user-defined table names in the database."""
    query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(query)
            tables = [row["name"] for row in cursor.fetchall()]
            return tables
    except sqlite3.Error as e:
        logger.error(f"Database: Error listing tables: {e}")
        return []

def execute_query(query: str, params: tuple = ()) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Executes a SQL query and returns the result as a Pandas DataFrame.
    Returns (DataFrame, None) on success, or (None, ErrorMessage) on failure.
    """
    try:
        with get_db_connection() as conn:
            # Use pandas for easy conversion to DataFrame
            df = pd.read_sql_query(query, conn, params=params)
            return df, None
    except Exception as e:
        logger.error(f"Database: Query execution failed: {e}")
        return None, str(e)

def get_table_schema_info(table_name: str) -> List[Dict[str, Any]]:
    """Retrieves metadata (columns, types, etc.) for a specific table."""
    query = f"PRAGMA table_info(\"{table_name}\");"
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Database: Error fetching schema for '{table_name}': {e}")
        return []

def check_table_exists(table_name: str) -> bool:
    """Checks if a table exists in the database."""
    return table_name in list_tables()