"""Tests for the curated guide layer: classification path, procedures, scenarios."""
from eu_ai_act import data, guides


def test_guide_layer_loads_with_its_four_parts():
    assert guides.meta()["title"]
    assert guides.risk_path()["questions"]
    assert guides.procedures()
    assert guides.scenarios()
    assert guides.governance_structure()["root"]


# -- the shipped case corpus ------------------------------------------------
def test_the_shipped_case_corpus_is_sound():
    """Schema, ids, tiers and every citation, via the library's own validator."""
    errors = guides.validation_errors()
    assert not errors, "\n".join(errors)
    assert len(guides.scenarios()) >= 40, "the corpus is meant to be broad, not a handful"


def test_the_corpus_validator_actually_bites():
    """
    `validation_errors()` returning [] proves nothing if it always returns [].
    Feed it a case citing a provision that does not exist.
    """
    good = dict(guides.scenarios()[0])
    doctored = {**good, "id": "invented-case", "refs": ["Article 114", "Annex XIV"]}
    problems = guides.validation_errors([doctored])

    assert any("Article 114" in p for p in problems), problems
    assert any("Annex XIV" in p for p in problems), problems

    # and it must not cry wolf over the real corpus
    assert not guides.validation_errors([good])


def test_the_article_50_transparency_duties_are_numbered_correctly():
    """
    Article 50 was off by one across the whole corpus: 50(2) was labelled emotion
    recognition and 50(3) deepfakes, so every citation above 50(1) pointed a
    paragraph too early — and 50(2), the machine-readable marking duty, was absent
    altogether. It also put all four duties on the provider, when (3) and (4) bind
    deployers.
    """
    from eu_ai_act import compliance

    duties: dict[str, list[dict]] = {}
    for obligation in compliance.OBLIGATIONS:
        if obligation["ref"].startswith("Article 50"):
            duties.setdefault(obligation["ref"], []).append(obligation)

    assert set(duties) == {
        "Article 50(1)", "Article 50(2)", "Article 50(3)", "Article 50(4)"
    }, "the machine-readable marking duty (50(2)) must not go missing again"

    # 50(4) carries two duties — deepfakes and public-interest text
    assert len(duties["Article 50(4)"]) == 2

    titles = {ref: " ".join(item["title"] for item in items).lower() for ref, items in duties.items()}
    assert "interact" in titles["Article 50(1)"]
    assert "machine-readable" in titles["Article 50(2)"]
    assert "emotion" in titles["Article 50(3)"]
    assert "deepfake" in titles["Article 50(4)"]
    assert "public-interest" in titles["Article 50(4)"]

    # (1) and (2) are provider duties; (3) and (4) fall on deployers
    for ref in ("Article 50(1)", "Article 50(2)"):
        assert all(item["actor"] == "provider" for item in duties[ref]), ref
    for ref in ("Article 50(3)", "Article 50(4)"):
        assert all(item["actor"] == "deployer" for item in duties[ref]), ref


def test_the_tier_obligation_lists_agree_with_the_obligation_table():
    """The curated tier record and the obligation table are two views of one fact."""
    from eu_ai_act import compliance

    tier = data.get_risk_tier("limited_risk")
    assert tier, "the limited-risk tier must exist"
    listed = {o["ref"] for o in tier["obligations"]}
    table = {o["ref"] for o in compliance.OBLIGATIONS if o["tier"] == "limited_risk"}
    assert listed == table, f"tier says {sorted(listed)}, table says {sorted(table)}"



# -- classification path ----------------------------------------------------
def test_risk_path_questions_all_have_both_branches():
    for q in guides.risk_path()["questions"]:
        assert q["yes"] and q["no"]
        assert q["question"] and q["ref"]


def test_every_branch_targets_a_question_or_an_outcome():
    path = guides.risk_path()
    ids = {q["id"] for q in path["questions"]}
    outcomes = set(path["outcomes"])
    for q in path["questions"]:
        for branch in (q["yes"], q["no"]):
            assert branch in ids or branch in outcomes


def test_classification_walks_to_each_outcome():
    cases = {
        "prohibited": {"q_prohibited": True},
        "high_risk": {"q_prohibited": False, "q_annex1": True},
        "gpai_systemic": {"q_prohibited": False, "q_annex1": False, "q_annex3": False,
                          "q_gpai": True, "q_systemic": True},
        "gpai": {"q_prohibited": False, "q_annex1": False, "q_annex3": False,
                 "q_gpai": True, "q_systemic": False},
        "limited_risk": {"q_prohibited": False, "q_annex1": False, "q_annex3": False,
                         "q_gpai": False, "q_transparency": True},
        "minimal_risk": {"q_prohibited": False, "q_annex1": False, "q_annex3": False,
                         "q_gpai": False, "q_transparency": False},
    }
    for expected, answers in cases.items():
        result = guides.classify_path(answers)
        assert result["complete"] is True
        assert result["outcome"] == expected, f"{expected}: got {result}"


def test_annex_iii_profiling_route_returns_high_risk():
    """The Article 6(3) filter is unavailable where the system profiles."""
    result = guides.classify_path({
        "q_prohibited": False, "q_annex1": False, "q_annex3": True, "q_filter": False,
    })
    assert result["outcome"] == "high_risk"


def test_classification_stops_and_asks_when_an_answer_is_missing():
    result = guides.classify_path({"q_prohibited": False})
    assert result["complete"] is False
    assert result["question"]["id"] == "q_annex1"


def test_every_outcome_cites_its_legal_basis():
    for key, outcome in guides.risk_path()["outcomes"].items():
        assert outcome["ref"], key
        assert outcome["summary"], key
        assert outcome["actions"], key


# -- procedures -------------------------------------------------------------
def test_every_procedure_step_cites_an_article():
    for procedure in guides.procedures():
        assert procedure["steps"], procedure["id"]
        for step in procedure["steps"]:
            assert step["ref"], f"{procedure['id']} step {step['n']}"
            assert step["title"] and step["detail"]


def test_procedure_steps_are_numbered_consecutively():
    for procedure in guides.procedures():
        numbers = [s["n"] for s in procedure["steps"]]
        assert numbers == list(range(1, len(numbers) + 1)), procedure["id"]


def test_get_and_filter_procedures():
    fria = guides.get_procedure("fria")
    assert fria is not None and fria["actor"] == "deployer"
    assert guides.get_procedure("nope") is None
    providers = guides.procedures_for(actor="provider")
    assert providers and all(p["actor"] == "provider" for p in providers)


# -- scenarios --------------------------------------------------------------
def test_scenarios_carry_a_tier_and_citations():
    for scenario in guides.scenarios():
        assert scenario["tier"] in guides.risk_path()["outcomes"], scenario["id"]
        assert scenario["refs"], scenario["id"]
        assert scenario["analysis"], scenario["id"]
        for item in scenario["analysis"]:
            assert item["title"] and item["detail"] and item["ref"]


def test_scenario_filtering():
    prohibited = guides.scenarios_for(tier="prohibited")
    assert prohibited and all(s["tier"] == "prohibited" for s in prohibited)
    cv = guides.get_scenario("cv-screening")
    assert cv is not None and cv["sector"] == "Employment"


# -- governance -------------------------------------------------------------
def test_governance_tree_is_nested_and_cited():
    root = guides.governance_structure()["root"]
    assert root["children"]
    names = [c["name"] for c in root["children"]]
    assert "European Commission" in names
    assert "National competent authorities" in names
    for child in root["children"]:
        assert child["ref"]
        for grandchild in child.get("children", []):
            assert grandchild["name"] and grandchild["ref"]
