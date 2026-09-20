# ilsamaritano.github.io

> Personal academic portfolio of **Vincenzo Sammartino** — PhD Candidate in Artificial Intelligence, Università di Pisa · Visiting PhD Student (VSRP Intern, Jan–Jun 2026), King Abdullah University of Science and Technology (KAUST).

[![Live](https://img.shields.io/badge/Live-ilsamaritano.github.io-00e5ff?style=flat-square&logo=github)](https://ilsamaritano.github.io)
[![License](https://img.shields.io/badge/License-MIT-7c3aed?style=flat-square)](LICENSE)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0002--4632--1179-a6ce39?style=flat-square&logo=orcid)](https://orcid.org/0009-0002-4632-1179)
[![Citations](https://img.shields.io/badge/Citations-161-10b981?style=flat-square)](https://scholar.google.com/citations?user=lQig7SEAAAAJ)
[![H-Index](https://img.shields.io/badge/H--Index-8-10b981?style=flat-square)](https://scholar.google.com/citations?user=lQig7SEAAAAJ)
[![i10-Index](https://img.shields.io/badge/i10--Index-7-10b981?style=flat-square)](https://scholar.google.com/citations?user=lQig7SEAAAAJ)

---

## Overview

Static single-page academic portfolio deployed via **GitHub Pages**, aggregating bibliometric indicators, research activities, institutional affiliations, and technical competencies into a single responsive interface. The visual design adheres to a terminal-inspired aesthetic commensurate with the research domains of cybersecurity and systems engineering.

The implementation is intentionally dependency-free at the deployment level — no build pipeline, no module bundler, no framework runtime — constituting a single self-contained `index.html` document with embedded CSS and vanilla JavaScript.

---

## Research Profile

| Field | Detail |
|---|---|
| **Primary Affiliation** | National PhD Programme in Artificial Intelligence, [Università di Pisa](https://people.unipi.it/vincenzo_sammartino/) |
| **Visiting Position** | VSRP Intern, KAUST · Thuwal, Saudi Arabia (Jan–Jun 2026) |
| **Supervisors** | Prof. Fabrizio Baiardi (UniPi) · Prof. Salvatore Ruggieri (UniPi) · Prof. Roberto Di Pietro (KAUST) |
| **Research Areas** | Security Twin · Digital Twin Architectures · Cyber-Physical Systems Resilience · Quantum ML & Post-Quantum Security · 6G Edge Digital Twins · UAV Swarm Security · TinyML / Edge AI · NLP |
| **Total Citations** | 161 (Google Scholar, 20 September 2026) |
| **H-Index / i10-Index** | 8 / 7 |
| **Publications** | 38 — 36 indexed by Google Scholar (IEEE · Springer · Elsevier · CRC/Taylor & Francis · arXiv / SSRN preprints) |
| **Peer Review** | 39 reviews for 20 journals (2026, ORCID) — incl. IEEE TNNLS, ACM Computing Surveys, Scientific Reports, Computers & Security, FGCS |
| **Research Grant** | *Smart Security for Connected Cyber-Physical Systems: Paradigms, Threats and AI-based Defenses* — Università di Pisa (2026) |
| **Identifiers** | ORCID 0009-0002-4632-1179 · Scopus 59166600100 · SciProfiles 3668849 |

---

## Repository Structure

```
ilsamaritano.github.io/
│
├── index.html          # Single-page application — complete site source
├── assets/
│   ├── photo.jpg       # 800×800 optimised portrait (hero + JSON-LD image)
│   └── og-cover.jpg    # 1200×630 social preview card (Open Graph / X)
├── foto_forum_ict.jpg  # Original full-resolution portrait (fallback)
├── robots.txt          # Crawler directives (search engines + AI agents)
├── sitemap.xml         # URL manifest for search engine discovery
├── llms.txt            # LLM-readable identity and research summary (llmstxt.org)
├── profile.json        # Complete machine-readable record (generated from index.html)
├── tools/
│   ├── sync-orcid.py         # ORCID   → peer reviews, DOIs, work list
│   ├── sync-scholar.py       # Scholar → citations, h-index, i10-index, per-paper counts
│   ├── build-profile.ps1     # index.html → profile.json
│   ├── build-llms-pubs.py    # profile.json → llms.txt publication block
│   └── validate.py           # cross-file consistency gate
├── .github/workflows/
│   ├── sync-profile.yml      # weekly ORCID + Scholar sync, commits only if valid
│   └── validate.yml          # runs validate.py on every push and pull request
├── .well-known/security.txt
└── readme.md           # This document
```

---

## Technical Implementation

### Frontend Architecture

The site is a **static HTML5 document** with no external JavaScript dependencies.

**CSS Custom Properties** provide a centralised design-token system (`--accent`, `--bg`, `--surface`, `--glow`, etc.). Motion effects — glitch displacement, scan-line traversal, orbital rotation — are implemented via `@keyframes` and CSS transitions and are disabled under `prefers-reduced-motion`.

**Vanilla JavaScript** governs behaviours requiring dynamic state: custom cursor (fine pointers only), neural-network canvas background (paused in background tabs), typed-text hero, `IntersectionObserver` scroll reveals, animated Scholar metrics, active-section navigation, and the publications explorer (type filter, full-text search, sort by year or citations).

**Progressive enhancement.** All content is present in the static HTML; reveal animations are gated behind an `html.js` class so the page is fully readable without JavaScript.

### Component Reference

| Component | Implementation Detail |
|---|---|
| Neural background | HTML5 Canvas 2D — 70-node proximity graph (35 on small screens); skipped under reduced motion, paused when the tab is hidden |
| Custom cursor | Dual-layer cursor, enabled only for `(hover: hover) and (pointer: fine)` devices |
| Scholar impact panel | Citations / h-index / i10-index / publications counters, citations-per-year bar chart (with screen-reader table), and top-cited works |
| Publications explorer | Type filter with counts, multi-term search over title/venue/authors, sort by newest or most cited, live result count (`aria-live`) |
| Theses | Supervised theses with EN/IT language toggle (persisted in `localStorage`) |
| Accessibility | Skip link, `:focus-visible` outlines, semantic `<main>`/`<nav>`, accessible mobile menu (Escape to close, `aria-expanded`) |

---

## SEO and AI Discoverability

**Structured Data (JSON-LD).** Schema.org `Person`, `ProfilePage`, `ResearchProject`, a peer-review `ItemList`, and an `ItemList` of `ScholarlyArticle` entries — one per publication, with arXiv / SSRN / DOI / Zenodo identifiers where available and an `interactionStatistic` (`CiteAction`) citation counter carrying its `observationDate`. The `Person` node additionally exposes citations, h-index, i10-index, work count and review counts as dated `PropertyValue` entries, so an agent can read the bibliometrics without scraping the rendered page.

**Machine-readable Profile.** `profile.json` is the canonical structured record: identity, persistent identifiers, metrics with observation date and citations-per-year, all 38 publications (id, title, authors, author position, venue, type, year, citation count, persistent links), research themes cross-referenced to publication ids, the peer-review breakdown, positions, grants and projects. It is *generated from* `index.html` (see **Staying in sync** below), so the page and the JSON cannot drift apart. Advertised via `<link rel="alternate" type="application/json">`, `sitemap.xml`, `robots.txt` and `llms.txt`.

**Crawler Directives.** `robots.txt` is allow-by-default and grants explicit `Allow` directives to four groups: generalist search engines (`Googlebot` and its variants, `Bingbot`, `Slurp`, `DuckDuckBot`, `YandexBot`, `Baiduspider`, `Applebot`, `SeznamBot`, `Qwantify`, `MojeekBot`), academic indexers and archives (`SemanticScholarBot`, `CiteSeerXBot`, `archive.org_bot`, `ia_archiver`), AI indexing crawlers (`GPTBot`, `ClaudeBot`, `anthropic-ai`, `Google-Extended`, `PerplexityBot`, `Applebot-Extended`, `CCBot`, `Meta-ExternalAgent`, `cohere-ai`, `Amazonbot`, `Bytespider`) and on-demand assistant fetchers (`OAI-SearchBot`, `ChatGPT-User`, `Claude-User`, `Claude-SearchBot`, `Perplexity-User`, `DuckAssistBot`, `MistralAI-User`, `YouBot`). Only four commercial SEO/backlink scrapers are disallowed.

Because a crawler that matches a named group ignores the `User-agent: *` group entirely, the named `Allow: /` entries also guarantee that no future restriction added to the default group can accidentally shut out a search or academic crawler. **Googlebot in particular must stay unrestricted: Google Scholar has no crawler of its own and indexes through Googlebot**, reading the `<meta name="citation_*">` tags on the crawled page.

**LLM-readable Summary.** `llms.txt` (per the [llmstxt.org](https://llmstxt.org) specification) opens with a machine-readable endpoint index and a *Quick answers* block, then lists identity, metrics and the complete publication record grouped by year, each entry tagged with its output type and citation count.

**Identity Graph.** `rel="me"` link annotations and `sameAs` JSON-LD properties link this domain to ORCID, Google Scholar, LinkedIn and GitHub.

**Social previews.** `assets/og-cover.jpg` provides a 1200×630 card for LinkedIn, WhatsApp, Slack and X.

---

## Deployment

The repository is configured for direct **GitHub Pages** deployment from the `main` branch root. No build step is required.

```bash
git clone https://github.com/ilsamaritano/ilsamaritano.github.io.git
cd ilsamaritano.github.io
open index.html          # local preview

git add .
git commit -m "update: <scope> — <description>"
git push origin main
```

---

## Staying in sync with ORCID and Google Scholar

`index.html` is the single source of truth for the publication record; `profile.json` and the publication block of `llms.txt` are generated from it. Two sources feed the page, and each has its own tool:

| Source | Tool | What it owns |
|---|---|---|
| **ORCID** (public API, no credentials) | `tools/sync-orcid.py` | Peer-review counts per journal, DOIs and repository handles, the work list |
| **Google Scholar** | `tools/sync-scholar.py` | Total citations, h-index, i10-index, citations per year, per-publication counts |

### Automatic — weekly workflow

`.github/workflows/sync-profile.yml` runs every Monday at 05:30 UTC (and on demand from the Actions tab). It syncs from ORCID, then from Scholar, regenerates `profile.json` and `llms.txt`, runs `tools/validate.py`, and **commits only if validation passes** — a half-applied update can never ship. The run's step summary shows exactly what each source reported.

Two things it deliberately does *not* do on its own:

- **Adding a publication.** When a work exists on ORCID or Scholar but not on the page, the tools report it and exit with code 2; the workflow opens (or comments on) an issue with the details and a ready-made checklist, because the venue wording, output type and position in the list are editorial decisions.
- **Scraping Scholar.** Google Scholar has no API and blocks CI address ranges. The Scholar step therefore needs a `SERPAPI_KEY` repository secret; without it the step logs that it is skipping and the citation figures are left untouched. Everything ORCID-driven keeps working regardless.

### Manual — same tools, no services

```bash
python tools/sync-orcid.py                       # report what ORCID has that the site lacks
python tools/sync-orcid.py --apply --as-of 2026-09-20

# Scholar, without any API key: put the numbers in a small JSON file and apply them
python tools/sync-scholar.py --from-json scholar.json --report
python tools/sync-scholar.py --from-json scholar.json

powershell -File tools/build-profile.ps1 -AsOf 2026-09-20   # index.html → profile.json
python tools/build-llms-pubs.py                             # profile.json → llms.txt pubs block
python tools/validate.py                                    # must print OK before committing
```

The shape `--from-json` expects is documented at the top of `tools/sync-scholar.py`; `articles` may list any subset of the publications, and a card whose title is not listed keeps its current count. Titles are matched loosely (case, punctuation and subtitles are ignored) and never guessed at: an unmatched title is reported, not applied.

`sync-scholar.py` updates the metric cards, the citations-per-year chart and its screen-reader table, the per-card citation counts and their `interactionStatistic` counters, the most-cited panel, the card ordering, every prose figure, and the date stamps in `index.html`, `llms.txt`, `readme.md`, `sitemap.xml` and the generator's defaults.

### Why it is safe to run unattended

`tools/validate.py` cross-checks everything that could drift and exits non-zero on any mismatch:

- HTML tag balance, and that every JSON-LD block parses;
- publication cards ↔ JSON-LD entries: same set, same titles, same citation counts, `numberOfItems` correct;
- filter-toolbar counts and the "Showing *n* of *n*" line against the actual cards; `data-order` a proper `0..n-1` permutation;
- citations, h-index and i10-index consistent across `index.html` (including meta descriptions and social cards), `profile.json`, `llms.txt` and `readme.md`;
- `profile.json` and the `llms.txt` publication block not stale with respect to the page;
- one observation date everywhere, `sitemap.xml` included, and every URL it lists existing in the repository;
- peer-review totals equal to the sum of the per-journal rows, in all three files;
- every local `src`/`href` in the page resolving to a file that exists.

`validate.yml` runs the same checks on every push and pull request, and additionally re-runs both generators to prove the committed derived files match the page.

The generators are strict too: `build-profile.ps1` refuses to write unless the number of publication cards it parses equals the count in the page's own filter toolbar, and `build-llms-pubs.py` refuses unless the `PUBS:START` / `PUBS:END` markers appear exactly once. Both are idempotent — re-running them on an unchanged page reproduces byte-identical output. Prose sections of `llms.txt` (identity header, quick answers, themes, affiliations) are maintained by hand.

> `tools/build-profile.ps1` must stay saved as **UTF-8 with BOM**: Windows PowerShell 5.1 reads a BOM-less script as ANSI and mangles its em dashes and accents. The Python tools handle this automatically when they rewrite it.

The canonical live endpoint is: **[https://ilsamaritano.github.io](https://ilsamaritano.github.io)**

---

## Selected Publications

Most-cited works (Google Scholar, 20 September 2026). The complete record is on the website, in [`profile.json`](profile.json) and [`llms.txt`](llms.txt), on [Google Scholar](https://scholar.google.com/citations?user=lQig7SEAAAAJ) and [ORCID](https://orcid.org/0009-0002-4632-1179).

- *AI-Enabled Cybersecurity Using Synthetic Data* — **IEEE PerCom 2025** · 17 citations
- *Anticipating Disasters through a Security Twin* — Dynamics of Disasters: Hybrid Threats, Springer, 2026 · 14 citations
- *A Security Twin to Defeat Intrusions in Cyber Physical Systems* — ESREL SRA-E 2025 · 14 citations
- *A Framework for Proactive Cyber-Resilience: Non-Intrusive Modeling for Autonomous Defense* — DS-RT 2025 · 13 citations
- *NotLine: A Non-Intrusive Automated Platform to Build a Digital Twin* — DS-RT 2025 · 11 citations
- *A Quantitative Framework for the Validation of Twin-Based Cyber Defense* — Procedia Computer Science 274, 2025 · 11 citations
- *Simulation-Powered Cybersecurity: Real-Time Risk Assessment via Non-Intrusive Security Twin* — The Journal of Supercomputing, 2026 · 10 citations

**Recent (2026)**
- *Model-Driven Security Analysis of SD-Access Fabrics Using Digital Twins* — Future Generation Computer Systems
- *Hybrid Quantum Graph Neural Networks for Robust Botnet Detection in Modern IoT Ecosystems* — Future Generation Computer Systems
- *QUASAR: A Quantum-Classical Neural Network for SAR Satellite Physical-Layer Authentication* — arXiv:2608.20240 (with N. Denis, R. Di Pietro)
- *HAVE: Host Active Verification Engine for Closing the Contextual Reality Gap in Security Digital Twins* — arXiv:2606.06968

---

## Contact and Academic Profiles

| Channel | Reference |
|---|---|
| **Email** | [vincesammartino@gmail.com](mailto:vincesammartino@gmail.com) |
| **University of Pisa** | [people.unipi.it/vincenzo_sammartino](https://people.unipi.it/vincenzo_sammartino/) — institutional profile |
| **ORCID** | [0009-0002-4632-1179](https://orcid.org/0009-0002-4632-1179) |
| **Google Scholar** | [scholar.google.com/citations?user=lQig7SEAAAAJ](https://scholar.google.com/citations?user=lQig7SEAAAAJ) |
| **LinkedIn** | [vincenzo-sammartino-0339191a1](https://www.linkedin.com/in/vincenzo-sammartino-0339191a1) |
| **GitHub** | [@ilsamaritano](https://github.com/ilsamaritano) |
| **Web Studio** | [SV WebStudio](https://ilsamaritano.github.io/sv-webstudio/) — custom websites, e-commerce, restyling, SEO · Instagram [@sv_webstudio](https://www.instagram.com/sv_webstudio/) |

---

## License

This repository is released under the **MIT License**. Academic content — including the publications list, research descriptions, and biographical data — remains the intellectual property of Vincenzo Sammartino. Reuse of design patterns and implementation code is permitted with attribution.

---

<p align="center">
  <sub>PhD in Artificial Intelligence · Università di Pisa · KAUST Visiting Researcher · 2026</sub>
</p>
