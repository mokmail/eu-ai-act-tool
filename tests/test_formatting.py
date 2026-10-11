"""Markdown formatting of extracted provision text."""
from __future__ import annotations

import pytest

from eu_ai_act import data, formatting


def lines(markdown: str) -> list[str]:
    return markdown.split("\n")


def has(markdown: str, prefix: str) -> bool:
    """
    True when some line *starts with* ``prefix``.

    Starting the prefix with spaces is how a test asserts nesting depth, so this
    is stricter than a substring search: "  - **(i)**" cannot be satisfied by a
    top-level "- **(i)**".
    """
    return any(line.startswith(prefix) for line in lines(markdown))


# -- paragraphs and points ---------------------------------------------------
def test_numbered_paragraph_inline_with_text():
    md = formatting.to_markdown(
        "1. The following AI practices shall be prohibited: \n (a) \n the first one; \n"
    )
    assert has(md, "**1.** The following AI practices shall be prohibited:")
    assert has(md, "- **(a)** the first one;")


def test_marker_alone_takes_the_next_line_as_its_body():
    md = formatting.to_markdown("1.\n The purpose of this Regulation is to improve. \n")
    assert has(md, "**1.** The purpose of this Regulation is to improve.")


def test_a_marker_with_inline_text_does_not_also_swallow_the_next_line():
    """Article 2(3): the following sentence is a new paragraph, not a continuation."""
    md = formatting.to_markdown(
        "3. This Regulation does not apply to areas outside Union law. \n"
        "This Regulation does not apply to systems placed on the market. \n"
    )
    assert has(md, "**3.** This Regulation does not apply to areas outside Union law.")
    assert has(md, "This Regulation does not apply to systems placed on the market.")


def test_labels_are_kept_verbatim_not_renumbered():
    md = formatting.to_markdown("(c)\n third item; \n (a)\n first item; \n")
    assert has(md, "- **(c)** third item;")
    assert has(md, "- **(a)** first item;")


def test_source_whitespace_is_collapsed_within_a_block():
    md = formatting.to_markdown("(a)\n have the relevant    competences; \n")
    assert has(md, "- **(a)** have the relevant competences;")


def test_consecutive_points_form_one_tight_list():
    md = formatting.to_markdown("1. shall: \n (a) \n one; \n (b) \n two; \n (c) \n three; \n")
    ls = lines(md)
    first = next(i for i, line in enumerate(ls) if line.startswith("- **(a)**"))
    assert ls[first + 1].startswith("- **(b)**"), ls[first:first + 3]
    assert ls[first + 2].startswith("- **(c)**"), ls[first:first + 3]


def test_separate_paragraphs_after_a_marker_are_not_glued_to_it():
    md = formatting.to_markdown("(iii)\n the item body; \n Point (h) is without prejudice. \n")
    assert has(md, "- **(iii)** the item body;")
    assert has(md, "Point (h) is without prejudice.")
    assert "- **(iii)** the item body; Point (h)" not in md


def test_nothing_is_emitted_for_empty_text():
    assert formatting.to_markdown("") == ""
    assert formatting.to_markdown("   \n  \n") == ""


# -- nesting, decided by sequence -------------------------------------------
def test_a_roman_marker_that_continues_the_letters_stays_top_level():
    """Article 16 runs (a) ... (h), (i): the `(i)` is the next letter."""
    md = formatting.to_markdown("(h)\n eighth; \n (i)\n ninth; \n")
    assert has(md, "- **(h)** eighth;")
    assert has(md, "- **(i)** ninth;")
    assert not has(md, "  - **(i)**")


def test_a_roman_marker_that_breaks_the_sequence_nests():
    """Article 13 runs (b), then (i) (ii) (iii): those are sub-points."""
    md = formatting.to_markdown("(b)\n bee; \n (i)\n one; \n (ii)\n two; \n")
    assert has(md, "- **(b)** bee;")
    assert has(md, "  - **(i)** one;")
    assert has(md, "  - **(ii)** two;")


