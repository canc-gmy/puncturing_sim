# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [3.0.0] - 2026-10-27
### Added
- **Full Discrete Meso-Scale Honeycomb Core Architecture (`mesoscale_honeycomb_full.py`, `generate_model_phase3.py`):**
  - Completely eliminated the homogenized continuum core across the entire $50 \times 50\text{ mm}$ quarter-symmetric domain.
  - Implemented parametric honeycomb generator with Liang-Barsky 2D box clipping, discretizing 871 unique hexagonal cell walls ($d_{\text{cell}} = 3.175\text{ mm}$) with $5,226$ Belytschko-Tsay aluminium foil shells and 4,382 nodes ($9,834$ total elements).
- **Core-to-Skin Adhesive Interface & Interpenetration Fix:**
  - Evaluated mechanical bond standards against ASTM C273 (sandwich plate core shear: $\tau_{13} = 3.48\text{ MPa}, \tau_{23} = 2.21\text{ MPa}$), ASTM C297 (flatwise tension: $6.5 - 9.5\text{ MPa}$), and aerospace epoxy structural film adhesives ($\tau_{\text{adh}} \approx 35 - 42\text{ MPa}$).
  - Resolved contact deactivation bug: identified that initial penetrations coupled with `INACTIV = 1` had set secondary contact stiffness to zero on over 1,000 nodes, allowing cell walls to ghost through the skins.
  - Implemented $z_{\text{offset}} = 0.050\text{ mm}$ geometric clearance with $Gap_{\text{min}} = 0.010\text{ mm}$ and active contact stiffness (`INACTIV = 0`), guaranteeing 0 initial penetrations and $100\%$ active contact resistance from cycle 0.
  - Expanded indenter `/INTER/TYPE7/1` slave set to all laminate and foil nodes in $r \le 28.0\text{ mm}$, preventing indenter mesh penetration through eroded plies.
- **Experimental Correlation Breakthrough:**
  - Solved 162,151 explicit integration cycles in **728.79 s (12 min 8 s)** on AMD Ryzen 9 7900X (24 OpenMP threads, `-nt 24`).
  - Accurately predicted the primary top-skin puncture resistance at **$37.34\text{ kN}$ at $5.00\text{ mm}$** (within **$4.3\%$** of the experimental $35.80\text{ kN}$ at $5.70\text{ mm}$).
  - Achieved the lowest Sprague-Geers phase error across all project models: **$P = 22.82\%$**.
  - Converted all 82 animation output states to VTK format in `results/phase3_full_mesoscale/vtk/` for 3D post-processing.
- **Documentation & Reporting:**
  - Updated validation module `compare_fd_curves.py` with 4-way correlation overlay and Sprague-Geers metrics across all three phases.
  - Authored and compiled comprehensive technical report: `reports/phase3_report.pdf` (and `docs/reports/phase3_report.pdf`).

## [2.3.0] - 2026-10-27
### Added
- **Literature-Grounded Constitutive Calibration:**
  - Calibrated Aluminium 5052 foil plasticity in Phase 2 using thin-foil fracture parameters ($A = 210.0\text{ MPa}$, $B = 65.0\text{ MPa}$, $n = 0.25$, $\varepsilon_{\text{max}} = 0.09$), eliminating artificial post-yield stiffness and capturing progressive shell tearing along the indenter perimeter.
  - Formulated out-of-plane shear yield function (`/FUNCT/29`) with shear plateau $\tau_y = 3.48\text{ MPa}$ and shear strain erosion limits ($\gamma = 0.25$) on orthotropic core (`/MAT/LAW28`).
  - Tuned solid brick deletion threshold (`/DT/BRICK/DEL` set to $2.0 \times 10^{-8}\text{ s}$) in `radioss_writer.py`, preventing inverted element locking and negative stiffness node errors during late bottom-skin compression.
