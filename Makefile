# Makefile for privacy-preserving-data-architecture
#
# Requires GNU Make. On Windows: WSL, Git Bash with make, or
# Chocolatey (choco install make) / Scoop (scoop install make).

.PHONY: help install lint fmt type-check test coverage benchmark demo validate-csv clean

help:
	@echo "Available targets:"
	@echo "  install     Install dev dependencies"
	@echo "  lint        Run ruff linter"
	@echo "  fmt         Run ruff formatter"
	@echo "  type-check  Run mypy on core modules"
	@echo "  test        Run pytest"
	@echo "  coverage    Run pytest with coverage report"
	@echo "  benchmark   Run FHE cleartext-vs-ciphertext benchmark"
	@echo "  demo        Run the FHE medical-image demo"
	@echo "  validate-csv  Validate docs/compliance/nist-control-mapping.csv schema + control IDs"
	@echo "  clean       Remove generated artefacts"

install:
	pip install -e ".[dev]"

lint:
	ruff check .

fmt:
	ruff format .

type-check:
	mypy fhe-feature-extraction/fhe_pipeline.py 	     dp-llm-training/dp_trainer.py 	     dp-llm-training/budget_accountant.py 	     llm-leakage-assessment/assessment_runner.py 	     --ignore-missing-imports --no-strict-optional

test:
	pytest tests/ -v --tb=short

coverage:
	pytest tests/ -v --tb=short --cov --cov-config=.coveragerc --cov-report=term-missing

benchmark:
	python fhe-feature-extraction/benchmarks/run_benchmark.py

demo:
	python fhe-feature-extraction/examples/medical_image_demo.py

validate-csv:
	python tools/validate_control_mapping.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .coverage .pytest_cache .mypy_cache htmlcov
