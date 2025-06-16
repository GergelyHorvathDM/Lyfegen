"""
This utility file provides functions for loading and extracting text
from various document formats using LangChain loaders.
"""
import os
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader, TextLoader
from app.core.logging_config import logger

def load_and_extract_text(file_path: str) -> str:
    """
    Loads a document from the given file path and extracts its raw text content.
    
    Args:
        file_path: The local path to the document file.

    Returns:
        The extracted text content as a single string.
        Returns an error message string if the file type is unsupported or fails.
    """
    logger.info(f"Loading and extracting text from: {file_path}")
    file_extension = os.path.splitext(file_path)[1].lower()

    try:
        if file_extension == '.pdf':
            loader = PyPDFLoader(file_path)
        elif file_extension == '.docx':
            loader = UnstructuredWordDocumentLoader(file_path, mode="elements")
        elif file_extension == '.txt':
            loader = TextLoader(file_path)
        else:
            logger.warning(f"Unsupported file type for ad-hoc processing: {file_extension}")
            return f"Unsupported file type: {file_extension}. Please upload a PDF, DOCX, or TXT file."

        docs = loader.load()
        if not docs:
            logger.warning(f"Loader {loader.__class__.__name__} extracted no content.")
            return "Could not extract any content from the uploaded document."
        
        # Combine the content of all loaded document pages/sections
        return "\n\n".join(doc.page_content for doc in docs)

    except Exception as e:
        logger.error(f"Failed to load and extract text from {file_path}: {e}", exc_info=True)
        return f"Failed to process document: {e}" 