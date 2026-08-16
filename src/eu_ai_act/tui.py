"""
Interactive TUI for the EU AI Act tool.

A menu-driven browser built on Textual. Navigate risk tiers, articles,
recitals, annexes, compliance checklists, search, timeline, penalties,
definitions, and governance bodies with arrow keys.

Run with:
    eu-ai-act-tui
or:
    uv run eu-ai-act-tui
"""
from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Markdown,
    Static,
)

from . import compliance, data, search


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def _article_md(num: str) -> str:
    art = data.get_article(num)
    if not art:
        return f"# Article {num}\n\n*Not found.*"
    return f"# Article {num} — {art['title']}\n\n{art['text']}\n\n---\n*Legal basis: Article {num} of Regulation (EU) 2024/1689*"


def _recital_md(num: int) -> str:
    rec = data.get_recital(num)
    if not rec:
        return f"# Recital {num}\n\n*Not found.*"
    return f"# Recital {num}\n\n{rec['text']}\n\n---\n*Legal basis: Recital {num} of Regulation (EU) 2024/1689*"


def _annex_md(num: str) -> str:
    ann = data.get_annex(num)
    if not ann:
        return f"# Annex {num}\n\n*Not found.*"
    return f"# Annex {num} — {ann['title']}\n\n{ann['text']}\n\n---\n*Legal basis: Annex {num} of Regulation (EU) 2024/1689*"


