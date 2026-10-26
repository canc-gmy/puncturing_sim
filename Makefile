# Composite Sandwich Puncture Simulation - Workflow Automation
# Python environment: .venv

PYTHON := .venv/Scripts/python.exe

.PHONY: all help init analyze phase1 phase2 report clean

help:
	@echo "Available commands:"
	@echo "  make analyze   - Analyze and plot experimental test data"
	@echo "  make phase1    - Generate OpenCourant input decks for Phase 1 (Homogenized Core)"
	@echo "  make phase2    - Generate OpenCourant input decks for Phase 2 (Meso-scale Core)"
	@echo "  make report    - Build LaTeX simulation report PDF"
	@echo "  make clean     - Clean temporary build artifacts"

analyze:
	$(PYTHON) src/validation/plot_experiment.py

phase1:
	$(PYTHON) src/preprocessing/generate_model_phase1.py

run-phase1:
	$(PYTHON) src/preprocessing/run_simulation.py

extract:
	$(PYTHON) src/postprocessing/extract_results.py

phase2:
	$(PYTHON) src/preprocessing/generate_model_phase2.py

clean:
	rm -rf *.tmp build/ *.aux *.log *.out
