# -*- coding: utf-8 -*-
"""Consistency checks for the site. Run it after any edit, automated or by hand.

    python tools/validate.py

Exits 0 when everything agrees, 1 with a list of problems otherwise. This is the gate the
sync workflow runs before it is allowed to commit, so nothing half-updated ever ships.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
problems = []


def bad(msg):
    problems.append(msg)


def read(name):
    return io.open(os.path.join(ROOT, name), encoding="utf-8").read()


# ── HTML well-formedness ──────────────────────────────────────────────────────

class Balance(HTMLParser):
    VOID = {"meta", "link", "br", "img", "input", "hr", "source", "area", "base",
            "col", "embed", "param", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if not self.stack:
            bad("index.html: stray </%s> at line %d" % (tag, self.getpos()[0]))
            return
        if self.stack[-1][0] != tag:
            bad("index.html: </%s> at line %d closes <%s> opened at line %d"
                % (tag, self.getpos()[0], self.stack[-1][0], self.stack[-1][1]))
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == tag:
                    del self.stack[i:]
                    return
        else:
            self.stack.pop()


def main():
    html = read("index.html")

    p = Balance()
    p.feed(html)
    for tag, line in p.stack:
        bad("index.html: <%s> opened at line %d is never closed" % (tag, line))

    # ── JSON-LD ──────────────────────────────────────────────────────────────
    blocks = {}
    for m in re.finditer(r'(?s)<script type="application/ld\+json">(.*?)</script>', html):
        try:
            obj = json.loads(m.group(1))
        except ValueError as e:
            bad("index.html: JSON-LD block at offset %d does not parse: %s" % (m.start(), e))
            continue
        blocks.setdefault(obj.get("@type"), []).append(obj)
    for required in ("Person", "ProfilePage", "BreadcrumbList"):
        if required not in blocks:
            bad("index.html: no %s JSON-LD block" % required)

    # ── publication cards ────────────────────────────────────────────────────
    cards = []
    for m in re.finditer(
            r'(?s)<article class="pub-card" data-type="(?P<type>[^"]+)" data-year="(?P<year>\d+)"'
            r' data-cites="(?P<cites>\d+)" data-order="(?P<order>\d+)" id="(?P<id>pub-\d+)"[^>]*>'
            r'(?P<body>.*?)</article>', html):
        body = m.group("body")
        shown = re.search(r'<div class="pub-citations[^"]*">(\d+) citations?</div>', body)
        cards.append({
            "id": m.group("id"),
            "type": m.group("type"),
            "year": int(m.group("year")),
            "cites": int(m.group("cites")),
            "order": int(m.group("order")),
            "shown_cites": int(shown.group(1)) if shown else 0,
            "title": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", re.search(
                r'(?s)<h3 class="pub-title">(.*?)</h3>', body).group(1))).strip(),
        })
    if not cards:
        bad("index.html: no publication cards found — has the markup changed?")
        return report()

    ids = [c["id"] for c in cards]
    if len(set(ids)) != len(ids):
        bad("index.html: duplicate publication ids")

    # citation count shown in the card must match its data-cites
    for c in cards:
        if c["cites"] != c["shown_cites"]:
            bad("%s: data-cites=%d but the card reads %d citations"
                % (c["id"], c["cites"], c["shown_cites"]))

    # data-order must be a 0..n-1 permutation
    if sorted(c["order"] for c in cards) != list(range(len(cards))):
        bad("index.html: data-order values are not 0..%d" % (len(cards) - 1))

    # toolbar counts
    total_btn = re.search(r'data-filter="all"[^>]*>All <span class="count">(\d+)</span>', html)
    if not total_btn or int(total_btn.group(1)) != len(cards):
        bad("publications toolbar: 'All' says %s, there are %d cards"
            % (total_btn and total_btn.group(1), len(cards)))
    for kind in ("journal", "conference", "book", "preprint"):
        btn = re.search(r'data-filter="%s"[^>]*><span class="count">(\d+)</span>' % kind, html) or \
              re.search(r'data-filter="%s"[^>]*>[^<]*<span class="count">(\d+)</span>' % kind, html)
        actual = sum(1 for c in cards if c["type"] == kind)
        if not btn:
            bad("publications toolbar: no count button for '%s'" % kind)
        elif int(btn.group(1)) != actual:
            bad("publications toolbar: '%s' says %s, there are %d" % (kind, btn.group(1), actual))
    status = re.search(r'id="pub-status"[^>]*>Showing (\d+) of (\d+) publications', html)
    if not status or int(status.group(2)) != len(cards) or int(status.group(1)) != len(cards):
        bad("pub-status line does not say 'Showing %d of %d publications'" % (len(cards), len(cards)))

    # ── publication JSON-LD mirrors the cards ────────────────────────────────
    pub_list = None
    for lst in blocks.get("ItemList", []):
        if lst.get("@id", "").endswith("#publications"):
            pub_list = lst
    if pub_list is None:
        bad("index.html: no publications ItemList JSON-LD")
    else:
        items = pub_list["itemListElement"]
        if pub_list.get("numberOfItems") != len(cards):
            bad("publications ItemList: numberOfItems=%s, %d cards"
                % (pub_list.get("numberOfItems"), len(cards)))
        if len(items) != len(cards):
            bad("publications ItemList: %d entries, %d cards" % (len(items), len(cards)))
        ld = {}
        for it in items:
            item = it["item"]
            pid = item["@id"].rsplit("#", 1)[1]
            ld[pid] = item
        for c in cards:
            item = ld.get(c["id"])
            if item is None:
                bad("%s has no JSON-LD entry" % c["id"])
                continue
            if item.get("name", "").strip() != c["title"]:
                bad("%s: JSON-LD name and card title differ\n    card: %s\n    json: %s"
                    % (c["id"], c["title"], item.get("name")))
            stat = item.get("interactionStatistic") or {}
            if stat.get("userInteractionCount") != c["cites"]:
                bad("%s: JSON-LD citation counter=%s, card says %d"
                    % (c["id"], stat.get("userInteractionCount"), c["cites"]))
        for pid in ld:
            if pid not in ids:
                bad("JSON-LD entry %s has no matching card" % pid)

    # ── metrics agree across every file ──────────────────────────────────────
    profile = json.loads(read("profile.json"))
    llms = read("llms.txt")
    readme = read("readme.md")
    m = profile["metrics"]
    as_of = m["asOf"]

    metric_card = re.search(r'<span class="metric-num" data-count="(\d+)">(\d+)</span>', html)
    if not metric_card:
        bad("index.html: citations metric card not found")
    elif {int(metric_card.group(1)), int(metric_card.group(2))} != {m["citations"]}:
        bad("citations: metric card says %s/%s, profile.json says %d"
            % (metric_card.group(1), metric_card.group(2), m["citations"]))

    for label, key in (("h-index", "hIndex"), ("i10-index", "i10Index")):
        want = m[key]
        found = re.search(r'data-count="(\d+)">\d+</span>\s*<span class="metric-label">%s'
                          % re.escape(label), html)
        if found and int(found.group(1)) != want:
            bad("%s: page says %s, profile.json says %d" % (label, found.group(1), want))

    # any prose mention of the indices must quote the current value
    for name, text in (("index.html", html), ("llms.txt", llms), ("readme.md", readme)):
        for label, key in (("h-index", "hIndex"), ("i10-index", "i10Index")):
            stale = {int(v) for v in re.findall(r"%s (\d+)" % re.escape(label), text)} - {m[key]}
            if stale:
                bad("%s quotes %s %s, profile.json says %d"
                    % (name, label, "/".join(str(s) for s in sorted(stale)), m[key]))

    for name, text in (("llms.txt", llms), ("readme.md", readme)):
        if str(m["citations"]) not in text:
            bad("%s never mentions the current citation count (%d)" % (name, m["citations"]))
        if as_of not in text and as_of_human(as_of) not in text:
            bad("%s does not carry the observation date %s" % (name, as_of))

    if len(profile["publications"]) != len(cards):
        bad("profile.json lists %d publications, the page has %d"
            % (len(profile["publications"]), len(cards)))
    else:
        by_id = {p["id"]: p for p in profile["publications"]}
        for c in cards:
            p = by_id.get(c["id"])
            if p is None:
                bad("profile.json is missing %s — regenerate it" % c["id"])
            elif p["citations"] != c["cites"] or p["title"] != c["title"]:
                bad("profile.json is stale for %s — regenerate it" % c["id"])

    entries = len(re.findall(r"(?m)^- \*\*", llms[llms.index("<!-- PUBS:START -->"):
                                                   llms.index("<!-- PUBS:END -->")]))
    if entries != len(cards):
        bad("llms.txt publication block has %d entries, the page has %d — regenerate it"
            % (entries, len(cards)))

    # per-publication citation sum quoted in profile.json
    stated = re.search(r"citation counts in this file: (\d+)", m.get("note", ""))
    if stated and int(stated.group(1)) != sum(c["cites"] for c in cards):
        bad("profile.json note quotes a citation sum of %s, cards add up to %d"
            % (stated.group(1), sum(c["cites"] for c in cards)))

    # ── dates ────────────────────────────────────────────────────────────────
    if 'dateModified": "%s"' % as_of not in html:
        bad('index.html dateModified is not "%s"' % as_of)
    sitemap = read("sitemap.xml")
    for lastmod in set(re.findall(r"<lastmod>([\d-]+)</lastmod>", sitemap)):
        if lastmod != as_of:
            bad("sitemap.xml has <lastmod>%s</lastmod>, expected %s" % (lastmod, as_of))
    for loc in re.findall(r"<loc>https://ilsamaritano\.github\.io/([^<]*)</loc>", sitemap):
        if loc and not os.path.exists(os.path.join(ROOT, loc)):
            bad("sitemap.xml lists /%s, which does not exist in the repository" % loc)

    # ── peer review ──────────────────────────────────────────────────────────
    pr = profile["peerReview"]
    counted = sum(j["reviews"] for j in pr["detail"])
    if counted != pr["reviews"]:
        bad("profile.json peer review: total %d, per-journal rows add up to %d"
            % (pr["reviews"], counted))
    if len(pr["detail"]) != pr["journals"]:
        bad("profile.json peer review: %d journals declared, %d rows"
            % (pr["journals"], len(pr["detail"])))
    card_reviews = sum(int(n) for n in re.findall(r'class="rv-count">(\d+) reviews?', html))
    if card_reviews != pr["reviews"]:
        bad("index.html review cards add up to %d, profile.json says %d"
            % (card_reviews, pr["reviews"]))
    shown_total = re.search(r'<div><span class="metric-num">(\d+)</span>'
                            r'<span class="metric-label">Reviews', html)
    if shown_total and int(shown_total.group(1)) != pr["reviews"]:
        bad("index.html Reviews counter says %s, profile.json says %d"
            % (shown_total.group(1), pr["reviews"]))

    # ── referenced local files exist ─────────────────────────────────────────
    for ref in set(re.findall(r'(?:src|href)="((?!https?:|mailto:|#|//)[^"]+)"', html)):
        target = ref.split("?")[0].split("#")[0]
        if not target or target.endswith("/"):
            continue
        if not os.path.exists(os.path.join(ROOT, target)):
            bad("index.html references %s, which is not in the repository" % target)

    return report()


def as_of_human(iso):
    y, mo, d = iso.split("-")
    months = ["January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"]
    return "%d %s %s" % (int(d), months[int(mo) - 1], y)


def report():
    if problems:
        print("FAILED — %d problem(s):" % len(problems))
        for p in problems:
            print("  · " + p)
        return 1
    print("OK — page, JSON-LD, profile.json, llms.txt, readme, sitemap and peer-review "
          "figures all agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
