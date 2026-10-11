"""
eu_ai_act — a tool for navigating, understanding and applying the EU AI Act
(Regulation (EU) 2024/1689).

Provides:
  * Full-text search over articles, recitals and annexes.
  * The Act's own skeleton: chapters, sections and annexes.
  * Risk-tier and actor obligation maps.
  * Compliance checklists with legal citations.
  * Application timeline, penalties, definitions, governance bodies.
  * A citation graph between provisions and corpus statistics.
  * A curated guide layer: classification path, procedures and worked scenarios.
"""
__version__ = "1.1.0"

from . import compliance, data, guides, search, structure  # noqa: F401

__all__ = [
    "compliance",
    "data",
    "guides",
    "search",
    "structure",
    "__version__",
]
