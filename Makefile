.PHONY: all up down ingest test dashboard lint clean

PYTHON ?= python
PYTHONPATH := src

all: up ingest test dashboard

up:
	docker compose up -d --wait

down:
	docker compose down

ingest:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m lh_nautical.ingestion

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -v

dashboard:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m lh_nautical.dashboard

lint:
	$(PYTHON) -m ruff check src tests run_all.py

clean:
	rm -rf reports/*.html reports/*.json .pytest_cache .ruff_cache

