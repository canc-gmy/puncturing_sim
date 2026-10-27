# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
