import os
import logging
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from langchain_core.documents import Document
from app.config import settings
from app.rag.seed_docs import POLICY_DOCUMENTS, seed_policy_documents, SAMPLE_DOCS_DIR
from app.rag.pdf_loader import load_and_split_policy_file

logger = logging.getLogger(__name__)

# Collection Name
COLLECTION_NAME = "health_insurance_policies"


class VectorStoreManager:
    """Manages ChromaDB vector store for policy document indexing and retrieval."""

    def __init__(self):
        self.chroma_dir = settings.CHROMA_DB_DIR
        os.makedirs(self.chroma_dir, exist_ok=True)
        
        # Initialize persistent Chroma client
        self.client = chromadb.PersistentClient(path=self.chroma_dir)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        self.embeddings = self._get_embedding_function()

    def _get_embedding_function(self):
        """Helper to compute dense vectors or use standard Chroma default / OpenAI."""
        if settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY.strip()) > 10:
            try:
                from langchain_openai import OpenAIEmbeddings
                logger.info("Using OpenAI Embeddings for RAG vector store.")
                emb_kwargs = {
                    "model": settings.EMBEDDING_MODEL,
                    "openai_api_key": settings.OPENAI_API_KEY
                }
                if settings.OPENAI_BASE_URL and len(settings.OPENAI_BASE_URL.strip()) > 5:
                    emb_kwargs["base_url"] = settings.OPENAI_BASE_URL.strip()
                return OpenAIEmbeddings(**emb_kwargs)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI Embeddings: {e}. Falling back to default.")
        
        logger.info("Using default embedding model for ChromaDB.")
        return None

    def ingest_all_sample_policies(self):
        """Seed sample policy text documents and populate vector database if empty."""
        count = self.collection.count()
        if count > 0:
            logger.info(f"Vector store already contains {count} documents. Skipping auto-ingest.")
            return

        logger.info("Seeding sample health insurance policy documents into ChromaDB...")
        seed_policy_documents()

        total_chunks = 0
        for doc_info in POLICY_DOCUMENTS:
            file_path = os.path.join(SAMPLE_DOCS_DIR, doc_info["filename"])
            chunks = load_and_split_policy_file(
                file_path=file_path,
                company=doc_info["company"],
                policy_name=doc_info["policy_name"]
            )

            ids = []
            documents_text = []
            metadatas = []

            for idx, chunk in enumerate(chunks):
                chunk_id = f"{chunk.metadata['company']}_{chunk.metadata['policy_name']}_{idx}".replace(" ", "_")
                ids.append(chunk_id)
                documents_text.append(chunk.page_content)
                metadatas.append(chunk.metadata)

            if documents_text:
                self.collection.add(
                    ids=ids,
                    documents=documents_text,
                    metadatas=metadatas
                )
                total_chunks += len(documents_text)

        logger.info(f"Ingestion complete. Total indexed chunks: {total_chunks}")

    def query(
        self,
        query_text: str,
        n_results: int = 4,
        company_filter: Optional[str] = None,
        policy_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query vector database with optional metadata filtering (company, policy_name).
        Returns list of dicts with content, score, and metadata (company, policy_name, page, chunk_id, source).
        """
        # Ensure collection is populated
        if self.collection.count() == 0:
            self.ingest_all_sample_policies()

        where_clause = {}
        if company_filter and company_filter.strip():
            where_clause["company"] = company_filter.strip()
        if policy_filter and policy_filter.strip():
            where_clause["policy_name"] = policy_filter.strip()

        # Chroma query
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where_clause if where_clause else None
        )

        formatted_results = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
            ids = results["ids"][0] if "ids" in results else [""] * len(docs)
            distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(docs)

            for doc_text, meta, chunk_id, dist in zip(docs, metas, ids, distances):
                formatted_results.append({
                    "content": doc_text,
                    "company": meta.get("company", "Unknown Insurer"),
                    "policy_name": meta.get("policy_name", "Health Policy"),
                    "page": meta.get("page", 1),
                    "chunk_id": chunk_id,
                    "source": meta.get("source", "policy_wording.pdf"),
                    "score": round(1.0 - dist, 4) if dist <= 1.0 else round(1.0 / (1.0 + dist), 4),
                    "citation": f"[Company: {meta.get('company')}, Policy: {meta.get('policy_name')}, Page: {meta.get('page')}]"
                })

        return formatted_results


# Global Instance Singleton
vector_store_manager = VectorStoreManager()
