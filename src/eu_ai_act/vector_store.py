"""
Hardened vector store for the EU AI Act.

Builds and queries a persistent ChromaDB collection that embeds the full text
of the Act (articles, recitals, annexes) using a local Ollama embedding model.
The store is durable: once built, queries do not recompute embeddings.

The store lives at ~/.local/share/eu-ai-act/chroma/ by default (overridable via
EU_AI_ACT_CHROMA_DIR). A build manifest records the source data hash and the
embedding model used, so the store is only rebuilt when the source or model
changes.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from .ai_provider import AIProvider, ProviderConfig

DEFAULT_CHROMA_DIR = os.path.join(
    os.path.expanduser("~"), ".local", "share", "eu-ai-act", "chroma"
)
CHROMA_DIR = os.environ.get("EU_AI_ACT_CHROMA_DIR", DEFAULT_CHROMA_DIR)
COLLECTION_NAME = "eu_ai_act"
MANIFEST_FILE = os.path.join(CHROMA_DIR, "manifest.json")


class OllamaEmbeddingFunction:
    """ChromaDB embedding function backed by a local Ollama model."""

    def __init__(self, provider: AIProvider):
        self._provider = provider

    def __call__(self, input: List[str]) -> List[List[float]]:
        return self._provider.embed(input)

    def embed_query(self, input: str) -> List[List[float]]:
        # ChromaDB expects embed_query to return a list of embeddings
        # (one per query). It may pass a plain string or a (nested) list;
        # normalise to a single query string and return a list of one embedding.
        if isinstance(input, list):
            if input and isinstance(input[0], list):
                input = input[0][0]
            elif input:
                input = input[0]
        return self._provider.embed([input])

    def embed_documents(self, input: List[str]) -> List[List[float]]:
        # ChromaDB may pass a nested list; flatten.
        if input and isinstance(input[0], list):
            input = [item for sub in input for item in sub]
        return self._provider.embed(input)

    def name(self) -> str:
        return self._provider.config.embed_model


def _source_hash() -> str:
    """Hash of the raw dataset, used to detect source changes."""
    from . import data

    raw = data.load_raw()
    blob = json.dumps(
        {
            "articles": raw.get("articles", []),
            "recitals": raw.get("recitals", []),
            "annexes": raw.get("annexes", []),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _chunk_text(text: str, max_chars: int = 2000) -> List[str]:
    """Split long text into overlapping chunks for embedding."""
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    overlap = 200
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return chunks


def _build_documents() -> List[Dict[str, Any]]:
    """Build the list of documents to embed from the raw dataset."""
    from . import data

    docs: List[Dict[str, Any]] = []
    for num, art in data.articles().items():
        for i, chunk in enumerate(_chunk_text(art["text"])):
            docs.append(
                {
                    "id": f"art-{num}-{i}",
                    "text": chunk,
                    "ref": f"Article {num}",
                    "title": art["title"],
                    "kind": "article",
                }
            )
    for num, rec in data.recitals().items():
        for i, chunk in enumerate(_chunk_text(rec["text"])):
            docs.append(
                {
                    "id": f"rec-{num}-{i}",
                    "text": chunk,
                    "ref": f"Recital {num}",
                    "title": "",
                    "kind": "recital",
                }
            )
    for num, ann in data.annexes().items():
        for i, chunk in enumerate(_chunk_text(ann["text"])):
            docs.append(
                {
                    "id": f"ann-{num}-{i}",
                    "text": chunk,
                    "ref": f"Annex {num}",
                    "title": ann["title"],
                    "kind": "annex",
                }
            )
    return docs


def _manifest() -> Optional[Dict[str, Any]]:
    if os.path.exists(MANIFEST_FILE):
        try:
            with open(MANIFEST_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
    return None


def _write_manifest(embed_model: str, source_hash: str, count: int) -> None:
    os.makedirs(CHROMA_DIR, exist_ok=True)
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "embed_model": embed_model,
                "source_hash": source_hash,
                "document_count": count,
                "collection": COLLECTION_NAME,
            },
            f,
            indent=2,
        )


def _get_client():
    import chromadb

    os.makedirs(CHROMA_DIR, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_DIR)


def build(force: bool = False, progress: bool = True) -> Dict[str, Any]:
    """
    Build (or rebuild) the vector store.

    Skips if the store is already up to date (same source hash + embed model),
    unless force=True.
    """
    from . import data

    provider = AIProvider()
    try:
        if not provider.is_available():
            raise RuntimeError(
                "Ollama is not reachable. Start it with `ollama serve` and ensure "
                f"the embedding model '{provider.config.embed_model}' is pulled."
            )
        source_hash = _source_hash()
        embed_model = provider.config.embed_model
        manifest = _manifest()
        if not force and manifest and manifest.get("source_hash") == source_hash and manifest.get("embed_model") == embed_model:
            return {
                "status": "up_to_date",
                "document_count": manifest.get("document_count", 0),
                "embed_model": embed_model,
                "path": CHROMA_DIR,
            }

        docs = _build_documents()
        if progress:
            print(f"Embedding {len(docs)} chunks with '{embed_model}'...")

        client = _get_client()
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=OllamaEmbeddingFunction(provider),
            metadata={"hnsw:space": "cosine"},
        )

        # Batch to avoid huge single requests
        batch_size = 32
        for i in range(0, len(docs), batch_size):
            batch = docs[i : i + batch_size]
            collection.add(
                ids=[d["id"] for d in batch],
                documents=[d["text"] for d in batch],
                metadatas=[
                    {
                        "ref": d["ref"],
                        "title": d["title"],
                        "kind": d["kind"],
                    }
                    for d in batch
                ],
            )
            if progress:
                print(f"  {min(i + batch_size, len(docs))}/{len(docs)}")

        _write_manifest(embed_model, source_hash, len(docs))
        return {
            "status": "built",
            "document_count": len(docs),
            "embed_model": embed_model,
            "path": CHROMA_DIR,
        }
    finally:
        provider.close()


def query(
    query_text: str,
    n_results: int = 5,
    where: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Semantic search over the vector store.

    Returns a list of {ref, title, kind, text, distance} dicts.
    """
    provider = AIProvider()
    try:
        client = _get_client()
        collection = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=OllamaEmbeddingFunction(provider),
        )
        res = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where,
        )
        results = []
        ids = res.get("ids", [[]])[0]
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        for i in range(len(ids)):
            meta = metas[i] or {}
            results.append(
                {
                    "id": ids[i],
                    "ref": meta.get("ref", ""),
                    "title": meta.get("title", ""),
                    "kind": meta.get("kind", ""),
                    "text": docs[i],
                    "distance": dists[i] if i < len(dists) else None,
                }
            )
        return results
    finally:
        provider.close()


def status() -> Dict[str, Any]:
    """Report the current state of the vector store."""
    manifest = _manifest()
    if not manifest:
        return {"status": "not_built", "path": CHROMA_DIR}
    return {
        "status": "built",
        "document_count": manifest.get("document_count", 0),
        "embed_model": manifest.get("embed_model", ""),
        "source_hash": manifest.get("source_hash", ""),
        "path": CHROMA_DIR,
    }
