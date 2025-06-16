"""
This file is used to initialize the language models.
"""

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.core.config import settings

# 1. Large, High-performance Embedding Model
# The top-tier embedding model for maximum quality.
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-large",
    openai_api_key=settings.OPENAI_API_KEY
)

# 2. Main, Fast, and Capable Model
# The primary model for most agentic tasks.
main_model = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    openai_api_key=settings.OPENAI_API_KEY
)

# 3. Top-tier Reasoning Model
# NOTE: The 'o1' model is a very new, specialized reasoning model.
# Using a powerful and reliable model like 'gpt-4o' is recommended to ensure stability.
# This model is explicitly configured to return JSON, which is required by the
# category_discovery and other tools.
reasoning_model = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    openai_api_key=settings.OPENAI_API_KEY,
    model_kwargs={"response_format": {"type": "json_object"}},
)

# 4. Model for Raw Text Generation (e.g., SQL)
# This model is for tasks where we need a raw text response, not JSON.
sql_generation_model = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    openai_api_key=settings.OPENAI_API_KEY,
)

# 5. Model for Generating the Final Answer
# This model is not bound to any tools and is used at the end of a graph
# to synthesize the final response to the user based on the chat history.
final_answer_model = ChatOpenAI(
    model="gpt-4o",
    temperature=0.7, # A slightly higher temperature for more natural-sounding responses
    openai_api_key=settings.OPENAI_API_KEY,
)
