# financial_analyzer/core/pdf_processor.py
from typing import List
import os
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter


def load_and_extract_text_from_pdfs(pdf_paths: List[str], upload_dir: str) -> str:
    """Loads and extracts text from multiple PDFs from upload directory."""
    print("DEBUG: Starting load_and_extract_text_from_pdfs")
    all_text = []
    for pdf_path in pdf_paths:
        full_pdf_path = os.path.join(upload_dir, os.path.basename(pdf_path)) # add correct paths.
        print(f"DEBUG: Loading PDF: {full_pdf_path}")
        try:
            loader = PyPDFLoader(file_path=full_pdf_path)
            documents = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            all_text.extend([doc.page_content for doc in text_splitter.split_documents(documents)])
            print(f"DEBUG: Successfully loaded and split text from: {full_pdf_path}")
        except Exception as e:
             print(f"ERROR: Could not load or split text from {full_pdf_path}: {e}")
             continue # Skip to the next file if there is an error

    if not all_text:
        print("DEBUG: No text extracted from any of the provided PDF documents.")
        return None  # return None if no text was extracted

    combined_text = " ".join(all_text)
    print("DEBUG: Finished load_and_extract_text_from_pdfs")
    return combined_text