- **Experimental Correlation Breakthrough:**
  - Phase 2 predicted ultimate peak force reached **$41.06\text{ kN}$**, within **$14.69\%$** of the physical test benchmark ($35.80\text{ kN}$, reduced from previous $+55.8\%$ overprediction).
  - Sprague-Geers phase error confirmed at **$P = 26.81\%$**, with full $16.2\text{ mm}$ stroke completed in **4 minutes 14 seconds** across 134,513 cycles on 24 OpenMP threads.
  - Phase 1 completed all 151,797 cycles in **3 minutes 00 seconds** under normal termination.
- **Repository Invariants & Rule Persistence:**
  - Persisted workspace simulation invariants in `GEMINI.md`: 24-thread execution profile, `/INTER/TYPE19` edge contact, quarter-symmetry conventions, `/PROP/TYPE6` card formatting, and $\Delta M / M < 1.0\%$ mass conservation.
- **Updated Documentation & Verification:**
  - Exported complete 3D visualization datasets (81 VTK states for Phase 1, 82 VTK states for Phase 2).
  - Compiled publication-quality technical PDF reports: `reports/phase1_report.pdf` and `reports/phase2_report.pdf`.

## [2.2.0] - 2026-10-27
### Added
- **Quarter-Symmetric FE Architecture (`polar_mesh_quarter.py`, `mesoscale_honeycomb_quarter.py`):**
  - Reduced computational domain by $4\times$ ($x \ge 0, y \ge 0$, $50 \times 50\text{ mm}$), dramatically speeding up simulation cycle while preserving physical boundary conditions.
  - Formulated exact quarter boundary constraints: $X$-symmetry on $x=0$ (`100 011`), $Y$-symmetry on $y=0$ (`010 101`), fully fixed circular aperture support on $z=0, r \ge 15.0\text{ mm}$ (`111 111`), and rigid punch master node guided purely in $Z$ (`110 111`).
  - Implemented automatic $4.0\times$ reaction force and energy scaling in `extract_fd_curve.py` for direct correlation against full experimental benchmarks.
- **Edge-to-Surface Penalty Contact (`/INTER/TYPE19`):**
  - Resolved the cell-wall mesh explosion bug that occurred upon initial punch contact under standard `/INTER/TYPE7` node-to-surface definitions.
  - `/INTER/TYPE19` (`Iedge = 1`, `INACTIV = 1`) treats laminate inner faces as master surfaces and foil shell edges as secondary lines, enforcing normal contact penalties strictly in the vertical $\pm Z$ direction without spurious transverse ejection forces.
  - Paired with `/INTER/TYPE7/4` self-contact for foil progressive accordion folding.
- **Rapid Parametric Calibration & Safe Mass Scaling:**
  - Tuned kinematics with $v = 1000\text{ mm/s}$ and $2\text{ ms}$ smooth ramp, coupled with safe nodal mass scaling (`/DT/NODA/CST` at $1.0\times 10^{-7}\text{ s}$).
  - Achieved mass error of only $0.14\%$ (well below the $1.0\%$ industry limit).
  - Reduced wallclock execution time by $\sim 10\times$:
    - Phase 1 Homogenized: **96.44 s (1 min 36 s)** across 85,990 cycles on 24 OpenMP threads.
    - Phase 2 Meso-Scale: **322.38 s (5 min 22 s)** across 162,001 cycles on 24 OpenMP threads.
- **Constitutive Property Bug Fixes:**
  - Rectified field alignment in `/PROP/TYPE6` where an extra line shifted the ply angle onto Card 5 (`deltaT_min`), which previously caused the starter to set `BRICK MINIMUM TIME STEP = 45.0 s` on plies 2, 4, 6 and delete them at cycle 0.
  - Adjusted `/DT/BRICK/DEL` and `/DT/SHELL/DEL` thresholds to $1.0\times 10^{-9}\text{ s}$ to prevent premature element erosion at initial integration steps.
- **Updated Documentation & Verification:**
  - Quantitative Sprague-Geers correlation metrics: Phase 1 ($M = 40.26\%, P = 32.88\%, C = 51.97\%$), Phase 2 ($F_{\text{peak}} = 55.79\text{ kN}, E_{\text{abs}} = 427.13\text{ J}$).
  - Compiled publication-quality technical PDF reports: `reports/phase1_report.pdf` and `reports/phase2_report.pdf`.

