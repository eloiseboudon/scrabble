.PHONY: install backend frontend db migrate upgrade clean

VENV=.venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

install: $(VENV)

$(VENV): backend/requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install -r backend/requirements.txt

backend: install
	$(VENV)/bin/uvicorn backend.main:app --reload

frontend:
	python3 -m http.server 5173 --directory frontend

db:
	psql -U eloise -d scrabble

migrate:
	$(VENV)/bin/alembic revision --autogenerate -m "migration"

upgrade:
	$(VENV)/bin/alembic upgrade head

clean:
	rm -rf .venv