def test_an_i_that_looks_like_the_next_letter_but_is_proved_roman_nests():
    """
    Article 5 nests (i) (ii) (iii) under (h). The (i) is indistinguishable from
    the successor letter until (ii) arrives.
    """
    md = formatting.to_markdown("(h)\n eighth; \n (i)\n one; \n (ii)\n two; \n (iii)\n three; \n")
    assert has(md, "- **(h)** eighth;")
    assert has(md, "  - **(i)** one;")
    assert has(md, "  - **(ii)** two;")
    assert has(md, "  - **(iii)** three;")


def test_two_letter_markers_are_top_level():
    md = formatting.to_markdown("(aa)\n first; \n (bb)\n second; \n")
    assert has(md, "- **(aa)** first;")
    assert has(md, "- **(bb)** second;")


def test_letters_that_sit_in_the_roman_alphabet_but_are_letters():
    """(d), (l), (m) are roman letters but not roman numerals in an a-z list."""
    md = formatting.to_markdown("(d)\n dee; \n (l)\n ell; \n (m)\n emm; \n")
    for label in ("d", "l", "m"):
        assert has(md, f"- **({label})** dee;" if label == "d" else f"- **({label})**")


def test_nesting_resets_at_each_new_paragraph():
    md = formatting.to_markdown("1. first: \n (a) \n one; \n 2. second: \n (a) \n again; \n")
    assert has(md, "- **(a)** one;")
    assert has(md, "- **(a)** again;")


def test_numbered_definitions_are_top_level_and_their_letters_nest():
    """Article 3's definitions are (1)..(68) and carry (a)..(i) beneath them."""
    md = formatting.to_markdown("lead in: \n (46) \n ‘law enforcement’ means; \n (a) \n nested; \n")
    assert has(md, "- **(46)** ‘law enforcement’ means;")
    assert has(md, "  - **(a)** nested;")


# -- annexes and headings ---------------------------------------------------
def test_annex_section_headings_are_emphasised():
    md = formatting.to_markdown("Section A. List of legislation \n 1.\n Directive 2006/42/EC \n")
    assert has(md, "**Section A.** List of legislation")
    assert has(md, "**1.** Directive 2006/42/EC")


def test_a_leading_title_that_repeats_the_heading_is_dropped():
    text = "List of legislation \n Section A. Framework \n 1.\n Directive 2006/42/EC \n"
    md = formatting.to_markdown(text, title="List of legislation")
    assert not has(md, "List of legislation")
    assert has(md, "**Section A.** Framework")


def test_a_leading_line_that_is_not_the_title_is_kept():
    md = formatting.to_markdown("Providers shall: \n (a) \n comply; \n",
                                title="Obligations of providers of high-risk AI systems")
    assert md.startswith("Providers shall:")


def test_a_trailing_chapter_masthead_is_dropped():
    """Article 4 ends with the next chapter's heading, not with its own text."""
    md = formatting.to_markdown(
        "Providers and deployers shall ensure a sufficient level of AI literacy. \n"
        "CHAPTER II \n PROHIBITED AI PRACTICES \n"
    )
    assert "AI literacy" in md
    assert "CHAPTER II" not in md
    assert "PROHIBITED AI PRACTICES" not in md


def test_an_opening_section_heading_is_kept():
    """Annex I's `Section A.` opens a real list, so it stays."""
    md = formatting.to_markdown("Section A. Framework \n 1.\n Directive 2006/42/EC \n")
    assert has(md, "**Section A.** Framework")


def test_a_trailing_fragment_without_a_heading_is_not_stripped():
    md = formatting.to_markdown("1. A complete sentence follows here. \n and a tail with no period \n")
    assert "and a tail with no period" in md


# -- recitals ---------------------------------------------------------------
def test_a_recital_renders_as_a_plain_paragraph():
    md = formatting.to_markdown(data.recitals()[12]["text"])
    assert not md.startswith("-")
    assert "\n- **" not in md
    assert md.startswith("The notion of")