## [2.1.0] - 2026-10-27
### Added
- **24-Thread Parallel Solver Execution:** Updated `run_simulation.py` with OpenMP 24-worker configuration (`-nt 24`, `OMP_NUM_THREADS=24`, `KMP_STACKSIZE=400m`) fully leveraging the 24 logical processors of AMD Ryzen 9 7900X.
- **Quasi-Static Velocity Scaling ($100\text{ mm/s}$):** Reduced indenter velocity from $1000\text{ mm/s}$ to $100\text{ mm/s}$ with a smooth sinusoidal acceleration ramp over $10\text{ ms}$, suppressing dynamic inertia oscillations and ensuring $E_{\text{kin}} / E_{\text{int}} < 1\%$.
- **High-Density Animation Output (82 States):** Refined `/ANIM/DT` to $\Delta t = 2.0\text{ ms}$ ($\Delta d = 0.20\text{ mm}$ displacement per frame), producing 82 continuous 3D VTK visualization states for Phase 2 and 55 states for Phase 1.
- **Multi-Body Penalty Interface Formulation (`/INTER/TYPE7`):**
  - Top skin to honeycomb cell-wall edges contact (`/INTER/TYPE7/2`) transmitting compression and shear.
  - Honeycomb cell-wall edges to bottom skin contact (`/INTER/TYPE7/3`) supporting the core over the aperture.
  - Honeycomb cell-wall self-contact (`/INTER/TYPE7/4`) preventing foil interpenetration during progressive folding.
  - Incorporated `INACTIV=1` deactivation to eliminate initial contact force spikes without altering coordinates.
- **Validation Correlation Improvements:**
  - Phase 1 absorbed energy achieved $221.50\text{ J}$ ($-1.8\%$ relative error against physical benchmark $225.56\text{ J}$).
  - Initial skin shear breakthrough captured at $2.00\text{ mm}$ with $15.28\text{ kN}$ ($+5.4\%$ error).
  - Phase 2 peak shear puncture force reached $52.89\text{ kN}$ at $3.71\text{ mm}$, with Sprague-Geers Comprehensive Error improved from $73.81\%$ to $51.95\%$.
- **Compiled PDF Documentation:**
  - `reports/phase1_report.pdf` & `docs/reports/phase1_report.pdf` (822 KB).
  - `reports/phase2_report.pdf` & `docs/reports/phase2_report.pdf` (423 KB).
  - Updated multi-model correlation overlay `docs/reports/correlation_overlay.png`.

## [2.0.0] - 2026-10-27
### Added
- **Cylindrical Polar Meshing (`polar_mesh_2d.py`):** Concentric rings matching punch radius ($r_p = 12.5\text{ mm}$) and aperture window ($r_{\text{ap}} = 15.0\text{ mm}$) with five radial element bands resolving the $2.5\text{ mm}$ shear clearance gap.
- **Ply-by-Ply Solid Discretization:** 7 explicit solid element layers per skin ($0.333\text{ mm}$ per ply, 14 total skin layers across $[0/45/0/45/0/45/0]$ layup) using orthotropic solid properties (`/PROP/TYPE6`).
- **Advanced Constitutive Models:**
  - CFRP woven fabric: `/MAT/LAW25` (Chang-Chang) coupled with progressive damage and element deletion `/FAIL/CHANG`.
  - Orthotropic crushable continuum: `/MAT/LAW28` with empirical plateau stress ($\sigma = 4.6\text{ MPa}$) and densification.
  - Meso-scale aluminium foil: Johnson-Cook plasticity `/MAT/LAW2` with 5-card standard parameterization.
- **Full Stroke Solver Execution:**
  - Phase 1 Homogenized: Full $16.0\text{ mm}$ stroke ($16.2\text{ ms}$, 207,479 cycles) with zero mass error and clean element erosion.
  - Phase 2 Meso-scale Hybrid: Full $16.0\text{ mm}$ stroke ($16.2\text{ ms}$, 193,446 cycles) resolving individual cell wall folding, buckling, and tearing.
