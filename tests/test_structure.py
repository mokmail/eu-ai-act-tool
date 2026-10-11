"""Tests for the structure, citation-graph and statistics layer."""
from eu_ai_act import structure


# -- the Act's skeleton -----------------------------------------------------
def test_thirteen_chapters_parsed_from_the_official_text():
    chapters = structure.chapters()
    assert len(chapters) == 13
    assert chapters[0]["number"] == "I"
    assert "GENERAL PROVISIONS" in chapters[0]["title"].upper()


def test_every_article_is_mapped_to_a_chapter():
    index = structure.article_index()
    assert len(index) == 113
    assert all(v["chapter"] for v in index.values())


def test_known_locations_are_correct():
    art5 = structure.location("5")
    art6 = structure.location("6")
    art53 = structure.location("53")
    art99 = structure.location("99")
    assert art5 and art6 and art53 and art99
    assert art5["chapter"] == "II"
    assert art6["chapter"] == "III"
    assert art6["section"] == 1
    assert art53["chapter"] == "V"
    assert art99["chapter"] == "XII"


def test_sections_are_nested_under_their_chapter():
    chapter_iii = structure.chapter("III")
    assert chapter_iii is not None
    assert len(chapter_iii["sections"]) == 5
    assert chapter_iii["sections"][0]["title"] == "Classification of AI systems as high-risk"


def test_chapter_article_counts_sum_to_the_corpus():
    total = sum(len(c["articles"]) for c in structure.chapters())
    assert total == 113


def test_annex_index_is_complete():
    annexes = structure.annexes()
    assert len(annexes) == 13
    titles = {a["number"]: a["title"] for a in annexes}
    assert "High-risk AI systems referred to in Article 6(2)" == titles["III"]


def test_table_of_contents_resolves_article_titles():
    toc = structure.table_of_contents()
    assert len(toc) == 13
    chapter_ii = next(c for c in toc if c["number"] == "II")
    assert chapter_ii["articles"] == [{"number": "5", "title": "Prohibited AI practices"}]


def test_breadcrumb_includes_section_only_when_there_is_one():
    assert structure.breadcrumb("5") == ["Chapter II"]
    assert structure.breadcrumb("53") == ["Chapter V", "Section 2"]
    assert structure.breadcrumb("999") == []


# -- citation graph ---------------------------------------------------------
def test_citation_graph_has_edges_and_nodes():
    graph = structure.citation_graph()
    assert graph["edge_count"] > 100
    assert "Article 6" in graph["nodes"]
    assert "Annex III" in graph["nodes"]


def test_citation_graph_never_self_references():
    graph = structure.citation_graph()
    for source, targets in graph["edges"].items():
        assert source not in targets


def test_annex_iii_is_the_most_cited_provision():
    top = structure.citation_graph()["most_cited"][0]
    assert top["ref"] == "Annex III"
    assert top["citations"] > 20


def test_references_of_and_cited_by_are_reciprocal():
    refs = {r["ref"] for r in structure.references_of("5")}
    assert refs, "Article 5 cites something"
    for ref in refs:
        if ref.startswith("Article "):
            back = {c["ref"] for c in structure.cited_by(ref.split(" ", 1)[1])}
            assert "Article 5" in back


def test_node_sort_key_orders_numerically_then_annexes():
    graph = structure.citation_graph()
    articles = [n for n in graph["nodes"] if n.startswith("Article ")]
    assert articles.index("Article 6") < articles.index("Article 10")
    assert graph["nodes"][-1].startswith("Annex ")


# -- statistics -------------------------------------------------------------
def test_corpus_statistics_match_the_dataset():
    corpus = structure.stats()["corpus"]
    assert corpus["articles"] == 113
    assert corpus["recitals"] == 180
    assert corpus["annexes"] == 13
    assert corpus["chapters"] == 13
    assert corpus["sections"] == 16
    assert corpus["words"] > 40_000


def test_chapter_statistics_are_complete():
    chapters = structure.stats()["chapters"]
    assert len(chapters) == 13
    biggest = max(chapters, key=lambda c: c["articles"])
    assert biggest["number"] == "III"
    assert all(c["words"] > 0 for c in chapters)


def test_article_113_no_longer_swallows_the_annexes():
    """Regression: the last article's body must stop at the first annex."""
    from eu_ai_act import data

    text = data.get_article("113")["text"]
    assert len(text) < 20_000
    assert "ANNEX I" not in text
    assert "2 August 2026" in text


def test_obligation_statistics():
    from eu_ai_act import compliance

    obligations = structure.stats()["obligations"]
    assert obligations["total"] == len(compliance.OBLIGATIONS)
    assert obligations["by_actor"]["provider"] > 0
    assert obligations["by_tier"]["high_risk"] > 0
