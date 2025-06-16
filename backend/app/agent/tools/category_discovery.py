"""
This file is used to discover potential document categories.
"""
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List
import json
from app.agent.llm import reasoning_model

# A prompt template for the category discovery task.
CATEGORY_PROMPT_TEMPLATE = """
Based on the following content from one or more legal or healthtech documents, please suggest 3-5 potential **high-level, thematic** category names.
These categories should represent broad classifications of the document's purpose, not specific subtypes.

Examples of good high-level categories: 
- "Healthcare Service Agreements"
- "Financial & Reimbursement Agreements"
- "Regulatory & Compliance Documents"
- "Intellectual Property Agreements"

Return your answer as a JSON object with a single key "categories" which contains a list of the suggested category strings.

Document Content:
---
{document_content}
---

JSON Response:
"""

async def discover_categories(document_content: str) -> List[str]:
    """
    Analyzes document content to discover a list of potential categories.

    Args:
        document_content: A string containing the combined text of documents.

    Returns:
        A list of unique, sorted category names.
    """
    print("  - Awaiting category discovery response from the model...")
    prompt = CATEGORY_PROMPT_TEMPLATE.format(document_content=document_content)
    
    try:
        response = await reasoning_model.ainvoke(prompt)
        print("  - Response received.")
        
        # The response should be a JSON string.
        response_json = json.loads(response.content)
        
        # Extract the list of categories
        suggested_list = response_json.get("categories", [])
        
        if not isinstance(suggested_list, list):
            print(f"  - Unexpected format for categories: {suggested_list}")
            return []
            
        # Sanitize and unique the categories
        unique_categories = sorted(list(set([cat.strip() for cat in suggested_list if isinstance(cat, str) and cat.strip()])))
        
        print(f"  - Successfully extracted {len(unique_categories)} unique categories.")
        return unique_categories

    except json.JSONDecodeError:
        print(f"  - Error: Failed to decode JSON from model response: {response.content}")
        return []
    except Exception as e:
        print(f"  - An unexpected error occurred during category discovery: {e}")
        return [] 