- **ISO 18571 / ASME V&V 10 Quantitative Validation:**
  - Automated Sprague-Geers metric calculation ($M, P, C$) implemented in `src/validation/compare_fd_curves.py`.
  - Phase 1 achieved magnitude error $M = -3.36\%$, phase error $P = 35.83\%$, and comprehensive error $C = 35.99\%$.
  - Phase 2 achieved phase error $P = 30.82\%$, comprehensive error $C = 73.81\%$.
- **Compiled PDF Documentation:**
  - `reports/phase1_report.pdf` & `docs/reports/phase1_report.pdf` (Homogenized formulation, 844 KB).
  - `reports/phase2_report.pdf` & `docs/reports/phase2_report.pdf` (Meso-scale hybrid formulation, 443 KB).
  - Multi-model correlation comparison figure `docs/reports/correlation_overlay.png`.

## [1.0.0] - 2026-10-26
### Added
- Complete end-to-end validated simulation suite for quasi-static shear puncture of CFRP/Al honeycomb sandwich panels.
- Automated multi-model validation pipeline (`src/validation/compare_fd_curves.py`) producing overlay comparison figures and metrics JSON.
- Publication-quality technical LaTeX reports with full theory, material parameters, energy conservation diagnostics, and experimental benchmarking:
  - `reports/phase1_report.pdf` (Homogenized continuum core formulation).
  - `reports/phase2_report.pdf` (Meso-scale discrete cell wall hybrid formulation).
- Validated with OpenCourant explicit integration solver, including full VTK datasets for ParaView visualization.

## [0.3.0] - 2026-10-26
### Added
- Phase 2 Meso-scale hybrid sandwich model generator (`src/preprocessing/generate_model_phase2.py`).
- Hexagonal cell grid generator with node-merging algorithms (`src/preprocessing/mesoscale_honeycomb_generator.py`) resolving 139 individual honeycomb cells and 4,020 shell elements.
- Discrete shell wall assignment for single foil ($0.0381\text{ mm}$) and double adhesive ribbon foil ($0.0762\text{ mm}$).
- Penalty contact formulation (/INTER/TYPE7) and imposed velocity boundary condition (/IMPVEL) calibrated for through-thickness shear clearance kinematics.
- Force-displacement extraction module (`src/postprocessing/extract_fd_curve.py`) supporting contact reaction forces and internal energy gradient rate formulations.

## [0.2.0] - 2026-10-26
### Added
- Integrated OpenCourant Windows 64-bit solver release (`starter_win64.exe`, `engine_win64_sp.exe`, `anim_to_vtk`, `th_to_csv`).
- Phase 1 Homogenized 3D explicit finite element model (23,409 nodes, 20,000 solid elements, 120 punch shells).
- Automated solver runner with Intel oneAPI environment configuration (`src/preprocessing/run_simulation.py`).
- Completed explicit dynamic time-integration cycles ($16.0\text{ ms}$ stroke).
- Post-processing pipeline converting binary animation files to 3D VTK meshes for ParaView (`src/postprocessing/extract_results.py`).
- Time-history conversion to CSV and energy balance diagnostics plotting (`src/postprocessing/plot_simulation_energy.py`).

## [0.1.0] - 2026-10-26
### Added
- Initial project architecture and directory structure.
- Material datasheets ingested and cataloged:
  - CFRP: CIT CF306 12K T700 T2/2 ET445 40% (cured ply thickness $0.333\text{ mm}$, $7$ plies $[0/45/0/45/0/45/0]$).
  - Honeycomb: IMATEC Aluminium 5052 - 1/8" cell - 0.0015" foil - 6.1 pcf.
- Full material characterization document (`docs/theory/material_characterization.md`).
- Experimental puncture data cataloged (`experimental/force_displacement/`).
- Python virtual environment with `numpy`, `scipy`, `pandas`, and `matplotlib`.
- Git version control initialized with feature branching model.
- Master project plan and specification artifact.
