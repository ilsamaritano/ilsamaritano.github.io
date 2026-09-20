# -*- coding: utf-8 -*-
"""Sync the site against the public ORCID record.

    python tools/sync-orcid.py                 # report only (no files touched)
    python tools/sync-orcid.py --apply         # apply the safe updates
    python tools/sync-orcid.py --snapshot F    # use a saved record instead of the network

What it applies (idempotent, safe to re-run):
  * peer-review counts per journal, the review/journal/publisher totals, and every prose
    figure derived from them, across index.html, llms.txt and readme.md;
  * DOI links (or the ARPI handle when ORCID has no DOI) on publication cards that lack one,
    plus a matching `identifier` entry in the publication JSON-LD;
  * the "synced" date stamps.

What it refuses to apply, reporting it instead: works that exist on ORCID but not on the site
(or vice versa). Adding a publication needs an editorial decision — venue wording, output type,
position in the list — so the script prints a ready-to-paste card and exits with code 2.

ORCID is the source of truth for peer review, DOIs and the work list. Google Scholar remains the
source for citation counts (see tools/sync-scholar.py).
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import urllib.request

ORCID = "0009-0002-4632-1179"
API = "https://pub.orcid.org/v3.0/%s/record" % ORCID
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ISSN → (display name, publisher) for the journals reviewed for. ORCID stores only the ISSN,
# so the human-readable names live here; add a line when a new ISSN shows up in the report.
JOURNALS = {
    "2731-0809": ("Discover Artificial Intelligence", "Springer Nature"),
    "2045-2322": ("Scientific Reports", "Springer Nature"),
    "1574-1192": ("Pervasive and Mobile Computing", "Elsevier"),
    "2162-2388": ("IEEE Transactions on Neural Networks and Learning Systems", "IEEE"),
    "1615-5270": ("International Journal of Information Security", "Springer Nature"),
    "2097-406X": ("Big Data Mining and Analytics", "Tsinghua University Press"),
    "1557-7341": ("ACM Computing Surveys", "ACM"),
    "0167-4048": ("Computers & Security", "Elsevier"),
    "0167-739X": ("Future Generation Computer Systems", "Elsevier"),
    "0140-3664": ("Computer Communications", "Elsevier"),
    "1875-8924": ("Journal of Computer Security", "SAGE Publications"),
    "1573-7543": ("Cluster Computing", "Springer Nature"),
    "2192-113X": ("Journal of Cloud Computing", "Springer Nature"),
    "2196-1115": ("Journal of Big Data", "Springer Nature"),
    "2948-2992": ("Discover Computing", "Springer Nature"),
    "2364-4168": ("International Journal of Data Science and Analytics", "Springer Nature"),
    "2213-1248": ("Journal of King Saud University – Computer and Information Sciences", "Springer Nature"),
    "2376-5992": ("PeerJ Computer Science", "PeerJ"),
    "1546-2218": ("Computers, Materials & Continua", "Tech Science Press"),
    "0267-6192": ("Computer Systems Science and Engineering", "Tech Science Press"),
}


# ── helpers ───────────────────────────────────────────────────────────────────

# ORCID titles that belong to a card the automatic matcher cannot reach, because the site
# merges two records ORCID keeps apart, or because the title was revised on publication.
# Keyed by the normalised ORCID title.
ALIASES = {
    # ESREL 2026: ORCID has both the "Digital Twin-Based What-If Analysis" and the
    # "Security Twin-Based What-If Analysis Framework" wording; the site lists one card.
    "quantifyingresilienceofcyberphysicalsystemstozerodaythreatsadigitaltwinbasedwhatifanalysis": "pub-6",
    # Published in Knowledge-Based Systems as "...LLM-driven Agentic and Multi-Agent Systems";
    # ORCID keeps the earlier SSRN preprint under the original title as a separate record.
    "vulnerabilitiesinautonomousexecutionasurveyofsecuritythreatsanddefensesinllmdrivenagenticandmultiagentsystems": "pub-36",
    "vulnerabilitiesinautonomousexecutionasurveyofsecuritythreatsanddefensesinllmdrivenmultiagentsystems": "pub-36",
}


def norm(s):
    """Normalise a title for matching: lowercase, alphanumerics only."""
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def read(path):
    # .ps1 files carry a UTF-8 BOM on purpose (see build-profile.ps1); read it as a signature
    # rather than as text, or rewriting the file would give it a second one.
    enc = "utf-8-sig" if path.endswith(".ps1") else "utf-8"
    return io.open(os.path.join(ROOT, path), encoding=enc).read()


def write(path, text):
    # .ps1 files must keep their UTF-8 BOM, or Windows PowerShell 5.1 reads them as ANSI
    # and their em dashes and accents become mojibake (the script then fails to parse).
    enc = "utf-8-sig" if path.endswith(".ps1") else "utf-8"
    io.open(os.path.join(ROOT, path), "w", encoding=enc, newline="").write(text)


def fetch_record(snapshot=None):
    if snapshot:
        return json.load(io.open(snapshot, encoding="utf-8"))
    req = urllib.request.Request(API, headers={"Accept": "application/json",
                                               "User-Agent": "ilsamaritano.github.io sync"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


# ── ORCID side ────────────────────────────────────────────────────────────────

def orcid_reviews(rec):
    """{issn: review count} from the peer-review section."""
    out = {}
    for g in rec["activities-summary"]["peer-reviews"]["group"]:
        issn = g["external-ids"]["external-id"][0]["external-id-value"].replace("issn:", "")
        out[issn] = sum(len(x["peer-review-summary"]) for x in g["peer-review-group"])
    return out


def orcid_works(rec):
    """[{title, year, type, ids: {doi, handle, url}}] — one entry per work group."""
    works = []
    for g in rec["activities-summary"]["works"]["group"]:
        s = g["work-summary"][0]
        ids = {}
        for e in (g.get("external-ids") or {}).get("external-id", []):
            t = e["external-id-type"]
            if t not in ids:
                ids[t] = e["external-id-value"]
        pub = s.get("publication-date") or {}
        works.append({
            "title": s["title"]["title"]["value"],
            "year": (pub.get("year") or {}).get("value"),
            "type": s.get("type"),
            "journal": ((s.get("journal-title") or {}) or {}).get("value"),
            "url": ((s.get("url") or {}) or {}).get("value"),
            "ids": ids,
            "put_code": s["put-code"],
        })
    return works


def best_link(w):
    """The most citable link ORCID offers for a work: DOI first, then the ARPI handle."""
    if "doi" in w["ids"]:
        return "DOI", "https://doi.org/" + w["ids"]["doi"]
    if "handle" in w["ids"]:
        return "ARPI", "https://arpi.unipi.it/handle/" + w["ids"]["handle"]
    if w["url"]:
        return "Record", w["url"]
    return None, None


# ── site side ─────────────────────────────────────────────────────────────────

CARD_RE = re.compile(
    r'(?s)<article class="pub-card"[^>]*id="(?P<id>pub-\d+)"[^>]*>(?P<body>.*?)</article>')


def site_cards(html):
    cards = {}
    for m in CARD_RE.finditer(html):
        body = m.group("body")
        title = re.sub(r"<[^>]+>", "", re.search(r"(?s)<h3 class=\"pub-title\">(.*?)</h3>", body).group(1))
        title = re.sub(r"\s+", " ", title).replace("&amp;", "&").strip()
        links = re.findall(r'<a href="([^"]+)"', body)
        cards[m.group("id")] = {"title": title, "links": links, "span": m.span(), "body": body}
    return cards


def match_work(work_title, cards):
    """Match an ORCID title to a site card, tolerating subtitle/case differences."""
    a = norm(work_title)
    if a in ALIASES:
        return ALIASES[a]
    for pid, c in cards.items():
        b = norm(c["title"])
        if a == b or (len(a) >= 25 and len(b) >= 25 and (a.startswith(b) or b.startswith(a))):
            return pid
    return None


# ── report / apply ────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write the safe updates to disk")
    ap.add_argument("--snapshot", help="path to a saved ORCID record JSON")
    ap.add_argument("--save-snapshot", help="write the fetched record here")
    ap.add_argument("--as-of", default=None, help="date stamp to write (YYYY-MM-DD)")
    args = ap.parse_args()

    rec = fetch_record(args.snapshot)
    if args.save_snapshot:
        io.open(args.save_snapshot, "w", encoding="utf-8", newline="\n").write(
            json.dumps(rec, indent=1, ensure_ascii=False))

    reviews = orcid_reviews(rec)
    works = orcid_works(rec)
    html = read("index.html")
    cards = site_cards(html)

    problems = []
    print("ORCID %s — %d work groups, %d review journals, %d reviews"
          % (ORCID, len(works), len(reviews), sum(reviews.values())))

    # 1. peer review -----------------------------------------------------------
    unknown = sorted(set(reviews) - set(JOURNALS))
    if unknown:
        problems.append("unknown ISSN(s) on ORCID, add them to JOURNALS in this script: %s"
                        % ", ".join(unknown))
    site_counts = {m.group("issn"): int(m.group("n")) for m in re.finditer(
        r'ISSN (?P<issn>[\dX-]+)</span></span><span class="rv-count">(?P<n>\d+) review',
        html)}
    review_changes = {i: (site_counts.get(i), n) for i, n in reviews.items()
                      if site_counts.get(i) != n}
    print("\nPeer review: site total %d → ORCID total %d" % (sum(site_counts.values()), sum(reviews.values())))
    for issn, (old, new) in sorted(review_changes.items()):
        print("  %-10s %s → %d   %s" % (issn, old, new, JOURNALS.get(issn, ("?",))[0]))
    if not review_changes:
        print("  (in sync)")

    # 2. missing DOI/handle links ---------------------------------------------
    link_adds = []
    unmatched = []
    queued = {}  # pid → label already queued in this run (ORCID keeps duplicate records)
    for w in sorted(works, key=lambda x: 0 if "doi" in x["ids"] else 1):
        pid = match_work(w["title"], cards)
        if not pid:
            unmatched.append(w)
            continue
        label, url = best_link(w)
        if not url:
            continue
        if pid in queued:  # one identifier per card per run, DOI first
            continue
        have = cards[pid]["links"]
        if url in have:
            continue
        # a DOI already present in another form counts as covered
        if label == "DOI" and any("doi.org" in h for h in have):
            continue
        if label == "ARPI" and any("arpi.unipi.it" in h for h in have):
            continue
        # don't add an ARPI handle to a card that already links the publisher/preprint
        if label != "DOI" and have:
            continue
        queued[pid] = label
        link_adds.append((pid, label, url, w["title"]))

    print("\nIdentifier links to add: %d" % len(link_adds))
    for pid, label, url, title in link_adds:
        print("  %-8s %-6s %s" % (pid, label, url))

    # 3. works on ORCID but not on the site (and vice versa) -------------------
    if unmatched:
        print("\nON ORCID BUT NOT ON THE SITE (%d) — add these by hand:" % len(unmatched))
        for w in unmatched:
            label, url = best_link(w)
            print("  · %s (%s, %s)" % (w["title"], w["year"], w["type"]))
            print("    %s %s" % (label or "-", url or "-"))
        problems.append("%d ORCID work(s) not on the site" % len(unmatched))

    matched_ids = {match_work(w["title"], cards) for w in works}
    orphans = [pid for pid in cards if pid not in matched_ids]
    if orphans:
        print("\nON THE SITE BUT NOT ON ORCID (%d): %s" % (len(orphans), ", ".join(sorted(orphans))))
        print("  (fine for preprints ORCID doesn't list; otherwise add them to ORCID)")

    # ── apply ────────────────────────────────────────────────────────────────
    if not args.apply:
        print("\nreport only — pass --apply to write the review counts and identifier links")
        return 2 if problems else 0

    changed = []

    # Every rewrite below *sets* the ORCID value rather than replacing a known old one, so the
    # step is idempotent and a partially-applied earlier run still converges.
    total, journals = sum(reviews.values()), len(reviews)
    before_review_state = html

    def plural(n):
        return "%d review%s" % (n, "" if n == 1 else "s")

    for issn, new in reviews.items():
        html = re.sub(
            r'(ISSN %s</span></span><span class="rv-count">)\d+ reviews?' % re.escape(issn),
            lambda m, n=new: m.group(1) + plural(n), html)
        if issn in JOURNALS:
            html = re.sub(
                r'("issn": "%s",.*?"description": ")\d+ reviews?( \(\d{4}\)")' % re.escape(issn),
                lambda m, n=new: m.group(1) + plural(n) + m.group(2), html)

    html = re.sub(r'(<div><span class="metric-num">)\d+(</span><span class="metric-label">Reviews)',
                  lambda m: "%s%d%s" % (m.group(1), total, m.group(2)), html)
    html = re.sub(r'\d+ reviews recorded on ORCID', "%d reviews recorded on ORCID" % total, html)
    html = re.sub(r'\d+ reviews for \d+ (international )?journals',
                  lambda m: "%d reviews for %d %sjournals" % (total, journals, m.group(1) or ""), html)
    html = re.sub(r'\d+ peer reviews for \d+ international journals',
                  "%d peer reviews for %d international journals" % (total, journals), html)
    html = re.sub(r'>\d+ reviews · \d+ journals<', ">%d reviews · %d journals<" % (total, journals), html)
    html = re.sub(r'\(\d+ reviews in \d{4}\)',
                  lambda m: "(%d reviews in 2026)" % total, html)
    html = re.sub(r'("peerReviewCount", "value": )\d+',
                  lambda m: "%s%d" % (m.group(1), total), html)
    html = re.sub(r'("reviewedJournalCount", "value": )\d+',
                  lambda m: "%s%d" % (m.group(1), journals), html)

    # llms.txt and readme.md carry the same figures in prose and in a per-journal table
    for path in ("llms.txt", "readme.md"):
        t = before = read(path)
        t = re.sub(r'\d+ reviews recorded on ORCID', "%d reviews recorded on ORCID" % total, t)
        t = re.sub(r'\d+ reviews for \d+ (international )?journals',
                   lambda m: "%d reviews for %d %sjournals" % (total, journals, m.group(1) or ""), t)
        t = re.sub(r'## Peer Review \(\d+ reviews', "## Peer Review (%d reviews" % total, t)
        t = re.sub(r'"reviews": \d+, "journals": \d+',
                   '"reviews": %d, "journals": %d' % (total, journals), t)
        for issn, new in reviews.items():
            t = re.sub(r'(\| %s \| )\d+( \|)' % re.escape(issn),
                       lambda m, n=new: "%s%d%s" % (m.group(1), n, m.group(2)), t)
        if t != before:
            write(path, t)
            changed.append("%s peer-review figures" % path)

    # the profile.json generator holds the same table
    gen = before = read("tools/build-profile.ps1")
    gen = re.sub(r'(reviews  = )\d+', lambda m: "%s%d" % (m.group(1), total), gen)
    gen = re.sub(r'(journals = )\d+', lambda m: "%s%d" % (m.group(1), journals), gen)
    for issn, new in reviews.items():
        gen = re.sub(r'(issn = "%s"; reviews = )\d+' % re.escape(issn),
                     lambda m, n=new: "%s%d" % (m.group(1), n), gen)
    if gen != before:
        write("tools/build-profile.ps1", gen)
        changed.append("build-profile.ps1 peer-review table")

    if html != before_review_state:
        changed.append("index.html peer review → %d reviews / %d journals" % (total, journals))

    if link_adds:
        for pid, label, url, _title in link_adds:
            m = re.search(r'(?s)(<article class="pub-card"[^>]*id="%s"[^>]*>)(.*?)(</article>)'
                          % re.escape(pid), html)
            card = m.group(2)
            anchor = '<a href="%s" target="_blank" rel="noopener">%s ↗</a>' % (url, label)
            if '<div class="pub-links">' in card:
                new_card = card.replace('<div class="pub-links">',
                                        '<div class="pub-links">' + anchor, 1)
            else:
                indent = re.search(r'\n(\s*)<div class="pub-authors">', card).group(1)
                new_card = re.sub(r'(?s)(<div class="pub-authors">.*?</div>)',
                                  lambda mm: '%s\n%s<div class="pub-links">%s</div>'
                                             % (mm.group(1), indent, anchor),
                                  card, count=1)
            html = html[:m.start(2)] + new_card + html[m.end(2):]

            # mirror it into the JSON-LD entry for the same publication
            ld = re.search(r'(?s)("@id": "https://ilsamaritano\.github\.io/#%s",\n)(\s*)'
                           % re.escape(pid), html)
            if ld and ('"%s"' % url) not in html[ld.start():ld.start() + 2000]:
                prop = ('"identifier": { "@type": "PropertyValue", "propertyID": "%s", "url": "%s" },\n%s'
                        % (label, url, ld.group(2)))
                html = html[:ld.end()] + prop + html[ld.end():]
        changed.append("%d identifier link(s) added" % len(link_adds))

    if args.as_of:
        html = re.sub(r"synced \d{4}-\d{2}-\d{2}", "synced " + args.as_of, html)
        changed.append("sync date → " + args.as_of)

    write("index.html", html)

    print("\napplied: " + ("; ".join(changed) if changed else "nothing to do"))
    if problems:
        print("ACTION NEEDED: " + "; ".join(problems))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
