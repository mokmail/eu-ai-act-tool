"""
Command-line interface for the EU AI Act tool.

Usage examples:
    eu-ai-act search "human oversight"
    eu-ai-act article 5
    eu-ai-act recital 12
    eu-ai-act annex III
    eu-ai-act tier high_risk
    eu-ai-act actor provider
    eu-ai-act checklist provider
    eu-ai-act timeline
    eu-ai-act penalties
    eu-ai-act definitions
    eu-ai-act classify "facial recognition for recruitment"
    eu-ai-act governance
    eu-ai-act crossrefs
    eu-ai-act citation
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from . import ai_provider, ai_rag, compliance, data, search, vector_store


# --- Output helpers --------------------------------------------------------
def _print_header(text: str) -> None:
    print(f"\n{'=' * 72}")
    print(text)
    print("=" * 72)


def _print_ref(ref: str) -> None:
    print(f"\n  [Legal basis: {ref}]")


def _print_article(num: str) -> None:
    art = data.get_article(num)
    if not art:
        print(f"Article {num} not found.")
        return
    _print_header(f"Article {num} — {art['title']}")
    print(art["text"])
    _print_ref(f"Article {num} of Regulation (EU) 2024/1689")


def _print_recital(num: int) -> None:
    rec = data.get_recital(num)
    if not rec:
        print(f"Recital {num} not found.")
        return
    _print_header(f"Recital {num}")
    print(rec["text"])
    _print_ref(f"Recital {num} of Regulation (EU) 2024/1689")


def _print_annex(num: str) -> None:
    ann = data.get_annex(num)
    if not ann:
        print(f"Annex {num} not found.")
        return
    _print_header(f"Annex {num} — {ann['title']}")
    print(ann["text"])
    _print_ref(f"Annex {num} of Regulation (EU) 2024/1689")


def _print_tier(tier: str) -> None:
    t = data.get_risk_tier(tier)
    if not t:
        print(f"Risk tier '{tier}' not found. Options: prohibited, high_risk, limited_risk, minimal_risk")
        return
    _print_header(f"RISK TIER: {t['label']}")
    print(f"\n{t['summary']}")
    _print_ref(t["legal_basis"])
    print(f"\n  Applies from: {t['applies_from']}")
    if t.get("penalty"):
        print(f"  Penalty: {t['penalty']}")
    if t["tier"] == "high_risk":
        print("\n  --- Annex III high-risk areas ---")
        for a in t["annex_iii_areas"]:
            print(f"  [{a['area']}] {a['name']} ({a['ref']})")
            print(f"      {a['description']}")
    if t.get("practices"):
        print("\n  --- Prohibited practices ---")
        for p in t["practices"]:
            print(f"  • {p['name']} ({p['ref']})")
            print(f"      {p['description']}")
            if p.get("exceptions"):
                print(f"      Exceptions: {p['exceptions']}")
    if t.get("obligations"):
        print("\n  --- Obligations ---")
        for o in t["obligations"]:
            print(f"  • {o['obligation']} ({o['ref']})")


def _print_actor(actor: str) -> None:
    a = data.get_actor(actor)
    if not a:
        print(f"Actor '{actor}' not found. Options: provider, deployer, importer, distributor, authorised_representative, operator")
        return
    _print_header(f"ACTOR: {a['actor'].replace('_', ' ').title()}")
    print(f"\n  Definition ({a['definition_ref']}): {a['definition']}")
    print("\n  --- Key obligations ---")
    for o in a["key_obligations"]:
        print(f"  • {o['obligation']} ({o['ref']})")


def _print_checklist(actor: str, tier: Optional[str]) -> None:
    items = compliance.checklist(actor, tier)
    if not items:
        print(f"No obligations found for actor '{actor}'" + (f" and tier '{tier}'" if tier else "") + ".")
        return
    label = actor.replace("_", " ").title()
    tier_label = f" ({tier.replace('_', ' ').title()})" if tier else ""
    _print_header(f"COMPLIANCE CHECKLIST — {label}{tier_label}")
    print(f"\n  {len(items)} obligations. Mark each as you complete it.")
    for i, item in enumerate(items, 1):
        print(f"\n  [{i:>2}] [ ] {item['title']}")
        print(f"       {item['description']}")
        print(f"       ACTION: {item['action']}")
        print(f"       {item['ref']}")


def _print_timeline() -> None:
    _print_header("APPLICATION TIMELINE")
    for ev in data.timeline():
        print(f"\n  {ev['date']}  {ev['event']}")
        print(f"       {ev['ref']}")


def _print_penalties() -> None:
    _print_header("PENALTIES")
    for p in data.penalties():
        print(f"\n  • {p['violation']}")
        if p.get("fine"):
            print(f"    Fine: {p['fine']}")
        if p.get("note"):
            print(f"    Note: {p['note']}")
        print(f"    {p['ref']}")


def _print_definitions() -> None:
    _print_header("KEY DEFINITIONS")
    for term, d in data.definitions().items():
        print(f"\n  {term.replace('_', ' ').title()} ({d['ref']})")
        print(f"    {d['definition']}")


def _print_governance() -> None:
    _print_header("GOVERNANCE BODIES")
    for g in data.governance_bodies():
        print(f"\n  • {g['body']} ({g['ref']})")
        print(f"    {g['role']}")


def _print_crossrefs() -> None:
    _print_header("CROSS-REFERENCES")
    for key, cr in data.cross_references().items():
        print(f"\n  {key.replace('_', ' ').title()} ({cr['ref']})")
        print(f"    {cr['summary']}")
        for a in cr["key_articles"]:
            print(f"    • {a['subject']} ({a['ref']})")


def _print_search(query: str, scope: str, whole_word: bool, limit: int) -> None:
    results = search.search(query, scope=scope, whole_word=whole_word, limit=limit)
    if not results:
        print(f"No results for '{query}'.")
        return
    _print_header(f"SEARCH: '{query}' ({len(results)} results)")
    for r in results:
        print(f"\n  {r['ref']} — {r['title']}")
        print(f"    {search.excerpt(r['text'], query)}")
        print(f"    ({r['count']} matches)")


def _print_classify(description: str) -> None:
    result = compliance.classify_high_risk(description)
    _print_header("HIGH-RISK CLASSIFICATION (heuristic)")
    verdict = "LIKELY HIGH-RISK" if result["likely_high_risk"] else "LIKELY NOT HIGH-RISK"
    print(f"\n  Verdict: {verdict}")
    if result["matched_annex_iii_areas"]:
        print("\n  Matched Annex III areas:")
        for a in result["matched_annex_iii_areas"]:
            print(f"    • [{a['area']}] {a['name']} ({a['ref']})")
    print(f"\n  {result['disclaimer']}")
    print(f"  {result['ref']}")


def _print_citation() -> None:
    print(data.citation())


def _print_json(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


# --- Argument parsing -----------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eu-ai-act",
        description="Navigate, understand and apply the EU AI Act (Regulation (EU) 2024/1689).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search", help="Full-text search the Act.")
    p_search.add_argument("query", help="Search terms.")
    p_search.add_argument("--scope", choices=["all", "articles", "recitals", "annexes"], default="all")
    p_search.add_argument("--whole-word", action="store_true", help="Match whole words only.")
    p_search.add_argument("--limit", type=int, default=20)
    p_search.add_argument("--json", action="store_true", help="Output as JSON.")

    p_art = sub.add_parser("article", help="Show a full article.")
    p_art.add_argument("number", help="Article number (e.g. 5, 6, 113).")
    p_art.add_argument("--json", action="store_true")

    p_rec = sub.add_parser("recital", help="Show a full recital.")
    p_rec.add_argument("number", type=int, help="Recital number (1-180).")
    p_rec.add_argument("--json", action="store_true")

    p_ann = sub.add_parser("annex", help="Show a full annex.")
    p_ann.add_argument("number", help="Annex roman numeral (e.g. I, III).")
    p_ann.add_argument("--json", action="store_true")

    p_tier = sub.add_parser("tier", help="Show a risk tier.")
    p_tier.add_argument("tier", choices=["prohibited", "high_risk", "limited_risk", "minimal_risk"])
    p_tier.add_argument("--json", action="store_true")

    p_actor = sub.add_parser("actor", help="Show an actor and its obligations.")
    p_actor.add_argument("actor", choices=["provider", "deployer", "importer", "distributor", "authorised_representative", "operator"])
    p_actor.add_argument("--json", action="store_true")

    p_check = sub.add_parser("checklist", help="Generate a compliance checklist.")
    p_check.add_argument("actor", choices=["provider", "deployer", "importer", "distributor", "authorised_representative", "operator", "all"])
    p_check.add_argument("--tier", choices=["prohibited", "high_risk", "limited_risk", "minimal_risk", "gpai", "gpai_systemic"])
    p_check.add_argument("--json", action="store_true")

    sub.add_parser("timeline", help="Show the application timeline.")
    sub.add_parser("penalties", help="Show the penalty schedule.")
    sub.add_parser("definitions", help="Show key definitions.")
    sub.add_parser("governance", help="Show governance bodies.")
    sub.add_parser("crossrefs", help="Show cross-references.")
    sub.add_parser("citation", help="Show the official citation.")

    p_class = sub.add_parser("classify", help="Heuristic high-risk classification.")
    p_class.add_argument("description", nargs="+", help="Describe the AI system (multiple words allowed).")
    p_class.add_argument("--json", action="store_true")

    # --- AI subcommands ---
    p_ai = sub.add_parser("ai", help="AI-powered interaction with the Act (requires local Ollama).")
    ai_sub = p_ai.add_subparsers(dest="ai_command", required=True)

    p_ai_ask = ai_sub.add_parser("ask", help="Ask a question grounded in the Act.")
    p_ai_ask.add_argument("question", nargs="+", help="Your question.")
    p_ai_ask.add_argument("--n", type=int, default=6, help="Number of context chunks to retrieve.")
    p_ai_ask.add_argument("--json", action="store_true")

    p_ai_sum = ai_sub.add_parser("summarize", help="Summarize a provision or topic.")
    p_ai_sum.add_argument("target", nargs="+", help="Provision (e.g. 'Article 5') or topic.")
    p_ai_sum.add_argument("--n", type=int, default=6)
    p_ai_sum.add_argument("--json", action="store_true")

    p_ai_list = ai_sub.add_parser("list", help="List obligations/practices on a topic.")
    p_ai_list.add_argument("topic", nargs="+", help="Topic to list items for.")
    p_ai_list.add_argument("--n", type=int, default=8)
    p_ai_list.add_argument("--json", action="store_true")

    p_ai_cmp = ai_sub.add_parser("compare", help="Compare two provisions or concepts.")
    p_ai_cmp.add_argument("a", help="First item.")
    p_ai_cmp.add_argument("b", help="Second item.")
    p_ai_cmp.add_argument("--n", type=int, default=8)
    p_ai_cmp.add_argument("--json", action="store_true")

    p_ai_obl = ai_sub.add_parser("obligations", help="List obligations for an actor or tier.")
    p_ai_obl.add_argument("--actor", choices=["provider", "deployer", "importer", "distributor", "authorised_representative", "operator"])
    p_ai_obl.add_argument("--tier", choices=["prohibited", "high_risk", "limited_risk", "minimal_risk", "gpai", "gpai_systemic"])
    p_ai_obl.add_argument("--json", action="store_true")

    p_ai_exp = ai_sub.add_parser("explain", help="Plain-language explanation of a provision.")
    p_ai_exp.add_argument("provision", nargs="+", help="e.g. 'Article 5'.")
    p_ai_exp.add_argument("--json", action="store_true")

    p_ai_embed = ai_sub.add_parser("embed", help="Build/rebuild the vector store.")
    p_ai_embed.add_argument("--force", action="store_true", help="Force rebuild even if up to date.")

    p_ai_status = ai_sub.add_parser("status", help="Show AI provider + vector store status.")

    p_ai_models = ai_sub.add_parser("models", help="List models available on the provider.")

    p_ai_config = ai_sub.add_parser("config", help="Show or set the AI provider config.")
    p_ai_config.add_argument("--base-url", help="Set the provider base URL.")
    p_ai_config.add_argument("--chat-model", help="Set the default chat model.")
    p_ai_config.add_argument("--embed-model", help="Set the embedding model.")
    p_ai_config.add_argument("--api-key", help="Set the API key (for cloud providers).")

    return parser


def _print_ai_result(result: Dict[str, Any], json_out: bool = False) -> None:
    """Print an AI result (answer + sources)."""
    if json_out:
        _print_json(result)
        return
    print(f"\n{result.get('answer', '')}")
    sources = result.get("sources", [])
    if sources:
        print(f"\n  Sources: {', '.join(sources)}")


def _dispatch_ai(args: argparse.Namespace) -> None:
    """Dispatch the `ai` subcommands."""
    cmd = args.ai_command

    if cmd == "embed":
        result = vector_store.build(force=args.force)
        print(f"\nVector store: {result['status']}")
        print(f"  Documents: {result.get('document_count', 0)}")
        print(f"  Embed model: {result.get('embed_model', '')}")
        print(f"  Path: {result.get('path', '')}")
        return

    if cmd == "status":
        provider = ai_provider.AIProvider()
        try:
            available = provider.is_available()
            print(f"\nAI Provider: {provider.config.base_url}")
            print(f"  Available: {'yes' if available else 'no'}")
            print(f"  Chat model: {provider.config.chat_model}")
            print(f"  Embed model: {provider.config.embed_model}")
            vs = vector_store.status()
            print(f"\nVector store: {vs['status']}")
            if vs.get("document_count"):
                print(f"  Documents: {vs['document_count']}")
                print(f"  Embed model: {vs.get('embed_model', '')}")
            print(f"  Path: {vs.get('path', '')}")
        finally:
            provider.close()
        return

    if cmd == "models":
        provider = ai_provider.AIProvider()
        try:
            if not provider.is_available():
                print("Provider not available. Is Ollama running?")
                return
            models = provider.list_models()
            print(f"\nModels on {provider.config.base_url}:")
            for m in models:
                print(f"  - {m.get('id', m.get('name', '?'))}")
        finally:
            provider.close()
        return

    if cmd == "config":
        cfg = ai_provider.ProviderConfig.load()
        changed = False
        if args.base_url:
            cfg.base_url = args.base_url
            changed = True
        if args.chat_model:
            cfg.chat_model = args.chat_model
            changed = True
        if args.embed_model:
            cfg.embed_model = args.embed_model
            changed = True
        if args.api_key is not None:
            cfg.api_key = args.api_key
            changed = True
        if changed:
            path = cfg.save()
            print(f"\nConfig saved to {path}")
        print(f"\nAI Provider config:")
        print(f"  base_url:   {cfg.base_url}")
        print(f"  chat_model: {cfg.chat_model}")
        print(f"  embed_model:{cfg.embed_model}")
        print(f"  api_key:    {'***' if cfg.api_key else '(none)'}")
        return

    # RAG-based commands
    if cmd == "ask":
        q = " ".join(args.question)
        result = ai_rag.ask(q, n=args.n)
        _print_ai_result(result, args.json)
    elif cmd == "summarize":
        target = " ".join(args.target)
        result = ai_rag.summarize(target, n=args.n)
        _print_ai_result(result, args.json)
    elif cmd == "list":
        topic = " ".join(args.topic)
        result = ai_rag.list_items(topic, n=args.n)
        _print_ai_result(result, args.json)
    elif cmd == "compare":
        result = ai_rag.compare(args.a, args.b, n=args.n)
        _print_ai_result(result, args.json)
    elif cmd == "obligations":
        result = ai_rag.obligations(actor=args.actor, tier=args.tier)
        _print_ai_result(result, args.json)
    elif cmd == "explain":
        provision = " ".join(args.provision)
        result = ai_rag.explain(provision)
        _print_ai_result(result, args.json)


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "search":
            if args.json:
                _print_json(search.search(args.query, scope=args.scope, whole_word=args.whole_word, limit=args.limit))
            else:
                _print_search(args.query, args.scope, args.whole_word, args.limit)
        elif args.command == "article":
            if args.json:
                _print_json(data.get_article(args.number))
            else:
                _print_article(args.number)
        elif args.command == "recital":
            if args.json:
                _print_json(data.get_recital(args.number))
            else:
                _print_recital(args.number)
        elif args.command == "annex":
            if args.json:
                _print_json(data.get_annex(args.number))
            else:
                _print_annex(args.number)
        elif args.command == "tier":
            if args.json:
                _print_json(data.get_risk_tier(args.tier))
            else:
                _print_tier(args.tier)
        elif args.command == "actor":
            if args.json:
                _print_json(data.get_actor(args.actor))
            else:
                _print_actor(args.actor)
        elif args.command == "checklist":
            if args.json:
                _print_json(compliance.checklist(args.actor, args.tier))
            else:
                _print_checklist(args.actor, args.tier)
        elif args.command == "timeline":
            _print_timeline()
        elif args.command == "penalties":
            _print_penalties()
        elif args.command == "definitions":
            _print_definitions()
        elif args.command == "governance":
            _print_governance()
        elif args.command == "crossrefs":
            _print_crossrefs()
        elif args.command == "citation":
            _print_citation()
        elif args.command == "classify":
            desc = " ".join(args.description)
            if args.json:
                _print_json(compliance.classify_high_risk(desc))
            else:
                _print_classify(desc)
        elif args.command == "ai":
            _dispatch_ai(args)
        else:
            parser.print_help()
            return 1
    except data.DataError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except (ai_provider.ProviderError, ai_rag.ProviderError) as e:
        print(f"AI Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
