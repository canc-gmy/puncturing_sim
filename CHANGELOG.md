# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Phase 1 homogenized model starter and engine deck generator.
- Experimental data analysis and visualization script.

## [0.2.0] - 2026-10-26
### Added
- Integrated OpenCourant Windows 64-bit solver release (`starter_win64.exe`, `engine_win64_sp.exe`, `anim_to_vtk`, `th_to_csv`).
- Phase 1 Homogenized 3D explicit finite element model (23,409 nodes, 20,000 solid elements, 120 punch shells).
- Automated solver runner with Intel oneAPI environment configuration (`src/preprocessing/run_simulation.py`).
- Completed 160,001 explicit dynamic time-integration cycles ($16.0\text{ ms}$ stroke).
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
