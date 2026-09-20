# -*- coding: utf-8 -*-
"""Sync the Google Scholar figures into the page.

Google Scholar has no public API and blocks datacentre IPs, so the numbers come from one of:

    python tools/sync-scholar.py --serpapi-key $SERPAPI_KEY          # fetch (needs a key)
    python tools/sync-scholar.py --from-json scholar.json            # hand-prepared numbers
    python tools/sync-scholar.py --from-json scholar.json --report    # show the diff only

`--from-json` takes exactly what the site needs, so the profile can be refreshed by hand in a
minute without any third-party service:

    {
      "asOf": "2026-09-20",
      "citations": 161, "hIndex": 8, "i10Index": 7, "indexedWorks": 36,
      "citationsByYear": {"2024": 3, "2025": 20, "2026": 138},
      "articles": [{"title": "AI-Enabled Cybersecurity Using Synthetic Data", "citations": 17}]
    }

`articles` may list any subset; titles are matched loosely against the publication cards, and a
card whose title is not listed keeps its current count. Unmatched titles are reported, never
guessed at. Publications the page does not have are reported for manual addition, exactly as
tools/sync-orcid.py does.

Afterwards regenerate the derived files and check the result:

    pwsh tools/build-profile.ps1 -AsOf <date> && python tools/build-llms-pubs.py
    python tools/validate.py
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request

SCHOLAR_ID = "lQig7SEAAAAJ"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOT_THRESHOLD = 10          # the page highlights a card from this many citations up
CHART_MAX_PX = 129          # pixel height used for the tallest bar in the per-year chart


def read(name):
    # .ps1 files carry a UTF-8 BOM on purpose (see build-profile.ps1); read it as a signature
    # rather than as text, or rewriting the file would give it a second one.
    enc = "utf-8-sig" if name.endswith(".ps1") else "utf-8"
    return io.open(os.path.join(ROOT, name), encoding=enc).read()


def write(name, text):
    enc = "utf-8-sig" if name.endswith(".ps1") else "utf-8"
    io.open(os.path.join(ROOT, name), "w", encoding=enc, newline="").write(text)


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def human_date(iso):
    y, mo, d = iso.split("-")
    months = ["January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"]
    return "%d %s %s" % (int(d), months[int(mo) - 1], y)


# ── sources ───────────────────────────────────────────────────────────────────

def from_serpapi(key, as_of):
    """Fetch the author profile through SerpApi and reduce it to our own shape."""
    url = "https://serpapi.com/search.json?" + urllib.parse.urlencode({
        "engine": "google_scholar_author",
        "author_id": SCHOLAR_ID,
        "hl": "en",
        "num": "100",
        "api_key": key,
    })
    with urllib.request.urlopen(url, timeout=90) as r:
        d = json.loads(r.read().decode("utf-8"))
    if "error" in d:
        raise SystemExit("SerpApi error: %s" % d["error"])
    table = {}
    for row in d.get("cited_by", {}).get("table", []):
        for k, v in row.items():
            if isinstance(v, dict) and "all" in v:
                table[k] = v["all"]
    graph = {str(g["year"]): g["citations"] for g in d.get("cited_by", {}).get("graph", [])}
    articles = [{"title": a.get("title", ""),
                 "citations": int((a.get("cited_by") or {}).get("value") or 0)}
                for a in d.get("articles", [])]
    return {
        "asOf": as_of,
        "citations": table.get("citations"),
        "hIndex": table.get("h_index"),
        "i10Index": table.get("i10_index"),
        "indexedWorks": len(articles),
        "citationsByYear": graph,
        "articles": articles,
    }


def from_file(path, as_of):
    d = json.load(io.open(path, encoding="utf-8"))
    d.setdefault("asOf", as_of)
    return d


# ── the page ──────────────────────────────────────────────────────────────────

CARD_RE = re.compile(
    r'(?s)<article class="pub-card" data-type="(?P<type>[^"]+)" data-year="(?P<year>\d+)"'
    r' data-cites="(?P<cites>\d+)" data-order="(?P<order>\d+)" id="(?P<id>pub-\d+)"(?P<rest>[^>]*)>'
    r'(?P<body>.*?)</article>')


def cards_of(html):
    out = []
    for m in CARD_RE.finditer(html):
        body = m.group("body")
        out.append({
            "id": m.group("id"),
            "cites": int(m.group("cites")),
            "year": int(m.group("year")),
            "title": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", re.search(
                r'(?s)<h3 class="pub-title">(.*?)</h3>', body).group(1))).replace("&amp;", "&").strip(),
            "venue": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", re.search(
                r'(?s)<div class="pub-venue">(.*?)</div>', body).group(1))).strip(),
            "span": m.span(),
        })
    return out


def set_card_citations(html, pid, n):
    """Set data-cites, the visible citation line and the JSON-LD counter for one card."""
    m = re.search(r'(?s)(<article class="pub-card"[^>]*id="%s"[^>]*>)(?P<body>.*?)(</article>)'
                  % re.escape(pid), html)
    head, body, tail = m.group(1), m.group("body"), m.group(3)
    head = re.sub(r'data-cites="\d+"', 'data-cites="%d"' % n, head)
    line = '<div class="pub-citations%s">%d citation%s</div>' % (
        " hot" if n >= HOT_THRESHOLD else "", n, "" if n == 1 else "s")
    if re.search(r'<div class="pub-citations[^"]*">.*?</div>', body):
        if n:
            body = re.sub(r'<div class="pub-citations[^"]*">.*?</div>', lambda _m: line, body, count=1)
        else:  # dropped back to zero: remove the line entirely, as uncited cards have none
            body = re.sub(r'\n\s*<div class="pub-citations[^"]*">.*?</div>', "", body, count=1)
    elif n:
        indent = re.search(r'\n(\s*)<h3 class="pub-title">', body).group(1)
        body = re.sub(r'(\n\s*)(<h3 class="pub-title">)',
                      lambda _m: "\n%s%s%s%s" % (indent, line, _m.group(1), _m.group(2)),
                      body, count=1)
    html = html[:m.start()] + head + body + tail + html[m.end():]

    return re.sub(
        r'("@id": "https://ilsamaritano\.github\.io/#%s",(?:.|\n)*?"userInteractionCount": )\d+'
        % re.escape(pid), lambda _m: "%s%d" % (_m.group(1), n), html, count=1)


def reorder(html):
    """Renumber data-order and reorder the cards: year desc, then citations desc."""
    anchor = '<div class="pub-list" id="pub-list">'
    start = html.index(anchor) + len(anchor)
    end = html.index('\n      </div>\n      <p class="pub-empty"', start)
    blocks = re.findall(r'(?s)<article class="pub-card".*?</article>', html[start:end])

    def key(c):
        year = int(re.search(r'data-year="(\d+)"', c).group(1))
        cites = int(re.search(r'data-cites="(\d+)"', c).group(1))
        order = int(re.search(r'data-order="(\d+)"', c).group(1))
        return (-(year if year else -1), -cites, order)

    blocks.sort(key=key)
    body = "\n" + "\n\n".join("        " + re.sub(r'data-order="\d+"', 'data-order="%d"' % i, c)
                              for i, c in enumerate(blocks)) + "\n"
    return html[:start] + body + html[end:]


def compact_venue(venue):
    """Short venue label for the impact panel, which gives each entry a single line.

    Prefers a parenthesised acronym with a year — "(PerCom 2025)", "(DS-RT 2025)" — since that
    is how a reader recognises the venue; falls back to the leading words of the full name.
    """
    acronym = re.search(r"\(([A-Z][A-Za-z0-9-]{1,14}(?:\s+Workshops)?\s+\d{4})\)", venue)
    if acronym:
        label = acronym.group(1)
        if re.match(r"\s*(IEEE|ACM|Springer|Elsevier)\b", venue):
            label = re.match(r"\s*(IEEE|ACM|Springer|Elsevier)\b", venue).group(1) + " " + label
        elif re.search(r"\bIEEE\b", venue.split("(")[0]):
            label = "IEEE " + label
        return label
    v = re.sub(r"\s*\([^)]*\)", "", venue).strip(" ·—-")
    return v if len(v) <= 62 else v[:59].rstrip(" ,;·—-") + "…"


def top_cited_panel(html, cards):
    """Rebuild the five most-cited works shown in the impact panel."""
    top = sorted(cards, key=lambda c: (-c["cites"], c["title"]))[:5]
    rows = []
    for c in top:
        venue = compact_venue(c["venue"]).replace("&", "&amp;")
        rows.append('            <li><span><span class="tc-title">%s</span>'
                    '<span class="tc-venue">%s</span></span>'
                    '<span class="tc-count">%d</span></li>'
                    % (c["title"].replace("&", "&amp;"), venue, c["cites"]))
    return re.sub(r'(?s)(<ol class="top-cited">\n).*?(\n\s*</ol>)',
                  lambda m: m.group(1) + "\n".join(rows) + m.group(2), html, count=1)


def set_chart(html, by_year):
    """Rewrite the citations-per-year bars and the screen-reader table."""
    years = sorted(by_year)
    if not years:
        return html
    peak = max(by_year[y] for y in years) or 1
    cols = []
    for y in years:
        n = by_year[y]
        px = max(3, int(round(n / peak * CHART_MAX_PX)))
        tip = "%d citations in %s%s" % (n, y, " (so far)" if y == years[-1] else "")
        cols.append('            <div class="bar-col">\n'
                    '              <span class="bar-val">%d</span>\n'
                    '              <div class="bar" style="--h:%dpx"><span class="bar-tip">%s</span></div>\n'
                    '              <span class="bar-year">%s</span>\n'
                    '            </div>' % (n, px, tip, y))
    html = re.sub(r'(?s)(<div class="cite-chart" aria-hidden="true">\n).*?(\n\s*</div>\n\s*<table class="sr-only">)',
                  lambda m: m.group(1) + "\n".join(cols) + m.group(2), html, count=1)
    rows = "\n".join("            <tr><td>%s</td><td>%d</td></tr>" % (y, by_year[y]) for y in years)
    return re.sub(r'(?s)(<tr><th scope="col">Year</th><th scope="col">Citations</th></tr>\n).*?(\n\s*</table>)',
                  lambda m: m.group(1) + rows + m.group(2), html, count=1)


def set_numbers(html, d, cards):
    """Every place the page states a metric."""
    cit, h, i10, works = d["citations"], d["hIndex"], d["i10Index"], d["indexedWorks"]
    listed = len(cards)
    as_of, as_of_h = d["asOf"], human_date(d["asOf"])

    html = re.sub(r'<span class="metric-num" data-count="\d+">\d+</span>\s*(<span class="metric-label">Citations)',
                  lambda m: '<span class="metric-num" data-count="%d">%d</span>\n          %s'
                            % (cit, cit, m.group(1)), html)
    for label, val in (("h-index", h), ("i10-index", i10), ("Publications", works)):
        html = re.sub(r'(<span class="metric-num[^"]*" data-count=")\d+(">)\d+(</span>\s*'
                      r'<span class="metric-label">%s)' % re.escape(label),
                      lambda m, v=val: "%s%d%s%d%s" % (m.group(1), v, m.group(2), v, m.group(3)), html)

    html = re.sub(r"Source: Google Scholar · updated [^<]+", "Source: Google Scholar · updated " + as_of_h, html)
    html = re.sub(r'"dateModified": "[\d-]+"', '"dateModified": "%s"' % as_of, html)
    html = re.sub(r'"observationDate": "[\d-]+"', '"observationDate": "%s"' % as_of, html)
    html = re.sub(r"synced \d{4}-\d{2}-\d{2}", "synced " + as_of, html)
    html = re.sub(r'("propertyID": "citationCount", "value": )\d+',
                  lambda m: "%s%d" % (m.group(1), cit), html)
    html = re.sub(r'("propertyID": "hIndex", "value": )\d+', lambda m: "%s%d" % (m.group(1), h), html)
    html = re.sub(r'("propertyID": "i10Index", "value": )\d+', lambda m: "%s%d" % (m.group(1), i10), html)
    html = re.sub(r'("propertyID": "workCount", "value": )\d+', lambda m: "%s%d" % (m.group(1), works), html)
    html = re.sub(r'("propertyID": "publicationCount", "value": )\d+',
                  lambda m: "%s%d" % (m.group(1), listed), html)
    html = re.sub(r'"description": "\d+ works indexed by Google Scholar plus \d+ further works',
                  '"description": "%d works indexed by Google Scholar plus %d further works'
                  % (works, listed - works), html)

    # prose
    html = re.sub(r"\d+ publications, \d+ citations", "%d publications, %d citations" % (listed, cit), html)
    html = re.sub(r"\d+ publications; the \d+ indexed by Google Scholar are cited \d+ times, h-index \d+, "
                  r"i10-index \d+ \([^)]*\)",
                  "%d publications; the %d indexed by Google Scholar are cited %d times, h-index %d, "
                  "i10-index %d (%s)" % (listed, works, cit, h, i10, as_of_h), html)
    html = re.sub(r"<strong>\d+ publications</strong> — the \d+ indexed by Google Scholar are cited",
                  "<strong>%d publications</strong> — the %d indexed by Google Scholar are cited"
                  % (listed, works), html)
    html = re.sub(r"<strong>\d+ times \(h-index \d+\)</strong>",
                  "<strong>%d times (h-index %d)</strong>" % (cit, h), html)
    html = re.sub(r">\d+ citations · h-index \d+( ↗)?<",
                  lambda m: ">%d citations · h-index %d%s<" % (cit, h, m.group(1) or ""), html)
    # every remaining prose mention of the indices (meta descriptions, og/twitter cards, …)
    html = re.sub(r"h-index \d+", "h-index %d" % h, html)
    html = re.sub(r"i10-index \d+", "i10-index %d" % i10, html)
    html = re.sub(r"Bibliometrics updated [^<]+", "Bibliometrics updated " + as_of_h, html)
    return html


def sync_side_files(d, cards):
    cit, h, i10, works = d["citations"], d["hIndex"], d["i10Index"], d["indexedWorks"]
    listed, as_of, as_of_h = len(cards), d["asOf"], human_date(d["asOf"])
    years = sorted(d["citationsByYear"])
    by_year = " · ".join(
        "%d (%s%s)" % (d["citationsByYear"][y], y, ", year to date" if y == years[-1] else "")
        for y in years)
    touched = []

    t = before = read("llms.txt")
    t = re.sub(r"> \d+ publications listed here; the \d+ indexed by Google Scholar \([^)]*\) are cited\n"
               r"> \d+ times · h-index \d+ · i10-index \d+\.",
               "> %d publications listed here; the %d indexed by Google Scholar (%s) are cited\n"
               "> %d times · h-index %d · i10-index %d." % (listed, works, as_of_h, cit, h, i10), t)
    t = re.sub(r"> Citations per year: .*", "> Citations per year: %s." % by_year, t, count=1)
    t = re.sub(r"> Last updated: [\d-]+\.", "> Last updated: %s." % as_of, t)
    t = re.sub(r'"citations": \d+, "hIndex": \d+, "i10Index": \d+, "worksIndexedByScholar": \d+,'
               r' "publicationsListed": \d+, "asOf": "[\d-]+"',
               '"citations": %d, "hIndex": %d, "i10Index": %d, "worksIndexedByScholar": %d,'
               ' "publicationsListed": %d, "asOf": "%s"' % (cit, h, i10, works, listed, as_of), t)
    t = re.sub(r'"citationsByYear": \{[^}]*\}',
               '"citationsByYear": { %s }' % ", ".join('"%s": %d' % (y, d["citationsByYear"][y])
                                                       for y in sorted(d["citationsByYear"])), t)
    t = re.sub(r"all \d+ publications", "all %d publications" % listed, t)
    t = re.sub(r"`ItemList` of \d+", "`ItemList` of %d" % listed, t)
    t = re.sub(r"citation count as of [\d-]+", "citation count as of " + as_of, t)
    if t != before:
        write("llms.txt", t)
        touched.append("llms.txt")

    t = before = read("readme.md")
    t = re.sub(r"Citations-\d+-", "Citations-%d-" % cit, t)
    t = re.sub(r"H--Index-\d+-", "H--Index-%d-" % h, t)
    t = re.sub(r"i10--Index-\d+-", "i10--Index-%d-" % i10, t)
    t = re.sub(r"\| \*\*Total Citations\*\* \| \d+ \(Google Scholar, [^)]*\) \|",
               "| **Total Citations** | %d (Google Scholar, %s) |" % (cit, as_of_h), t)
    t = re.sub(r"\| \*\*H-Index / i10-Index\*\* \| \d+ / \d+ \|",
               "| **H-Index / i10-Index** | %d / %d |" % (h, i10), t)
    t = re.sub(r"\| \*\*Publications\*\* \| \d+ — \d+ indexed by Google Scholar",
               "| **Publications** | %d — %d indexed by Google Scholar" % (listed, works), t)
    t = re.sub(r"all \d+ publications \(id, title", "all %d publications (id, title" % listed, t)
    t = re.sub(r"Most-cited works \(Google Scholar, [^)]*\)",
               "Most-cited works (Google Scholar, %s)" % as_of_h, t)
    t = re.sub(r"observation date \(`[\d-]+`\)", "observation date (`%s`)" % as_of, t)
    if t != before:
        write("readme.md", t)
        touched.append("readme.md")

    t = before = read("sitemap.xml")
    t = re.sub(r"<lastmod>[\d-]+</lastmod>", "<lastmod>%s</lastmod>" % as_of, t)
    if t != before:
        write("sitemap.xml", t)
        touched.append("sitemap.xml")

    gen = before = read("tools/build-profile.ps1")
    gen = re.sub(r'(\[string\]\$AsOf = ")[\d-]+(")', lambda m: m.group(1) + as_of + m.group(2), gen)
    gen = re.sub(r"(citations        = )\d+", lambda m: "%s%d" % (m.group(1), cit), gen)
    gen = re.sub(r"(hIndex           = )\d+", lambda m: "%s%d" % (m.group(1), h), gen)
    gen = re.sub(r"(i10Index         = )\d+", lambda m: "%s%d" % (m.group(1), i10), gen)
    gen = re.sub(r"(indexedWorks     = )\d+", lambda m: "%s%d" % (m.group(1), works), gen)
    gen = re.sub(r"citationsByYear  = \[ordered\]@\{[^}]*\}",
                 "citationsByYear  = [ordered]@{ %s }"
                 % "; ".join("'%s' = %d" % (y, d["citationsByYear"][y])
                             for y in sorted(d["citationsByYear"])), gen)
    gen = re.sub(r"of which \d+ are indexed by Google Scholar",
                 "of which %d are indexed by Google Scholar" % works, gen)
    if gen != before:
        write("tools/build-profile.ps1", gen)
        touched.append("tools/build-profile.ps1")

    return touched


def main():
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--serpapi-key")
    src.add_argument("--from-json")
    ap.add_argument("--as-of", default=None, help="observation date (default: today, UTC)")
    ap.add_argument("--report", action="store_true", help="show the diff without writing")
    args = ap.parse_args()

    as_of = args.as_of
    if not as_of:
        import datetime
        as_of = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    d = from_serpapi(args.serpapi_key, as_of) if args.serpapi_key else from_file(args.from_json, as_of)
    for k in ("citations", "hIndex", "i10Index", "indexedWorks", "citationsByYear"):
        if d.get(k) in (None, {}):
            raise SystemExit("the Scholar data is missing '%s'" % k)
    d["asOf"] = args.as_of or d.get("asOf") or as_of

    html = read("index.html")
    cards = cards_of(html)
    by_norm = {norm(c["title"]): c for c in cards}

    print("Scholar %s — %d citations · h-index %d · i10-index %d · %d indexed works"
          % (d["asOf"], d["citations"], d["hIndex"], d["i10Index"], d["indexedWorks"]))

    cite_changes, unmatched = [], []
    for a in d.get("articles", []):
        n = norm(a["title"])
        c = by_norm.get(n)
        if c is None:
            for k, cand in by_norm.items():
                if len(n) >= 25 and (k.startswith(n) or n.startswith(k)):
                    c = cand
                    break
        if c is None:
            unmatched.append(a)
            continue
        if c["cites"] != int(a["citations"]):
            cite_changes.append((c["id"], c["cites"], int(a["citations"]), c["title"]))

    print("\nPer-publication citation changes: %d" % len(cite_changes))
    for pid, old, new, title in cite_changes:
        print("  %-8s %3d → %-3d %s" % (pid, old, new, title[:60]))
    if unmatched:
        print("\nON SCHOLAR BUT NOT ON THE SITE (%d) — add these by hand:" % len(unmatched))
        for a in unmatched:
            print("  · %s [%s citations]" % (a["title"], a["citations"]))

    if args.report:
        print("\nreport only — drop --report to write the changes")
        return 2 if unmatched else 0

    for pid, _old, new, _title in cite_changes:
        html = set_card_citations(html, pid, new)
    html = set_numbers(html, d, cards)
    html = set_chart(html, d["citationsByYear"])
    html = reorder(html)
    html = top_cited_panel(html, cards_of(html))
    write("index.html", html)
    touched = ["index.html"] + sync_side_files(d, cards)

    print("\nupdated: %s" % ", ".join(touched))
    print("now run:  pwsh tools/build-profile.ps1 -AsOf %s && python tools/build-llms-pubs.py"
          " && python tools/validate.py" % d["asOf"])
    return 2 if unmatched else 0


if __name__ == "__main__":
    sys.exit(main())
