# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
