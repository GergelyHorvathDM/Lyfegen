"""
This tool uses a language model to dynamically design a PostgreSQL table schema
based on the content of a document.
"""
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from app.agent.llm import sql_generation_model
from app.core.logging_config import logger

# A prompt template for the schema design task.
SCHEMA_PROMPT_TEMPLATE = """
You are an expert database administrator specializing in both HealthTech and LegalTech. Your task is to design a PostgreSQL table schema based on the provided document text.

The table name should be a lowercase, snake_cased version of the document category: "{category_name}".

Analyze the following document text and propose a PostgreSQL `CREATE TABLE` statement.
The schema should capture the most critical, structured information from the document.
Key fields to consider are parties involved, effective dates, termination dates, monetary values, policy numbers, medical codes, and important terms.

**VERY IMPORTANT RULES:**
1.  For any column that holds an identifier, number, or code (e.g., 'agreement_number', 'policy_number'), ALWAYS use the `TEXT` data type to avoid length issues.
2.  For contract durations, create a column named `duration_years` and use the `INTEGER` data type.
3.  For columns that will hold descriptive text, names, or clauses whose length is uncertain, ALWAYS use the `TEXT` data type instead of `VARCHAR`.
4.  Use `JSONB` for complex, nested data or key-value pairs like reimbursement rates.
5.  Use `DATE` for specific dates.

Document Category: {category_name}

Document Text Sample:
---
{document_text}
---

Provide ONLY the `CREATE TABLE` statement and nothing else.

Example:
CREATE TABLE managed_care_contract (
    id SERIAL PRIMARY KEY,
    contract_name TEXT,
    provider_name TEXT,
    payer_name TEXT,
    effective_date DATE,
    termination_date DATE,
    reimbursement_rates JSONB,
    covered_services TEXT[],
    state_jurisdiction VARCHAR(100)
);
"""

async def design_schema_for_category(document_content: str, category: str) -> str:
    """
    Generates a PostgreSQL CREATE TABLE statement for a given document category.

    Args:
        document_content: The combined text of documents for context.
        category: The name of the document category (e.g., "Employment Agreement").

    Returns:
        A string containing the `CREATE TABLE` SQL statement.
    """
    snake_cased_category = category.lower().replace(" ", "_").replace("-", "_").replace("&", "and")
    
    prompt = SCHEMA_PROMPT_TEMPLATE.format(
        category_name=snake_cased_category,
        document_text=document_content
    )
    
    logger.info(f"  - Designing schema for category: '{category}'...")
    response = await sql_generation_model.ainvoke(prompt)
    
    # The model should return just the SQL statement. We do some light cleaning.
    sql_statement = response.content.strip()

    # The model sometimes wraps the SQL in a markdown block, so we need to remove it.
    if sql_statement.startswith("```sql"):
        sql_statement = sql_statement.replace("```sql", "", 1).strip()
    if sql_statement.startswith("```"):
        sql_statement = sql_statement.replace("```", "", 1).strip()
    if sql_statement.endswith("```"):
        sql_statement = sql_statement.rsplit("```", 1)[0].strip()
    
    # A simple validation to ensure it looks like a CREATE TABLE statement
    if not sql_statement.upper().startswith("CREATE TABLE"):
        logger.warning(f"  - Warning: Model output for '{category}' doesn't look like a CREATE TABLE statement. Got:\n{sql_statement}")
        # Return None or an empty string to signal failure
        return None
        
    logger.info(f"  - Successfully designed schema for '{category}'.")
    return sql_statement 