# ---------------------------------------------------------------------------
# Screens
# ---------------------------------------------------------------------------
class HomeScreen(Screen):
    """Main menu."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("enter", "select", "Select"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            Static("EU AI Act Tool", classes="title"),
            Static("Regulation (EU) 2024/1689 — navigate, understand, apply", classes="subtitle"),
            ListView(
                ListItem(Label("🔍  Search the Act")),
                ListItem(Label("📄  Articles")),
                ListItem(Label("📜  Recitals")),
                ListItem(Label("📎  Annexes")),
                ListItem(Label("⚠️  Risk Tiers")),
                ListItem(Label("👤  Actors & Obligations")),
                ListItem(Label("✅  Compliance Checklists")),
                ListItem(Label("🗓️  Timeline")),
                ListItem(Label("💰  Penalties")),
                ListItem(Label("📖  Definitions")),
                ListItem(Label("🏛️  Governance Bodies")),
                ListItem(Label("🔗  Cross-References")),
                ListItem(Label("📌  Citation")),
                ListItem(Label("🤖  AI Assistant (Ollama)")),
                id="menu",
            ),
            id="home",
        )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        index = event.list_view.index
        if index == 0:
            self.app.push_screen(SearchScreen())
        elif index == 1:
            self.app.push_screen(ArticleListScreen())
        elif index == 2:
            self.app.push_screen(RecitalListScreen())
        elif index == 3:
            self.app.push_screen(AnnexListScreen())
        elif index == 4:
            self.app.push_screen(TierListScreen())
        elif index == 5:
            self.app.push_screen(ActorListScreen())
        elif index == 6:
            self.app.push_screen(ChecklistScreen())
        elif index == 7:
            self.app.push_screen(TimelineScreen())
        elif index == 8:
            self.app.push_screen(PenaltiesScreen())
        elif index == 9:
            self.app.push_screen(DefinitionsScreen())
        elif index == 10:
            self.app.push_screen(GovernanceScreen())
        elif index == 11:
            self.app.push_screen(CrossrefsScreen())
        elif index == 12:
            self.app.push_screen(CitationScreen())
        elif index == 13:
            self.app.push_screen(AIChatScreen())


class ArticleListScreen(Screen):
    """List of all 113 articles."""

    BINDINGS = [Binding("escape", "pop", "Back"), Binding("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            Static("Articles", classes="title"),
            ListView(id="articles"),
            id="content",
        )
        yield Footer()

    def on_mount(self) -> None:
        lv = self.query_one("#articles", ListView)
        for num, art in data.articles().items():
            lv.append(ListItem(Label(f"Article {num} — {art['title']}")))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        num = event.list_view.index + 1
        self.app.push_screen(ArticleDetailScreen(str(num)))


class ArticleDetailScreen(Screen):
    """Full text of a single article."""

    BINDINGS = [Binding("escape", "pop", "Back"), Binding("q", "quit", "Quit")]

    def __init__(self, number: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.number = number

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Markdown(_article_md(self.number), id="body")
        yield Footer()


class RecitalListScreen(Screen):
    """List of all 180 recitals."""

    BINDINGS = [Binding("escape", "pop", "Back"), Binding("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            Static("Recitals", classes="title"),
            ListView(id="recitals"),
            id="content",
        )
        yield Footer()

    def on_mount(self) -> None:
        lv = self.query_one("#recitals", ListView)
        for num in sorted(data.recitals().keys()):
            lv.append(ListItem(Label(f"Recital {num}")))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        num = event.list_view.index + 1
        self.app.push_screen(RecitalDetailScreen(num))


class RecitalDetailScreen(Screen):
    """Full text of a single recital."""

    BINDINGS = [Binding("escape", "pop", "Back"), Binding("q", "quit", "Quit")]

    def __init__(self, number: int, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.number = number

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Markdown(_recital_md(self.number), id="body")
        yield Footer()


class AnnexListScreen(Screen):
    """List of all 13 annexes."""

    BINDINGS = [Binding("escape", "pop", "Back"), Binding("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            Static("Annexes", classes="title"),
            ListView(id="annexes"),
            id="content",
        )
        yield Footer()

    def on_mount(self) -> None:
        lv = self.query_one("#annexes", ListView)
        for num, ann in data.annexes().items():
            lv.append(ListItem(Label(f"Annex {num} — {ann['title']}")))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        nums = list(data.annexes().keys())
        num = nums[event.list_view.index]
        self.app.push_screen(AnnexDetailScreen(num))


class AnnexDetailScreen(Screen):
    """Full text of a single annex."""

    BINDINGS = [Binding("escape", "pop", "Back"), Binding("q", "quit", "Quit")]

    def __init__(self, number: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.number = number

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Markdown(_annex_md(self.number), id="body")
        yield Footer()


class TierListScreen(Screen):
    """List of the four risk tiers."""

    BINDINGS = [Binding("escape", "pop", "Back"), Binding("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            Static("Risk Tiers", classes="title"),
            ListView(
                ListItem(Label("🚫  Prohibited AI practices")),
                ListItem(Label("⚠️  High-risk AI systems")),
                ListItem(Label("ℹ️  Limited-risk / transparency")),
                ListItem(Label("✅  Minimal-risk")),
                id="tiers",
            ),
            id="content",
        )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        tiers = ["prohibited", "high_risk", "limited_risk", "minimal_risk"]
        self.app.push_screen(TierDetailScreen(tiers[event.list_view.index]))


class TierDetailScreen(Screen):
    """Detail view of a single risk tier."""

    BINDINGS = [Binding("escape", "pop", "Back"), Binding("q", "quit", "Quit")]

    def __init__(self, tier: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.tier = tier

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Markdown(self._build_markdown(), id="body")
        yield Footer()

    def _build_markdown(self) -> str:
        t = data.get_risk_tier(self.tier)
        if not t:
            return f"# Risk tier '{self.tier}' not found."
        lines = [f"# {t['label']}", "", t["summary"], "", f"**Legal basis:** {t['legal_basis']}", f"**Applies from:** {t['applies_from']}"]
        if t.get("penalty"):
            lines.append(f"**Penalty:** {t['penalty']}")
        if t.get("practices"):
            lines.append("")
            lines.append("## Prohibited practices")
            for p in t["practices"]:
                lines.append(f"- **{p['name']}** ({p['ref']}) — {p['description']}")
                if p.get("exceptions"):
                    lines.append(f"  - *Exceptions:* {p['exceptions']}")
        if t.get("annex_iii_areas"):
            lines.append("")
            lines.append("## Annex III high-risk areas")
            for a in t["annex_iii_areas"]:
                lines.append(f"- **[{a['area']}] {a['name']}** ({a['ref']}) — {a['description']}")
        if t.get("obligations"):
            lines.append("")
            lines.append("## Obligations")
            for o in t["obligations"]:
                lines.append(f"- {o['obligation']} ({o['ref']})")
        return "\n".join(lines)


class ActorListScreen(Screen):
    """List of actors."""

    BINDINGS = [Binding("escape", "pop", "Back"), Binding("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            Static("Actors & Obligations", classes="title"),
            ListView(id="actors"),
            id="content",
        )
        yield Footer()

    def on_mount(self) -> None:
        lv = self.query_one("#actors", ListView)
        for a in data.actors():
            lv.append(ListItem(Label(a["actor"].replace("_", " ").title())))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        actors = [a["actor"] for a in data.actors()]
        self.app.push_screen(ActorDetailScreen(actors[event.list_view.index]))


class ActorDetailScreen(Screen):
    """Detail view of a single actor."""

    BINDINGS = [Binding("escape", "pop", "Back"), Binding("q", "quit", "Quit")]

    def __init__(self, actor: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.actor = actor

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Markdown(self._build_markdown(), id="body")
        yield Footer()

    def _build_markdown(self) -> str:
        a = data.get_actor(self.actor)
        if not a:
            return f"# Actor '{self.actor}' not found."
        lines = [f"# {a['actor'].replace('_', ' ').title()}", "", f"**Definition ({a['definition_ref']}):** {a['definition']}", "", "## Key obligations"]
        for o in a["key_obligations"]:
            lines.append(f"- {o['obligation']} ({o['ref']})")
        return "\n".join(lines)


class ChecklistScreen(Screen):
    """Compliance checklist generator."""

    BINDINGS = [Binding("escape", "pop", "Back"), Binding("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            Static("Compliance Checklists", classes="title"),
            Static("Select an actor to generate its checklist:", classes="hint"),
            ListView(
                ListItem(Label("Provider")),
                ListItem(Label("Deployer")),
                ListItem(Label("Importer")),
                ListItem(Label("Distributor")),
                ListItem(Label("Authorised Representative")),
                ListItem(Label("Operator")),
                id="actors",
            ),
            id="content",
        )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        actors = ["provider", "deployer", "importer", "distributor", "authorised_representative", "operator"]
        self.app.push_screen(ChecklistDetailScreen(actors[event.list_view.index]))


class ChecklistDetailScreen(Screen):
    """Checklist for a single actor."""

    BINDINGS = [Binding("escape", "pop", "Back"), Binding("q", "quit", "Quit")]

    def __init__(self, actor: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.actor = actor

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Markdown(self._build_markdown(), id="body")
        yield Footer()

    def _build_markdown(self) -> str:
        items = compliance.checklist(self.actor)
        lines = [f"# Compliance Checklist — {self.actor.replace('_', ' ').title()}", "", f"**{len(items)} obligations.**", ""]
        for i, item in enumerate(items, 1):
            lines.append(f"### {i}. {item['title']}")
            lines.append(f"*{item['description']}*")
            lines.append(f"**Action:** {item['action']}")
            lines.append(f"**Legal basis:** {item['ref']}")
            lines.append("")
        return "\n".join(lines)


class SearchScreen(Screen):
    """Full-text search."""

    BINDINGS = [Binding("escape", "pop", "Back"), Binding("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            Static("Search the Act", classes="title"),
            Input(placeholder="Enter search terms (e.g. 'human oversight')", id="query"),
            ListView(id="results"),
            id="content",
        )
        yield Footer()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if not query:
            return
        lv = self.query_one("#results", ListView)
        lv.clear()
        results = search.search(query, limit=30)
        if not results:
            lv.append(ListItem(Label(f"No results for '{query}'")))
            return
        for r in results:
            lv.append(ListItem(Label(f"{r['ref']} — {r['title']}")))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        lv = self.query_one("#results", ListView)
        item = lv.children[event.list_view.index]
        label = str(item.children[0].renderable)
        if label.startswith("No results"):
            return
        ref = label.split(" — ")[0]
        if ref.startswith("Article"):
            self.app.push_screen(ArticleDetailScreen(ref.split()[1]))
        elif ref.startswith("Recital"):
            self.app.push_screen(RecitalDetailScreen(int(ref.split()[1])))
        elif ref.startswith("Annex"):
            self.app.push_screen(AnnexDetailScreen(ref.split()[1]))


class TimelineScreen(Screen):
    """Application timeline."""

    BINDINGS = [Binding("escape", "pop", "Back"), Binding("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Markdown(self._build_markdown(), id="body")
        yield Footer()

    def _build_markdown(self) -> str:
        lines = ["# Application Timeline", ""]
        for ev in data.timeline():
            lines.append(f"## {ev['date']}")
            lines.append(ev["event"])
            lines.append(f"*{ev['ref']}*")
            lines.append("")
        return "\n".join(lines)


class PenaltiesScreen(Screen):
    """Penalty schedule."""

    BINDINGS = [Binding("escape", "pop", "Back"), Binding("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Markdown(self._build_markdown(), id="body")
        yield Footer()

    def _build_markdown(self) -> str:
        lines = ["# Penalties", ""]
        for p in data.penalties():
            lines.append(f"## {p['ref']}")
            lines.append(p["violation"])
            if p.get("fine"):
                lines.append(f"**Fine:** {p['fine']}")
            if p.get("note"):
                lines.append(f"*{p['note']}*")
            lines.append("")
        return "\n".join(lines)


class DefinitionsScreen(Screen):
    """Key definitions."""

    BINDINGS = [Binding("escape", "pop", "Back"), Binding("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Markdown(self._build_markdown(), id="body")
        yield Footer()

    def _build_markdown(self) -> str:
        lines = ["# Key Definitions", ""]
        for term, d in data.definitions().items():
            lines.append(f"## {term.replace('_', ' ').title()} ({d['ref']})")
            lines.append(d["definition"])
            lines.append("")
        return "\n".join(lines)


class GovernanceScreen(Screen):
    """Governance bodies."""

    BINDINGS = [Binding("escape", "pop", "Back"), Binding("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Markdown(self._build_markdown(), id="body")
        yield Footer()

    def _build_markdown(self) -> str:
        lines = ["# Governance Bodies", ""]
        for g in data.governance_bodies():
            lines.append(f"## {g['body']} ({g['ref']})")
            lines.append(g["role"])
            lines.append("")
        return "\n".join(lines)


class CrossrefsScreen(Screen):
    """Cross-references."""

    BINDINGS = [Binding("escape", "pop", "Back"), Binding("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Markdown(self._build_markdown(), id="body")
        yield Footer()

    def _build_markdown(self) -> str:
        lines = ["# Cross-References", ""]
        for key, cr in data.cross_references().items():
            lines.append(f"## {key.replace('_', ' ').title()} ({cr['ref']})")
            lines.append(cr["summary"])
            for a in cr["key_articles"]:
                lines.append(f"- {a['subject']} ({a['ref']})")
            lines.append("")
        return "\n".join(lines)


class CitationScreen(Screen):
    """Official citation."""

    BINDINGS = [Binding("escape", "pop", "Back"), Binding("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Markdown(f"# Official Citation\n\n{data.citation()}", id="body")
        yield Footer()


class AIChatScreen(Screen):
    """AI chat assistant (RAG over the Act via local Ollama)."""

    BINDINGS = [Binding("escape", "pop", "Back"), Binding("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            Static("AI Assistant — ask anything about the EU AI Act", classes="title"),
            Static("Type a question and press Enter. Answers are grounded in the Act.", classes="hint"),
            Input(placeholder="e.g. What are the prohibited AI practices?", id="ai_query"),
            Markdown("", id="ai_output"),
            id="content",
        )
        yield Footer()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if not query:
            return
        out = self.query_one("#ai_output", Markdown)
        out.update(f"*Asking: {query}...*")
        # Run the RAG ask in a thread to avoid blocking the UI
        from textual import work

        @work(thread=True)
        def do_ask() -> None:
            try:
                from . import ai_rag

                result = ai_rag.ask(query)
                answer = result.get("answer", "")
                sources = result.get("sources", [])
                src = f"\n\n---\n*Sources: {', '.join(sources)}*" if sources else ""
                self.call_from_thread(out.update, f"{answer}{src}")
            except Exception as e:
                self.call_from_thread(out.update, f"*Error: {e}*")

        do_ask()
        self.query_one("#ai_query", Input).value = ""


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
class EUAIActApp(App):
    """EU AI Act TUI application."""

    TITLE = "EU AI Act Tool"
    SUB_TITLE = "Regulation (EU) 2024/1689"
    CSS = """
    Screen {
        background: #1a1b26;
    }
    #home {
        align: center middle;
        width: 100%;
        height: 100%;
    }
    .title {
        text-style: bold;
        color: #7aa2f7;
        text-align: center;
        width: 100%;
        content-align: center middle;
        height: 3;
    }
    .subtitle {
        color: #a9b1d6;
        text-align: center;
        width: 100%;
        height: 1;
        margin-bottom: 1;
    }
    .hint {
        color: #a9b1d6;
        margin-bottom: 1;
    }
    #menu {
        width: 60;
        height: auto;
        border: round #7aa2f7;
        padding: 1;
    }
    #content {
        padding: 1 2;
        height: 100%;
    }
    #body {
        padding: 1 2;
        height: 100%;
    }
    ListView {
        background: #24283b;
        border: round #565f89;
    }
    ListItem {
        padding: 0 1;
    }
    ListItem:hover {
        background: #3b4261;
    }
    Input {
        margin-bottom: 1;
    }
    """

    def on_mount(self) -> None:
        self.push_screen(HomeScreen())


def main(argv: Optional[List[str]] = None) -> int:
    app = EUAIActApp()
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
