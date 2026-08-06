import os
import uuid
from typing import List, Dict, Any
from langchain_core.documents import Document

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


def load_and_split_policy_file(file_path: str, company: str, policy_name: str) -> List[Document]:
    """
    Parse policy file (PDF or TXT) and split into page-aware chunk Documents 
    enriched with metadata (company, policy_name, page, chunk_id, source).
    """
    documents: List[Document] = []
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Policy file not found: {file_path}")

    filename = os.path.basename(file_path)

    # 1. Handle PDF files
    if file_path.endswith(".pdf") and PYPDF_AVAILABLE:
        try:
            reader = PdfReader(file_path)
            for page_idx, page in enumerate(reader.pages):
                text = page.extract_text()
                if not text or not text.strip():
                    continue
                
                # Further split page text into chunks if page is long
                paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
                for p_idx, para in enumerate(paragraphs):
                    chunk_id = f"{policy_name.lower().replace(' ', '_')}_p{page_idx + 1}_c{p_idx + 1}"
                    doc = Document(
                        page_content=para,
                        metadata={
                            "company": company,
                            "policy_name": policy_name,
                            "page": page_idx + 1,
                            "chunk_id": chunk_id,
                            "source": filename,
                            "file_path": file_path
                        }
                    )
                    documents.append(doc)
        except Exception as e:
            print(f"[PDFLoader] Warning reading PDF {file_path}: {e}")

    # 2. Handle Text files (or fallback text)
    if not documents or file_path.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        pages_raw = content.split("--- PAGE SEPARATOR ---")
        for page_idx, page_text in enumerate(pages_raw):
            page_num = page_idx + 1
            paragraphs = [p.strip() for p in page_text.split("\n\n") if p.strip()]
            for p_idx, para in enumerate(paragraphs):
                chunk_id = f"{policy_name.lower().replace(' ', '_')}_p{page_num}_c{p_idx + 1}"
                doc = Document(
                    page_content=para,
                    metadata={
                        "company": company,
                        "policy_name": policy_name,
                        "page": page_num,
                        "chunk_id": chunk_id,
                        "source": filename,
                        "file_path": file_path
                    }
                )
                documents.append(doc)

    print(f"[PDFLoader] Processed {file_path} -> {len(documents)} document chunks.")
    return documents
