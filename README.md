# Composite Sandwich Puncture Simulation (OpenCourant)

High-fidelity research-grade finite element simulation of a composite sandwich panel subjected to quasi-static shear puncture, modeled and solved using **OpenCourant** (open-source explicit solver, community fork of OpenRadioss).

---

## 1. Specimen Architecture

```
                       Indenter (Rigid Cylinder ⌀25 mm)
                                     ↓↓↓
 ═══════════════════════════════════════════════════════════════════  Top Face Sheet (2.33 mm)
 -------------------------------------------------------------------  7 plies T700 Woven [0/45/0/45/0/45/0]
                                                                      Cohesive interface (Skin-Core)
 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  Aluminium Honeycomb Core
 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  5052 - 1/8" - 6.1 pcf (15.0 mm)
 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  
                                                                      Cohesive interface (Skin-Core)
 ═══════════════════════════════════════════════════════════════════  Bottom Face Sheet (2.33 mm)
 -------------------------------------------------------------------  7 plies T700 Woven [0/45/0/45/0/45/0]
               ████████                            ████████
               Support                              Support
               (Rigid)        <--- ⌀30 mm --->     (Rigid)
                              Aperture Window
```

* **Panel Dimensions:** $100\text{ mm} \times 100\text{ mm} \times 19.66\text{ mm}$
* **Top & Bottom Skins:** 7 plies of CIT CF306 12K T700 Twill 2×2 ($t_{\text{ply}} = 0.333\text{ mm}$, total $h = 2.331\text{ mm}$ per skin)
* **Layup:** $[0^\circ / 45^\circ / 0^\circ / 45^\circ / 0^\circ / 45^\circ / 0^\circ]$
* **Core:** Aluminium Honeycomb Alloy 5052, cell 1/8", foil $0.0015''$, density 6.1 pcf, height $15.0\text{ mm}$
* **Indenter:** Flat-ended rigid cylinder $\varnothing 25\text{ mm}$
* **Support Fixture:** Rigid plate with central $\varnothing 30\text{ mm}$ circular aperture ($2.5\text{ mm}$ shear clearance)

---

## 2. Methodology & Phases

1. **Phase 1 — Homogenized Core Model:**
   * 3D solid elements for face sheets with cohesive zone interfaces.
   * Continuum orthotropic crushable solid for the honeycomb core (LAW28).
   * Fast turnaround for calibration against experimental force-displacement curve.
2. **Phase 2 — Meso-scale Hybrid Model:**
   * Meso-scale honeycomb cell walls explicitly modeled as shell elements in the puncture zone ($\varnothing 40\text{ mm}$).
   * Captures cell-wall buckling, folding, plastic yielding, and tearing.
   * Homogenized core in the far-field with kinematic tied interfaces.
3. **Automated Reporting:**
   * Script-driven extraction of force-displacement, energy balance, delamination areas, and stress distributions.
   * Auto-compiled publication-quality LaTeX reports.

---

## 3. Directory Layout

```
punturing_sim/
├── docs/
│   ├── datasheets/          # CFRP and Honeycomb manufacturer specifications
│   ├── theory/              # Constitutive models & parameter derivation
│   └── reports/             # LaTeX report sources
├── src/
│   ├── preprocessing/       # Python model and mesh generation
│   ├── postprocessing/      # Python result extraction and plotting
│   └── validation/          # Correlation with experimental curves
├── models/
│   ├── phase1_homogenized/  # OpenCourant starter and engine decks (Phase 1)
│   └── phase2_mesoscale/    # OpenCourant starter and engine decks (Phase 2)
├── experimental/            # Test data (CSV force-displacement, C-scans)
├── results/                 # Raw solver outputs (git-ignored)
├── reports/                 # Compiled PDF reports
├── templates/               # LaTeX templates
├── requirements.txt         # Python dependencies
├── Makefile                 # Automated build/run workflow
├── CHANGELOG.md             # Semantic versioning history
└── README.md                # This document
```

---

## 4. Quick Start

### 4.1 Python Environment
```bash
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4.2 Inspect Experimental Data
```bash
python src/validation/plot_experiment.py
```

### 4.3 Generate and Run Model
```bash
python src/preprocessing/generate_model_phase1.py
# Execute OpenCourant starter and engine:
# agy / opencourant starter & engine commands
```
