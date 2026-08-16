"""
RAG + AI interaction layer for the EU AI Act tool.

Provides natural-language capabilities over the Act:
  * ask        — answer a question grounded in retrieved articles/recitals
  * summarize  — summarize a specific article, recital, annex, or a topic
  * list       — list obligations / practices / requirements on a topic
  * compare    — compare two provisions or concepts
  * obligations — list obligations for a given actor or risk tier
  * explain    — plain-language explanation of a provision

Every answer is grounded in the vector store and cites its sources.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import compliance, data, vector_store
from .ai_provider import AIProvider, ProviderError

SYSTEM_PROMPT = (
    "You are an expert assistant on the EU AI Act (Regulation (EU) 2024/1689). "
    "Answer questions accurately and concisely, grounded ONLY in the provided "
    "context. Always cite the specific Article, Recital, or Annex you rely on "
    "(e.g. 'Article 5(1)(a)'). If the context does not contain the answer, say "
    "so clearly rather than guessing. Do not invent legal provisions."
)


def _retrieve_context(query: str, n: int = 6) -> str:
    """Retrieve relevant chunks and format them as context for the model."""
    try:
        results = vector_store.query(query, n_results=n)
    except Exception as e:
        msg = str(e).lower()
        if "readonly" in msg or "read-only" in msg or "read only" in msg:
            raise ProviderError(
                "The vector store database is not writable. Make sure the Chroma "
                "directory is writable, or rebuild it with the 'ai embed' command."
            ) from e
        raise ProviderError(f"Vector store query failed: {e}") from e
    if not results:
        return ""
    parts = []
    for r in results:
        title = f" ({r['title']})" if r.get("title") else ""
        parts.append(f"[{r['ref']}{title}]\n{r['text']}")
    return "\n\n".join(parts)


def _run(messages: List[Dict[str, str]], **kwargs: Any) -> str:
    provider = AIProvider()
    try:
        return provider.chat(messages, **kwargs)
    finally:
        provider.close()


def ask(question: str, n: int = 6) -> Dict[str, Any]:
    """Answer a question grounded in the Act."""
    context = _retrieve_context(question, n=n)
    if not context:
        return {
            "answer": "No relevant context found. Build the vector store first with `eu-ai-act ai embed`.",
            "sources": [],
        }
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Context from the EU AI Act:\n\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer the question using only the context above. Cite your sources.",
        },
    ]
    answer = _run(messages)
    sources = _extract_sources(context)
    return {"answer": answer, "sources": sources}


def summarize(target: str, n: int = 6) -> Dict[str, Any]:
    """Summarize a specific provision or a topic."""
    # If target looks like a provision reference, fetch it directly.
    direct = _direct_provision(target)
    if direct:
        context = f"[{direct['ref']}]\n{direct['text']}"
        sources = [direct["ref"]]
    else:
        context = _retrieve_context(target, n=n)
        sources = _extract_sources(context)
    if not context:
        return {
            "answer": "No content found to summarize. Build the vector store first with `eu-ai-act ai embed`.",
            "sources": [],
        }
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Content from the EU AI Act:\n\n{context}\n\n"
            f"Provide a clear, concise summary of the following: {target}. "
            "Highlight the key obligations or points and cite the relevant provisions.",
        },
    ]
    answer = _run(messages)
    return {"answer": answer, "sources": sources}


def list_items(topic: str, n: int = 8) -> Dict[str, Any]:
    """List obligations / practices / requirements on a topic."""
    context = _retrieve_context(topic, n=n)
    if not context:
        return {
            "answer": "No relevant content found. Build the vector store first with `eu-ai-act ai embed`.",
            "sources": [],
        }
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Context from the EU AI Act:\n\n{context}\n\n"
            f"List the key items related to: {topic}. "
            "Format as a numbered list, each item citing its Article/Recital/Annex.",
        },
    ]
    answer = _run(messages)
    return {"answer": answer, "sources": _extract_sources(context)}


def compare(a: str, b: str, n: int = 8) -> Dict[str, Any]:
    """Compare two provisions or concepts."""
    context_a = _retrieve_context(a, n=n // 2)
    context_b = _retrieve_context(b, n=n // 2)
    context = f"--- {a} ---\n{context_a}\n\n--- {b} ---\n{context_b}"
    if not context.strip():
        return {
            "answer": "No relevant content found. Build the vector store first with `eu-ai-act ai embed`.",
            "sources": [],
        }
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Context from the EU AI Act:\n\n{context}\n\n"
            f"Compare '{a}' and '{b}'. Highlight similarities, differences, and "
            "which provisions apply to each. Cite your sources.",
        },
    ]
    answer = _run(messages)
    return {"answer": answer, "sources": _extract_sources(context)}


def obligations(actor: Optional[str] = None, tier: Optional[str] = None) -> Dict[str, Any]:
    """List obligations for an actor or risk tier (uses the curated dataset)."""
    items = compliance.obligations_for(actor=actor, tier=tier)
    if not items:
        return {"answer": "No obligations found for that filter.", "sources": []}
    lines = []
    for o in items:
        lines.append(f"- **{o['title']}** ({o['ref']}) — {o['description']}")
    answer = "\n".join(lines)
    sources = sorted({o["ref"] for o in items})
    return {"answer": answer, "sources": sources}


def explain(provision: str) -> Dict[str, Any]:
    """Plain-language explanation of a specific provision."""
    direct = _direct_provision(provision)
    if not direct:
        return {
            "answer": f"Could not find provision '{provision}'. Try e.g. 'Article 5', 'Recital 12', 'Annex III'.",
            "sources": [],
        }
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Provision text:\n\n[{direct['ref']}]\n{direct['text']}\n\n"
            f"Explain {direct['ref']} in plain, accessible language. "
            "Summarize what it requires, who it applies to, and any key nuances.",
        },
    ]
    answer = _run(messages)
    return {"answer": answer, "sources": [direct["ref"]]}


# -- helpers ---------------------------------------------------------------
def _direct_provision(target: str) -> Optional[Dict[str, Any]]:
    """Fetch a provision directly by reference (e.g. 'Article 5', 'Recital 12', 'Annex III')."""
    t = target.strip()
    low = t.lower()
    parts = t.split()
    if low.startswith("article"):
        if len(parts) < 2:
            return None
        num = parts[1]
        art = data.get_article(num)
        if art:
            return {"ref": f"Article {num}", "text": art["text"]}
    elif low.startswith("recital"):
        if len(parts) < 2:
            return None
        try:
            num = int(parts[1])
        except ValueError:
            return None
        rec = data.get_recital(num)
        if rec:
            return {"ref": f"Recital {num}", "text": rec["text"]}
    elif low.startswith("annex"):
        if len(parts) < 2:
            return None
        num = parts[1].upper()
        ann = data.get_annex(num)
        if ann:
            return {"ref": f"Annex {num}", "text": ann["text"]}
    return None


def _extract_sources(context: str) -> List[str]:
    """Extract provision references from a context block."""
    import re

    refs = re.findall(r"\[(Article \d+[a-z]?(?:\(\d+\)(?:[a-z])?)?|Recital \d+|Annex [IVX]+)\]", context)
    seen = []
    for r in refs:
        if r not in seen:
            seen.append(r)
    return seen
