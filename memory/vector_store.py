"""ChromaDB persistent vector store for research summary caching."""

from datetime import datetime, timezone
import uuid

import chromadb

from config import CHROMA_PERSIST_DIR


class VectorStore:
    """Local persistent ChromaDB store for research summaries."""

    COLLECTION_NAME = "research_summaries"

    def __init__(self) -> None:
        self._client = None
        self._collection = None

    def _ensure_collection(self):
        if self._collection is not None:
            return
        try:
            self._client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
            self._collection = self._client.get_or_create_collection(
                name=self.COLLECTION_NAME,
            )
        except Exception:
            self._client = None
            self._collection = None

    def store_summary(self, topic: str, sub_question: str, summary: str) -> None:
        """Embed and store a summary with topic metadata."""
        try:
            self._ensure_collection()
            if self._collection is None:
                return
            doc_id = str(uuid.uuid4())
            self._collection.add(
                documents=[summary],
                ids=[doc_id],
                metadatas=[
                    {
                        "topic": topic,
                        "sub_question": sub_question,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ],
            )
        except Exception:
            pass

    def retrieve_relevant(self, topic: str, n_results: int = 3) -> list[str]:
        """Query for the n most similar summaries to the topic."""
        try:
            self._ensure_collection()
            if self._collection is None:
                return []
            count = self._collection.count()
            if count == 0:
                return []
            results = self._collection.query(
                query_texts=[topic],
                n_results=min(n_results, count),
            )
            documents = results.get("documents", [[]])
            if not documents or not documents[0]:
                return []
            return list(documents[0])
        except Exception:
            return []

    def get_summaries_for_topic(self, topic: str) -> list[str]:
        """Return all stored summaries for an exact topic match."""
        try:
            self._ensure_collection()
            if self._collection is None:
                return []
            results = self._collection.get(where={"topic": topic})
            documents = results.get("documents", [])
            return list(documents) if documents else []
        except Exception:
            return []

    def has_cached_report(self, topic: str) -> bool:
        """Return True if 3+ summaries exist for this exact topic."""
        try:
            self._ensure_collection()
            if self._collection is None:
                return False
            results = self._collection.get(where={"topic": topic})
            documents = results.get("documents", [])
            return len(documents) >= 3 if documents else False
        except Exception:
            return False
