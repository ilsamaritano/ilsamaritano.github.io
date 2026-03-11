# ilsamaritano.github.io

> Personal academic portfolio of **Vincenzo Sammartino** — PhD Candidate in Artificial Intelligence, Università di Pisa · Visiting Researcher, KAUST.

[![Live](https://img.shields.io/badge/Live-ilsamaritano.github.io-00e5ff?style=flat-square&logo=github)](https://ilsamaritano.github.io)
[![License](https://img.shields.io/badge/License-MIT-7c3aed?style=flat-square)](LICENSE)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0002--4632--1179-a6ce39?style=flat-square&logo=orcid)](https://orcid.org/0009-0002-4632-1179)
[![Citations](https://img.shields.io/badge/Citations-37-10b981?style=flat-square)](https://scholar.google.com)
[![H-Index](https://img.shields.io/badge/H--Index-4-10b981?style=flat-square)](https://scholar.google.com)

---

## Overview

Static single-page academic portfolio deployed via **GitHub Pages**. The site aggregates bibliometric indicators, research activities, institutional affiliations, and technical competencies into a single responsive interface, adhering to a dark, terminal-inspired aesthetic consistent with the domains of cybersecurity and systems engineering research.

The implementation is intentionally dependency-free at the deployment level — no build pipeline, no bundler, no framework runtime — consisting of a single self-contained `index.html` file with embedded CSS and vanilla JavaScript.

---

## Research Profile

| Field | Detail |
|---|---|
| **Primary Affiliation** | National PhD Programme in Artificial Intelligence, Università di Pisa |
| **Visiting Position** | VSRP Intern, King Abdullah University of Science and Technology (KAUST) |
| **Supervisors** | Prof. Fabrizio Baiardi (UniPi), Prof. Salvatore Ruggieri (UniPi), Prof. Roberto Di Pietro (KAUST) |
| **Research Areas** | Security Twin, Digital Twin, Cyber-Physical Systems, UAV Swarm Security, TinyML/Edge AI, GDPR-compliant Distributed Systems, NLP |
| **Total Citations** | 37 |
| **H-Index** | 4 |
| **Publications** | 23 |

---

## Repository Structure

```
ilsamaritano.github.io/
│
├── index.html          # Single-page application — complete site
├── README.md           # This document
└── LICENSE             # MIT License
```

> **Note on the single-file architecture.** All stylesheets, scripts, and markup are co-located within `index.html`. This design choice prioritises deployment simplicity and eliminates dependency on asset-loading pipelines, at the cost of modularity. For projects requiring component reuse or multi-page routing, a framework-based approach would be preferable.

---

## Technical Implementation

### Architecture

The site is implemented as a **static HTML5 document** with no external JavaScript dependencies. All visual behaviour is driven by:

- **CSS Custom Properties** — centralised design token system (`--accent`, `--bg`, `--surface`, etc.) enabling coherent theming across the entire document with O(1) modification complexity.
- **CSS Animations** — all motion effects (glitch, scan, orbit rotation, cursor ring interpolation) are implemented via `@keyframes` and CSS transitions, avoiding JavaScript repaints on the main thread where possible.
- **Vanilla JavaScript** — custom cursor kinematics, neural-network canvas renderer, typed-text automaton, scroll-triggered `IntersectionObserver` reveals, and publication filter state machine.

### Key Components

| Component | Implementation |
|---|---|
| Neural background | HTML5 Canvas 2D API — 70-node force graph with proximity-based edge rendering |
| Custom cursor | Dual-layer (point + ring) with CSS `mix-blend-mode: screen` and cubic-bezier ring interpolation |
| Typed text | Finite-state automaton cycling across 5 research-descriptor phrases |
| Publication filter | DOM-based show/hide keyed on `data-type` attributes; O(n) pass on filter event |
| Scroll reveals | `IntersectionObserver` (threshold 0.1) toggling `.visible` class; CSS handles the transition |
| Counter animation | Linear interpolation over 1500ms via `setInterval` at ~60fps |

### Performance Considerations

- Zero JavaScript framework overhead; Time-to-Interactive is bounded by font loading (Google Fonts: Syne, DM Mono, Space Mono).
- Canvas animation runs on `requestAnimationFrame` loop; node count (70) is calibrated to maintain ≥60fps on mid-range devices.
- All CSS animations use `transform` and `opacity` exclusively, ensuring GPU compositing without layout reflow.

---

## Deployment

The repository is configured for direct **GitHub Pages** deployment from the `main` branch root. No build step is required.

```bash
# Clone the repository
git clone https://github.com/ilsamaritano/ilsamaritano.github.io.git
cd ilsamaritano.github.io

# Open locally (no server required for static assets)
open index.html

# Deploy: push to main branch — GitHub Pages handles the rest
git add .
git commit -m "update: <description>"
git push origin main
```

The live site is accessible at: **[https://ilsamaritano.github.io](https://ilsamaritano.github.io)**

---

## Selected Publications

A non-exhaustive selection of high-impact contributions. Full bibliographic record available on [Google Scholar](https://scholar.google.com) and [ORCID](https://orcid.org/0009-0002-4632-1179).

**2026**
- *From Digital Twins to AI Agents: A Synthetic Data Paradigm for Next-Generation Cybersecurity* — CRC/Taylor & Francis (Book Chapter)
- *Evaluating Adversary Strategies Through a Security Twin* — IEEE PerCom Workshops 2026
- *Quantifying Resilience of Cyber-Physical Systems to Zero-Day Threats* — ESREL 2026

**2025**
- *AI-enabled Cybersecurity using Synthetic Data* — **IEEE PerCom 2025**, Washington DC · 5 citations
- *A Security Twin to Defeat Intrusions in Cyber Physical Systems* — ESREL SRA-E 2025 · 4 citations
- *A Framework for Proactive Cyber-Resilience: Non-intrusive Modeling for Autonomous Defense* — DS-RT 2025 · 3 citations

**2024**
- *A Comparative Study of Machine Learning Models for Hate Speech and Stereotype Detection in Italian Texts* — IJCAST · 6 citations
- *Database Decomposition to Satisfy the Least Privilege Principle in Healthcare* — ARIS2 · 2 citations

---

## Contact & Academic Profiles

| Channel | Link |
|---|---|
| **Email** | [vincesammartino@gmail.com](mailto:vincesammartino@gmail.com) |
| **LinkedIn** | [vincenzo-sammartino-0339191a1](https://www.linkedin.com/in/vincenzo-sammartino-0339191a1) |
| **ORCID** | [0009-0002-4632-1179](https://orcid.org/0009-0002-4632-1179) |
| **GitHub** | [@ilsamaritano](https://github.com/ilsamaritano) |

---

## License

This repository is released under the **MIT License**. Academic content (publications list, research descriptions, biographical data) remains the intellectual property of Vincenzo Sammartino. Reuse of design patterns and implementation code is permitted with attribution.

---

<p align="center">
  <sub>PhD in Artificial Intelligence · Università di Pisa · KAUST Visiting Researcher · 2026</sub>
</p>
