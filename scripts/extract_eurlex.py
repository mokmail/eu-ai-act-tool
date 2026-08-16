#!/usr/bin/env python3
"""
Extract the full text of Regulation (EU) 2024/1689 (the EU AI Act) from the
official EUR-Lex HTML and emit structured JSON.

Source: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32024R1689
Official citation: Regulation (EU) 2024/1689 of the European Parliament and of
the Council of 13 June 2024 laying down harmonised rules on artificial
intelligence (Artificial Intelligence Act), OJ L, 2024/1689, 12.7.2024.
"""
import json
import re
import sys
from html import unescape

NS = "\xa0"


def clean(text: str) -> str:
    """Strip tags, collapse whitespace, unescape entities."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace(NS, " ")
    text = unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def extract(html: str) -> dict:
    # --- Recitals ---
    recitals = []
    # Recital headings look like: <p class="oj-ti-art">(1)</p> ... or similar
    # We'll capture the body between consecutive recital markers.
    # First, find the recitals section boundaries.
    recital_markers = list(re.finditer(r"<p class=\"oj-sti-art\">\s*\((\d+)\)\s*</p>", html))
    # Fallback: recitals are numbered (1)...(180) in the preamble
    if not recital_markers:
        recital_markers = list(re.finditer(r"<p class=\"oj-sti-art\">\((\d+)\)</p>", html))

    # --- Recitals ---
    # Recital markers: <p class="oj-normal">(N)</p> in the preamble
    recitals = []
    art1 = html.find('art_1')
    preamble = html[:art1] if art1 != -1 else html
    recital_pattern = re.compile(r'<p class="oj-normal">\s*\((\d+)\)\s*</p>', re.S)
    rec_positions = [(m.start(), int(m.group(1))) for m in recital_pattern.finditer(preamble)]
    for i, (start, num) in enumerate(rec_positions):
        body_start = preamble.find("</p>", start) + 4
        if i + 1 < len(rec_positions):
            body_end = rec_positions[i + 1][0]
        else:
            body_end = len(preamble)
        body = clean(preamble[body_start:body_end])
        recitals.append({"number": num, "text": body})

    # --- Articles ---
    # Article heading: <p class="oj-ti-art">Article N</p>
    # followed by <div class="eli-title"><p class="oj-sti-art">Title</p></div>
    article_pattern = re.compile(
        r'<p[^>]*class="oj-ti-art"[^>]*>\s*Article[\s\xa0]+(\d+[a-z]?)\s*</p>',
        re.S,
    )
    articles = []
    positions = []
    for m in article_pattern.finditer(html):
        num = m.group(1)
        # find the title in the following eli-title div
        after = html[m.end():m.end() + 2000]
        tm = re.search(r'<p class="oj-sti-art">(.*?)</p>', after, re.S)
        title = clean(tm.group(1)) if tm else ""
        positions.append((m.start(), num, title))

    # Extract body text for each article: from end of its title div to start of next article heading
    for i, (start, num, title) in enumerate(positions):
        # body starts after the eli-title div closes
        title_div_end = html.find("</div>", html.find("eli-title", start))
        body_start = html.find(">", title_div_end) + 1
        if i + 1 < len(positions):
            body_end = positions[i + 1][0]
        else:
            body_end = len(html)
        body = clean(html[body_start:body_end])
        articles.append({"number": num, "title": title, "text": body})

    # --- Annexes ---
    annexes = []
    annex_pattern = re.compile(
        r'<p class="oj-doc-ti"[^>]*>\s*ANNEX[\s\xa0]+([IVX]+)\s*</p>\s*'
        r'<p class="oj-doc-ti"[^>]*>(.*?)</p>',
        re.S,
    )
    annex_positions = []
    for m in annex_pattern.finditer(html):
        num = m.group(1)
        title = clean(m.group(2))
        annex_positions.append((m.start(), num, title))
    for i, (start, num, title) in enumerate(annex_positions):
        body_start = html.find("</p>", html.find("oj-doc-ti", start) + 1) + 4
        if i + 1 < len(annex_positions):
            body_end = annex_positions[i + 1][0]
        else:
            body_end = len(html)
        body = clean(html[body_start:body_end])
        annexes.append({"number": num, "title": title, "text": body})

    return {
        "source": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32024R1689",
        "citation": "Regulation (EU) 2024/1689 of the European Parliament and of the Council of 13 June 2024 laying down harmonised rules on artificial intelligence (Artificial Intelligence Act), OJ L, 2024/1689, 12.7.2024.",
        "recitals": recitals,
        "articles": articles,
        "annexes": annexes,
    }


def main():
    if len(sys.argv) < 3:
        print("usage: extract_eurlex.py <input.html> <output.json>")
        sys.exit(1)
    html = open(sys.argv[1], encoding="utf-8").read()
    data = extract(html)
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Extracted {len(data['articles'])} articles, {len(data['annexes'])} annexes -> {sys.argv[2]}")


if __name__ == "__main__":
    main()
