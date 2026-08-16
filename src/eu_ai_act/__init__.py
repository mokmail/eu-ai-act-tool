"""
eu_ai_act — a tool for navigating, understanding and applying the EU AI Act
(Regulation (EU) 2024/1689).

Provides:
  * Full-text search over articles, recitals and annexes.
  * Risk-tier and actor obligation maps.
  * Compliance checklists with legal citations.
  * Application timeline, penalties, definitions, governance bodies.
"""
__version__ = "1.0.0"

from . import compliance, data, search  # noqa: F401

__all__ = ["compliance", "data", "search", "__version__"]
