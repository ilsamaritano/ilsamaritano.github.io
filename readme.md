# ilsamaritano.github.io

> Personal academic portfolio of **Vincenzo Sammartino** — PhD Candidate in Artificial Intelligence, Università di Pisa · Visiting Researcher (VSRP Intern), King Abdullah University of Science and Technology (KAUST).

[![Live](https://img.shields.io/badge/Live-ilsamaritano.github.io-00e5ff?style=flat-square&logo=github)](https://ilsamaritano.github.io)
[![License](https://img.shields.io/badge/License-MIT-7c3aed?style=flat-square)](LICENSE)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0002--4632--1179-a6ce39?style=flat-square&logo=orcid)](https://orcid.org/0009-0002-4632-1179)
[![Citations](https://img.shields.io/badge/Citations-37-10b981?style=flat-square)](https://scholar.google.com/citations?user=lQig7SEAAAAJ)
[![H-Index](https://img.shields.io/badge/H--Index-4-10b981?style=flat-square)](https://scholar.google.com/citations?user=lQig7SEAAAAJ)

---

## Overview

Static single-page academic portfolio deployed via **GitHub Pages**, aggregating bibliometric indicators, research activities, institutional affiliations, and technical competencies into a single responsive interface. The visual design adheres to a terminal-inspired aesthetic commensurate with the research domains of cybersecurity and systems engineering.

The implementation is intentionally dependency-free at the deployment level — no build pipeline, no module bundler, no framework runtime — constituting a single self-contained `index.html` document with embedded CSS and vanilla JavaScript. This architectural constraint ensures reproducible deployment across arbitrary hosting environments with zero configuration overhead.

---

## Research Profile

| Field | Detail |
|---|---|
| **Primary Affiliation** | National PhD Programme in Artificial Intelligence, Università di Pisa |
| **Visiting Position** | VSRP Intern, King Abdullah University of Science and Technology (KAUST) · Thuwal, Saudi Arabia |
| **Supervisors** | Prof. Fabrizio Baiardi (UniPi) · Prof. Salvatore Ruggieri (UniPi) · Prof. Roberto Di Pietro (KAUST) |
| **Research Areas** | Security Twin · Digital Twin Architectures · Cyber-Physical Systems Resilience · UAV Swarm Security · TinyML / Edge AI · Byzantine Fault Tolerance · GDPR-compliant Distributed Systems · NLP |
| **Total Citations** | 37 |
| **H-Index** | 4 |
| **Publications** | 23 (IEEE · Springer · CRC/Taylor & Francis · peer-reviewed journals) |

---

## Repository Structure

```
ilsamaritano.github.io/
│
├── index.html          # Single-page application — complete site source
├── robots.txt          # Crawler directives (search engines + AI agents)
├── sitemap.xml         # URL manifest for search engine discovery
├── llms.txt            # LLM-readable identity and research summary (llmstxt.org)
├── README.md           # This document
└── LICENSE             # MIT License
```

> **Architectural note.** All stylesheets, scripts, and markup are co-located within `index.html`. This design choice prioritises deployment atomicity and eliminates dependency on asset-loading pipelines, at the cost of modularity. For projects requiring component reuse or multi-page routing, a framework-based approach would be architecturally preferable.

---

## Technical Implementation

### Frontend Architecture

The site is implemented as a **static HTML5 document** with no external JavaScript dependencies. All interactive and visual behaviour is driven by three complementary mechanisms:

**CSS Custom Properties** provide a centralised design-token system (`--accent`, `--bg`, `--surface`, `--glow`, etc.), enabling coherent theming across the entire document with O(1) propagation complexity on token modification. All motion effects — glitch displacement, scan-line traversal, orbital rotation, cursor ring interpolation — are implemented via `@keyframes` and CSS transitions, deliberately avoiding JavaScript-driven repaints on the main thread wherever the animation model permits.

**Vanilla JavaScript** governs behaviours requiring dynamic state: custom cursor kinematics with cubic-bezier ring interpolation, a neural-network canvas renderer, a typed-text finite-state automaton, scroll-triggered `IntersectionObserver`-based reveal sequences, and a publication filter state machine keyed on `data-type` attributes.

**HTML5 Semantic Markup** with embedded Schema.org JSON-LD structured data exposes the site's informational content to search engine crawlers and AI retrieval systems in a machine-interpretable form, independently of JavaScript execution.

### Component Reference

| Component | Implementation Detail |
|---|---|
| Neural background | HTML5 Canvas 2D — 70-node proximity graph; edges rendered at opacity proportional to inverse inter-node distance (threshold: 130 px) |
| Custom cursor | Dual-layer architecture (12 px filled point + 40 px hollow ring) with `mix-blend-mode: screen`; ring position interpolated via `requestAnimationFrame` at 0.12 lerp factor |
| Typed text | Five-state FSA cycling across research-descriptor phrases; variable-delay character emission (60 ms write / 40 ms erase) with 2 s hold at phrase completion |
| Publication filter | DOM traversal over `.pub-card` elements with `data-type` attribute matching; O(n) pass per filter event with `display` toggling |
| Scroll reveals | `IntersectionObserver` (threshold 0.1) toggling `.visible` class; CSS `opacity` + `transform` transitions handle the visual interpolation |
| Counter animation | Linear interpolation over 1500 ms via `setInterval` at ≈60 fps, triggered on first viewport intersection of the metrics section |

### Performance Characteristics

- Zero JavaScript framework overhead. Time-to-Interactive is bounded by font loading latency (Google Fonts: Syne, DM Mono, Space Mono), which is mitigated via `<link rel="preconnect">` and `dns-prefetch` directives.
- Canvas animation loop runs on `requestAnimationFrame`; node count (n = 70) is empirically calibrated to sustain ≥60 fps on mid-range hardware.
- All CSS animations operate exclusively on `transform` and `opacity` properties, ensuring GPU-composited rendering without triggering layout reflow or paint invalidation.

---

## SEO and AI Discoverability

The repository is instrumented for both conventional search engine indexing and AI-assisted retrieval, addressing the distinct requirements of each crawling paradigm:

**Structured Data (JSON-LD).** Schema.org entities of type `Person`, `ProfilePage`, `ScholarlyArticle`, and `ResearchProject` are embedded in the document `<head>`, enabling Google Knowledge Graph integration, Google Scholar entity resolution, and structured extraction by LLM-based retrieval systems (Perplexity, ChatGPT Web, Claude Web).

**Crawler Directives.** `robots.txt` includes explicit `Allow` directives for `GPTBot`, `ClaudeBot`, `anthropic-ai`, and `PerplexityBot`, ensuring that AI indexing agents are not inadvertently excluded by default crawler policies.

**LLM-readable Summary.** `llms.txt` (per the [llmstxt.org](https://llmstxt.org) specification) provides a structured, plain-text synopsis of identity, affiliations, and research content, directly consumable by language models without HTML parsing.

**Identity Graph.** `rel="me"` link annotations and `sameAs` JSON-LD properties establish verifiable co-reference between this domain and external academic profiles (ORCID, Google Scholar, LinkedIn, GitHub), supporting entity disambiguation in search engine knowledge graphs.

---

## Deployment

The repository is configured for direct **GitHub Pages** deployment from the `main` branch root. No build step, transpilation, or asset compilation is required.

```bash
# Clone the repository
git clone https://github.com/ilsamaritano/ilsamaritano.github.io.git
cd ilsamaritano.github.io

# Local preview (no development server required for purely static assets)
open index.html

# Deployment: push to main branch — GitHub Pages CI/CD handles publication
git add .
git commit -m "update: <scope> — <description>"
git push origin main
```

The canonical live endpoint is: **[https://ilsamaritano.github.io](https://ilsamaritano.github.io)**

---

## Selected Publications

A representative, non-exhaustive selection of contributions ordered by recency. The complete bibliographic record is available via [Google Scholar](https://scholar.google.com/citations?user=lQig7SEAAAAJ) and [ORCID 0009-0002-4632-1179](https://orcid.org/0009-0002-4632-1179).

**2026**
- *From Digital Twins to AI Agents: A Synthetic Data Paradigm for Next-Generation Cybersecurity* — CRC / Taylor & Francis (Book Chapter)
- *Evaluating Adversary Strategies Through a Security Twin* — IEEE PerCom Workshops 2026
- *Quantifying Resilience of Cyber-Physical Systems to Zero-Day Threats* — ESREL 2026

**2025**
- *AI-enabled Cybersecurity using Synthetic Data* — **IEEE PerCom 2025**, Washington DC · 5 citations
- *A Security Twin to Defeat Intrusions in Cyber Physical Systems* — ESREL / SRA-E 2025 · 4 citations
- *A Framework for Proactive Cyber-Resilience: Non-intrusive Modeling for Autonomous Defense* — DS-RT 2025 · 3 citations

**2024**
- *A Comparative Study of Machine Learning Models for Hate Speech and Stereotype Detection in Italian Texts* — IJCAST · 6 citations
- *Database Decomposition to Satisfy the Least Privilege Principle in Healthcare* — ARIS2 2024 · 2 citations

---

## Contact and Academic Profiles

| Channel | Reference |
|---|---|
| **Email** | [vincesammartino@gmail.com](mailto:vincesammartino@gmail.com) |
| **ORCID** | [0009-0002-4632-1179](https://orcid.org/0009-0002-4632-1179) |
| **Google Scholar** | [scholar.google.com/citations?user=lQig7SEAAAAJ](https://scholar.google.com/citations?user=lQig7SEAAAAJ) |
| **LinkedIn** | [vincenzo-sammartino-0339191a1](https://www.linkedin.com/in/vincenzo-sammartino-0339191a1) |
| **GitHub** | [@ilsamaritano](https://github.com/ilsamaritano) |

---

## License

This repository is released under the **MIT License**. Academic content — including the publications list, research descriptions, and biographical data — remains the intellectual property of Vincenzo Sammartino. Reuse of design patterns and implementation code is permitted with attribution.

---

<p align="center">
  <sub>PhD in Artificial Intelligence · Università di Pisa · KAUST Visiting Researcher · 2026</sub>
</p>