# -- against the real corpus ------------------------------------------------
def test_the_real_article_3_keeps_definitions_top_level_and_nests_their_letters():
    md = formatting.to_markdown(data.get_article("3")["text"])
    assert has(md, "- **(61)** ‘widespread infringement’ means")
    assert has(md, "  - **(a)** has harmed")
    assert has(md, "    - **(i)** the act or omission originated or took place;")
    assert not has(md, "- **(a)"), \
        "Article 3 has no top-level letter points; its definitions are the top level"


def test_the_real_article_16_keeps_i_at_the_top_level():
    md = formatting.to_markdown(data.get_article("16")["text"])
    assert has(md, "- **(h)**")
    assert has(md, "- **(i)**")
    assert not has(md, "  - **(i)**")


def test_the_real_article_13_nests_i_through_vii():
    md = formatting.to_markdown(data.get_article("13")["text"])
    for label in ("i", "ii", "iii", "iv", "v", "vi", "vii"):
        assert has(md, f"  - **({label})**"), f"({label}) should be a sub-point"


def test_the_real_article_5_nests_the_exceptions_under_h():
    md = formatting.to_markdown(data.get_article("5")["text"])
    assert has(md, "- **(h)**")
    assert has(md, "  - **(i)**")
    assert has(md, "  - **(ii)**")
    assert has(md, "  - **(iii)**")


def test_the_real_article_7_has_both_a_letter_i_and_a_nested_i():
    """(h) → (i) is a letter; (k) → (i) is a sub-point. Same article."""
    md = formatting.to_markdown(data.get_article("7")["text"])
    assert has(md, "- **(i)**")
    assert has(md, "  - **(i)**")


def test_the_real_article_108_numbers_its_amendment_paragraphs():
    md = formatting.to_markdown(data.get_article("108")["text"])
    for label in ("1", "2", "3"):
        assert has(md, f"- **({label})**")


@pytest.mark.parametrize("number", ["4", "5", "63", "98"])
def test_no_chapter_or_section_masthead_survives_in_an_article(number):
    md = formatting.to_markdown(data.get_article(number)["text"])
    for line in lines(md):
        assert not line.startswith("CHAPTER"), f"Article {number}: {line!r}"
        assert not line.startswith("SECTION"), f"Article {number}: {line!r}"


def test_the_real_annex_i_opens_with_its_section():
    annex = data.annexes()["I"]
    md = formatting.to_markdown(annex["text"], annex.get("title"))
    assert md.startswith("**Section A.** List of Union harmonisation legislation")


def test_every_provision_formats_and_keeps_its_opening_words():
    """A sweep: nothing raises, nothing comes out empty, no text is dropped."""
    provisions = (
        list(data.articles().items())
        + list(data.annexes().items())
        + list(data.recitals().items())
    )
    assert len(provisions) > 300

    for key, provision in provisions:
        raw = provision["text"]
        md = formatting.to_markdown(raw, provision.get("title"))
        assert md.strip(), f"{key} produced no markdown"

        first = raw.split("\n")[0].strip()
        if provision.get("title") and first and first != provision["title"]:
            head = first.split()[0]
            assert head in md, f"{key}: lost its opening word {head!r}"


def test_no_provision_has_a_run_of_blank_lines_or_trailing_whitespace():
    for key, provision in list(data.articles().items()):
        md = formatting.to_markdown(provision["text"], provision.get("title"))
        assert "\n\n\n" not in md, key
        for line in lines(md):
            assert line == line.rstrip(), f"{key}: trailing whitespace on {line!r}"


@pytest.mark.parametrize("number", ["1", "5", "16", "113"])
def test_article_markdown_starts_with_a_readable_paragraph(number):
    provision = data.get_article(number)
    md = formatting.to_markdown(provision["text"], provision.get("title"))
    first = lines(md)[0]
    assert first and not first.startswith("- ")
    assert len(first) > 10
