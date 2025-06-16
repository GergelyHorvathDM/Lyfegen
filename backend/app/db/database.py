"""
This module handles all database interactions for the Lyfegen AI project.
"""
import json
from typing import Dict, Any, List

import asyncpg
from app.core.config import settings
from app.core.logging_config import logger

async def get_db_connection():
    """Establishes a connection to the database."""
    return await asyncpg.connect(settings.DATABASE_URL)

async def create_table_from_schema(schema_sql: str):
    """
    Executes a CREATE TABLE statement to create a new table in the database.
    It will first drop the table if it already exists.
    """
    conn = await get_db_connection()
    try:
        # Extract table name from schema and sanitize it
        table_name_from_schema = schema_sql.split("CREATE TABLE")[1].strip().split("(")[0].strip()
        sanitized_table_name = table_name_from_schema.replace("&", "and")
        
        # Recreate the schema with the sanitized name
        schema_sql = schema_sql.replace(table_name_from_schema, sanitized_table_name)
        
        logger.info(f"  - Dropping table '{sanitized_table_name}' if it exists...")
        await conn.execute(f"DROP TABLE IF EXISTS {sanitized_table_name} CASCADE;")
        
        logger.info(f"  - Creating table '{sanitized_table_name}'...")
        await conn.execute(schema_sql)
        logger.info(f"  - Successfully created table '{sanitized_table_name}'.")
    except Exception as e:
        logger.error(f"Error creating table: {e}", exc_info=True)
    finally:
        await conn.close()

async def get_table_column_types(conn: asyncpg.Connection, table_name: str) -> Dict[str, str]:
    """Retrieves the column names and their data types for a given table."""
    query = """
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = $1
    """
    rows = await conn.fetch(query, table_name)
    return {row['column_name']: row['data_type'] for row in rows}

async def insert_structured_data(table_name: str, data: Dict[str, Any]):
    """
    Inserts a single record of structured data into the specified table.
    It automatically handles type conversions for array and JSON columns that the
    LLM might return as structured objects or string representations.
    """
    conn = await get_db_connection()
    try:
        column_types = await get_table_column_types(conn, table_name)
        
        columns = data.keys()
        values = []
        for col, value in data.items():
            col_type = column_types.get(col)
            
            # If the target column is an array and the value is a string that looks
            # like a list, parse it into a Python list.
            if col_type and "ARRAY" in col_type.upper() and isinstance(value, str) and value.startswith('[') and value.endswith(']'):
                try:
                    values.append(json.loads(value))
                except json.JSONDecodeError:
                    values.append([value]) # Fallback for malformed JSON string
            # If the value is a dict or list, and the target is not an array,
            # serialize it as a JSON string for storage in TEXT/JSONB columns.
            elif isinstance(value, (dict, list)):
                values.append(json.dumps(value))
            else:
                values.append(value)
        
        columns_str = ", ".join(f'"{c}"' for c in columns)
        placeholders = ", ".join(f"${i+1}" for i in range(len(columns)))
        
        insert_sql = f'INSERT INTO "{table_name}" ({columns_str}) VALUES ({placeholders})'
        
        await conn.execute(insert_sql, *values)
        logger.info(f"  - Successfully inserted data into '{table_name}'.")
        
    except Exception as e:
        logger.error(f"Error inserting data into {table_name}: {e}", exc_info=True)
    finally:
        await conn.close() 