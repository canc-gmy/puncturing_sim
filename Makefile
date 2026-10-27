# Composite Sandwich Puncture Simulation - Workflow Automation
# Python environment: .venv

PYTHON := .venv/Scripts/python.exe
PDFLATEX := C:/Users/rossi/AppData/Local/Programs/MiKTeX/miktex/bin/x64/pdflatex.exe

.PHONY: all help init analyze phase1 phase1-v1 run-phase1 extract fd-curve validate phase2 phase2-v1 run-phase2 report clean

help:
	@echo "Available commands:"
	@echo "  make analyze     - Analyze and plot experimental test data"
	@echo "  make phase1      - Generate OpenCourant input decks for Phase 1 (v2.0 Polar Homogenized)"
	@echo "  make run-phase1  - Execute OpenCourant solver for Phase 1"
	@echo "  make extract     - Convert animations to VTK & export time history CSVs"
	@echo "  make fd-curve    - Extract Force-Displacement response"
	@echo "  make validate    - Compare Simulation vs Experimental F-d curve"
	@echo "  make phase2      - Generate OpenCourant input decks for Phase 2 (v2.0 Polar Meso-scale)"
	@echo "  make run-phase2  - Execute OpenCourant solver for Phase 2"
	@echo "  make report      - Build publication-grade LaTeX simulation report PDFs"
	@echo "  make clean       - Clean temporary build artifacts"

analyze:
	$(PYTHON) src/validation/plot_experiment.py

phase1:
	$(PYTHON) src/preprocessing/generate_model_phase1_v2.py

phase1-v1:
	$(PYTHON) src/preprocessing/generate_model_phase1.py

run-phase1:
	$(PYTHON) src/preprocessing/run_simulation.py phase1

extract:
	$(PYTHON) src/postprocessing/extract_results.py phase1
	$(PYTHON) src/postprocessing/extract_results.py phase2

fd-curve:
	$(PYTHON) src/postprocessing/extract_fd_curve.py phase1
	$(PYTHON) src/postprocessing/extract_fd_curve.py phase2

validate:
	$(PYTHON) src/validation/compare_fd_curves.py

phase2:
	$(PYTHON) src/preprocessing/generate_model_phase2_v2.py

phase2-v1:
	$(PYTHON) src/preprocessing/generate_model_phase2.py

run-phase2:
	$(PYTHON) src/preprocessing/run_simulation.py phase2

report:
	cd docs/reports && $(PDFLATEX) -interaction=nonstopmode --enable-installer phase1_report.tex
	cd docs/reports && $(PDFLATEX) -interaction=nonstopmode --enable-installer phase2_report.tex
	cp docs/reports/phase1_report.pdf reports/phase1_report.pdf
	cp docs/reports/phase2_report.pdf reports/phase2_report.pdf

clean:
	rm -rf *.tmp build/ *.aux *.log *.out
