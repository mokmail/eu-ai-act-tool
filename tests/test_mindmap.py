"""Tests for the mindmap builder."""
from eu_ai_act import mindmap


def test_topics_are_listed_with_summaries():
    topics = mindmap.topics()
    ids = {t["id"] for t in topics}
    assert {"contents", "prohibited", "high-risk", "transparency", "gpai",
            "governance", "timeline", "penalties"} <= ids
    assert all(t["title"] for t in topics)


def test_every_topic_builds_a_tree_with_leaves():
    for topic in mindmap.topics():
        node = mindmap.build(topic["id"])
        assert node is not None
        assert node["children"], topic["id"]


def test_unknown_topic_is_none():
    assert mindmap.build("nope") is None


def test_leaves_cite_a_provision():
    node = mindmap.build("high-risk")
    assert node is not None
    leaves = [leaf for branch in node["children"] for leaf in branch.get("children", [])]
    assert leaves
    assert all(leaf["ref"].startswith(("Article", "Annex")) for leaf in leaves)


def test_high_risk_map_excludes_transparency_and_gpai_duties():
    node = mindmap.build("high-risk")
    assert node is not None
    refs = {leaf["ref"] for branch in node["children"] for leaf in branch.get("children", [])}
    assert "Article 50(1)" not in refs
    assert "Article 55" not in refs
    assert "Article 9" in refs


def test_contents_map_covers_every_article():
    node = mindmap.build("contents")
    assert node is not None
    assert len(node["children"]) == 13

    def count_leaves(n):
        kids = n.get("children")
        return sum(count_leaves(k) for k in kids) if kids else 1

    assert count_leaves(node) == 113


def test_governance_map_is_nested():
    node = mindmap.build("governance")
    assert node is not None
    names = [c["label"] for c in node["children"]]
    assert "European Commission" in names
    commission = next(c for c in node["children"] if c["label"] == "European Commission")
    assert any(k["label"] == "AI Office" for k in commission["children"])


def test_prohibited_map_lists_all_eight_practices():
    node = mindmap.build("prohibited")
    assert node is not None
    assert len(node["children"]) == 8


def test_chapter_map_for_a_real_and_a_fake_chapter():
    node = mindmap.chapter_map("III")
    assert node is not None
    assert node["ref"] == "Chapter III"
    assert node["children"]
    assert mindmap.chapter_map("XCIX") is None
