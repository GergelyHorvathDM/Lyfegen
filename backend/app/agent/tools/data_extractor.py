"""
This tool uses a language model to extract structured data from a document
based on a given database schema.
"""
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import json
from app.agent.llm import reasoning_model

EXTRACTION_PROMPT_TEMPLATE = """
You are an expert data extraction agent. Your task is to extract structured information from the provided document text and format it as a JSON object that strictly conforms to the given PostgreSQL table schema.

**Table Schema:**
```sql
{schema_sql}
```

**Document Text:**
---
{document_text}
---

**Instructions:**
1.  Read the document text carefully.
2.  Extract the information required to populate the columns defined in the table schema.
3.  The keys of your JSON object MUST match the column names in the schema.
4.  The data types of the values in your JSON object should be compatible with the column types (e.g., strings for VARCHAR/TEXT, numbers for INT/NUMERIC, 'YYYY-MM-DD' for DATE).
5.  For JSONB fields, extract the relevant information as a nested JSON object.
6.  If a piece of information is not present in the document, use a `null` value for that key.
7.  Do not include the primary key column (e.g., `id`) in your output.

Respond with ONLY the JSON object.

**JSON Output:**
"""

async def extract_structured_data(document_text: str, schema_sql: str) -> Dict[str, Any] | None:
    """
    Extracts structured data from a document based on a given table schema.

    Args:
        document_text: The full text of the document.
        schema_sql: The `CREATE TABLE` statement for the target table.

    Returns:
        A dictionary containing the extracted data, or None if extraction fails.
    """
    prompt = EXTRACTION_PROMPT_TEMPLATE.format(
        schema_sql=schema_sql,
        document_text=document_text
    )

    print("  - Extracting structured data...")
    try:
        response = await reasoning_model.ainvoke(prompt)
        extracted_data = json.loads(response.content)
        
        print("  - Successfully extracted data.")
        return extracted_data
    except json.JSONDecodeError:
        print(f"  - Error: Failed to decode JSON from extraction response: {response.content}")
        return None
    except Exception as e:
        print(f"  - Error during data extraction: {e}")
        return None 