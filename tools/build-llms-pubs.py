# -*- coding: utf-8 -*-
"""Regenerate the <!-- PUBS:START -->...<!-- PUBS:END --> block of llms.txt from profile.json."""
import io, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
prof = json.load(io.open(os.path.join(ROOT, "profile.json"), encoding="utf-8"))
pubs = prof["publications"]
m = prof["metrics"]

LABEL = {
    "journal": "Journal",
    "conference": "Conference",
    "book": "Book chapter",
    "preprint": "Preprint",
}

def entry(p):
    lines = []
    lines.append("- **%s**" % p["title"])
    lines.append("  %s" % ", ".join(p["authors"]))
    year = p["year"]
    venue = "  *%s*" % p["venue"]
    venue += ", %s." % year if year else "."
    tags = [p.get("outputForm") or LABEL.get(p["type"], p["type"])]
    c = p["citations"]
    if c:
        tags.append("%d citation%s" % (c, "" if c == 1 else "s"))
    venue += " [%s]" % " · ".join(tags)
    lines.append(venue)
    for idf in p.get("identifiers", []):
        lines.append("  %s: %s" % (idf["label"], idf["url"]))
    return "\n".join(lines)

years = sorted({p["year"] for p in pubs if p["year"]}, reverse=True)
out = []
out.append(
    "## Publications (%d listed; the %d indexed by Google Scholar are cited %d times, "
    "h-index %d, i10-index %d — %s)\n"
    % (len(pubs), m["indexedWorks"], m["citations"], m["hIndex"], m["i10Index"], m["asOf"])
)
out.append(
    "Entries are grouped by year, then by citation count (descending). Each entry carries its output\n"
    "type and its Google Scholar citation count as of 2026-09-20. Canonical ids (`pub-N`) match\n"
    "profile.json and the page anchors at https://ilsamaritano.github.io/#pub-N.\n"
)
for y in years:
    group = sorted(
        [p for p in pubs if p["year"] == y],
        key=lambda p: (-p["citations"], p["title"]),
    )
    out.append("### %d\n" % y)
    out.append("\n\n".join(entry(p) for p in group) + "\n")

undated = sorted([p for p in pubs if not p["year"]], key=lambda p: (-p["citations"], p["title"]))
if undated:
    out.append("### Undated preprints\n")
    out.append("\n\n".join(entry(p) for p in undated) + "\n")

block = "<!-- PUBS:START -->\n" + "\n".join(out) + "<!-- PUBS:END -->"

path = os.path.join(ROOT, "llms.txt")
txt = io.open(path, encoding="utf-8").read()
new, n = re.subn(r"<!-- PUBS:START -->.*?<!-- PUBS:END -->", lambda _m: block, txt, flags=re.S)
assert n == 1, "marker block not found exactly once (%d)" % n
io.open(path, "w", encoding="utf-8", newline="\n").write(new)
print("rewrote PUBS block: %d entries, %d years + %d undated" % (len(pubs), len(years), len(undated)))
