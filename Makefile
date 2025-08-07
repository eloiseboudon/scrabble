.PHONY: install backend frontend clean

install: .venv

.venv: backend/requirements.txt
	python3 -m venv .venv
	.venv/bin/pip install -r backend/requirements.txt

backend: install
	.venv/bin/uvicorn backend.main:app --reload

frontend:
	python3 -m http.server 5173 --directory frontend

clean:
	rm -rf .venv
