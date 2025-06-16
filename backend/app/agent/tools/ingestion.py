"""
This file is used to load and chunk the PDF documents.
"""

import os
from typing import Dict
from langchain_community.document_loaders import PyPDFLoader


def load_document_texts(data_dir: str) -> Dict[str, str]:
    """
    Loads the full text content of each PDF document in the specified directory.

    Args:
        data_dir: The path to the directory containing the raw PDF documents.

    Returns:
        A dictionary mapping each filename to its full text content.
    """
    print(f"Loading documents from: {data_dir}")

    document_texts = {}
    for filename in os.listdir(data_dir):
        if filename.endswith(".pdf"):
            filepath = os.path.join(data_dir, filename)
            try:
                loader = PyPDFLoader(filepath)
                # Load the document pages
                pages = loader.load()
                # Concatenate the content of all pages into a single string
                full_text = "\\n\\n".join([page.page_content for page in pages])
                document_texts[filename] = full_text
                print(f"  - Loaded and extracted text from {filename}")
            except Exception as e:
                print(f"  - Failed to load {filename}: {e}")

    print(f"\nSuccessfully loaded text from {len(document_texts)} documents.")
    return document_texts
