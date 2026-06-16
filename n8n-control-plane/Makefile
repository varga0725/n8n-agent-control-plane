.PHONY: help install models test test-all smoke doctor tools clean

help:
	@echo "make install   - install dev deps (pytest, pyyaml, datamodel-code-generator)"
	@echo "make models    - generate typed Pydantic models from openapi/n8n-openapi.json"
	@echo "make test      - run offline unit + contract tests"
	@echo "make doctor    - validate configuration"
	@echo "make tools     - list all primitive tools"

install:
	pip install -e ".[dev]" datamodel-code-generator

models:
	python3 scripts/generate_models.py

test:
	PYTHONPATH=src python3 -m pytest tests/unit tests/contract -q

test-all:
	PYTHONPATH=src python3 -m pytest -q

doctor:
	PYTHONPATH=src python3 -m n8n_cp doctor

tools:
	PYTHONPATH=src python3 -m n8n_cp tools

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
