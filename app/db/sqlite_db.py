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
    """
    col_defs = []
    for col in schema.columns:
        col_def = f'"{col.name}" {col.dtype}'
        if col.pk: 
            col_def += " PRIMARY KEY"
        if not col.nullable: 
            col_def += " NOT NULL"
        if col.default_value:
            val = col.default_value.strip()
            is_func = val.upper().startswith("CURRENT_")
            is_num = val.replace('.', '', 1).isdigit()
            if is_func or is_num: 
                col_def += f" DEFAULT {val}"
            else: 
                col_def += f" DEFAULT '{val}'"
        col_defs.append(col_def)
    
    sql = f"CREATE TABLE IF NOT EXISTS \"{schema.table_name}\" (\n    " + ",\n    ".join(col_defs) + "\n);"
    
    conn = get_db_connection()
    if not conn: 
        return False
    try:
        conn.execute(sql)
        conn.commit()
        logger.info(f"Database: Created table '{schema.table_name}'")
        return True
    except sqlite3.Error as e:
        logger.error(f"Database: Failed to create table '{schema.table_name}': {e}")
        return False
    finally:
        conn.close()

def execute_query(query: str, params: tuple = ()) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Executes a SQL query and returns the result as a Pandas DataFrame.
    Supports both SELECT (reading) and DML/DDL (writing/modifying) queries.
    """
    if not query or not isinstance(query, str):
        return None, "Invalid or empty query generated."

    conn = get_db_connection()
    if conn is None:
        return None, "Could not connect to database."
    
    try:
        cursor = conn.execute(query, params)
        
        # If the query returns a result set (SELECT, PRAGMA, etc.)
        if cursor.description:
            columns = [column[0] for column in cursor.description]
            data = cursor.fetchall()
            df = pd.DataFrame(data, columns=columns)
            return df, None
        else:
            # For non-returning queries like ALTER, UPDATE, DELETE, INSERT
            conn.commit()
            return pd.DataFrame({"Status": ["Command executed successfully"]}), None
            
    except Exception as e:
        logger.error(f"Database: Query execution failed: {e}")
        return None, str(e)
    finally:
        conn.close()

def list_tables() -> List[str]:
    """Returns a list of all user-defined table names in the database."""
    query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    conn = get_db_connection()
    if not conn: 
        return []
    try:
        cursor = conn.execute(query)
        tables = [row["name"] for row in cursor.fetchall()]
        return tables
    except sqlite3.Error:
        return []
    finally:
        conn.close()

def get_table_schema_info(table_name: str) -> List[Dict[str, Any]]:
    """Retrieves metadata (columns, types, etc.) for a specific table."""
    query = f"PRAGMA table_info(\"{table_name}\");"
    conn = get_db_connection()
    if not conn: 
        return []
    try:
        cursor = conn.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error:
        return []
    finally:
        conn.close()

def check_table_exists(table_name: str) -> bool:
    """Checks if a table exists in the database."""
    return table_name in list_tables()