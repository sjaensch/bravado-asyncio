all: devenv

.PHONY: devenv
devenv: venv setup.py requirements-dev.txt
	venv/bin/pip install -e .
	venv/bin/pip install -r requirements-dev.txt

.PHONY: test
test: devenv
	venv/bin/tox

.PHONY: docs
docs: devenv
	venv/bin/tox -e docs

venv:
	virtualenv -p python3.8 venv

.PHONY: clean
clean:
	find . -name '__pycache__' -delete
	rm -rf .tox
	rm -rf venv
