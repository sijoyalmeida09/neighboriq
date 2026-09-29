.PHONY: analyze install test lint compare stats

ZIP ?= 02122

install:
	pip install -e ".[dev]"
	playwright install chromium

analyze:
	python -m neighboriq analyze --zip $(ZIP)

compare:
	python -m neighboriq compare --zips $(ZIP)

stats:
	python -m neighboriq stats

test:
	pytest tests/ -v

lint:
	ruff check . --fix
	black .
