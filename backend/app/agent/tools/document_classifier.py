"""
This tool classifies a document into one of the predefined categories.
"""
import json
from typing import List
from app.agent.llm import reasoning_model
from langchain_core.prompts import ChatPromptTemplate

CLASSIFICATION_PROMPT_TEMPLATE = """
You are an expert document classifier. Your task is to classify the following document into ONE of the provided categories.

Analyze the document text and determine which single category best represents its primary subject matter.

Available Categories:
---
{category_list}
---

Document Text:
---
{document_text}
---

Respond with a JSON object containing a single key "category" with the name of the chosen category. It MUST be one of the categories from the provided list.

JSON Response:
"""

async def classify_document(document_text: str, categories: List[str]) -> str | None:
    """
    Classifies the document into one of the given categories.

    Args:
        document_text: The full text of the document to classify.
        categories: A list of available category names.

    Returns:
        The name of the chosen category, or None if classification fails.
    """
    category_list_str = "\n".join(f"- {c}" for c in categories)
    prompt = CLASSIFICATION_PROMPT_TEMPLATE.format(
        category_list=category_list_str,
        document_text=document_text[:8000]  # Use a slice of the text to avoid exceeding token limits
    )

    print(f"  - Classifying document...")
    try:
        response = await reasoning_model.ainvoke(prompt)
        response_json = json.loads(response.content)
        chosen_category = response_json.get("category")

        if chosen_category and chosen_category in categories:
            print(f"  - Classified as: '{chosen_category}'")
            return chosen_category
        else:
            print(f"  - Warning: Model returned an invalid category: {chosen_category}")
            return None
    except Exception as e:
        print(f"  - Error during classification: {e}")
        return None 