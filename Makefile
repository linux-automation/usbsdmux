PYTHON=python3

PYTHON_ENV_ROOT=envs
PYTHON_PACKAGING_VENV=$(PYTHON_ENV_ROOT)/$(PYTHON)-packaging-env
PYTHON_QA_ENV=$(PYTHON_ENV_ROOT)/$(PYTHON)-qa-env

# packaging environment #######################################################
.PHONY: packaging-env build _release

$(PYTHON_PACKAGING_VENV)/.created: REQUIREMENTS.packaging.txt
	rm -rf $(PYTHON_PACKAGING_VENV) && \
	$(PYTHON) -m venv $(PYTHON_PACKAGING_VENV) && \
	. $(PYTHON_PACKAGING_VENV)/bin/activate && \
	$(PYTHON) -m pip install --upgrade pip && \
	$(PYTHON) -m pip install -r REQUIREMENTS.packaging.txt
	date > $(PYTHON_PACKAGING_VENV)/.created

packaging-env: $(PYTHON_PACKAGING_VENV)/.created

build: packaging-env
	. $(PYTHON_PACKAGING_VENV)/bin/activate && \
	rm -rf dist *.egg-info && \
	./setup.py sdist

_release: build
	. $(PYTHON_PACKAGING_VENV)/bin/activate && \
	$(PYTHON) -m twine upload dist/*

# helper ######################################################################
.PHONY: clean envs

clean:
	rm -rf $(PYTHON_ENV_ROOT)

envs: packaging-env qa-env

# testing #####################################################################
.PHONY: qa qa-env qa-black qa-flake8 qa-pytest

$(PYTHON_QA_ENV)/.created: REQUIREMENTS.qa.txt
	rm -rf $(PYTHON_QA_ENV) && \
	$(PYTHON) -m venv $(PYTHON_QA_ENV) && \
	. $(PYTHON_QA_ENV)/bin/activate && \
	$(PYTHON) -m pip install pip --upgrade && \
	$(PYTHON) -m pip install -r ./REQUIREMENTS.qa.txt && \
	date > $(PYTHON_QA_ENV)/.created

qa-env: $(PYTHON_QA_ENV)/.created

qa: qa-black qa-flake8 qa-pytest

qa-black: qa-env
	. $(PYTHON_QA_ENV)/bin/activate && \
	$(PYTHON) -m black --check --diff .

qa-flake8: qa-env
	. $(PYTHON_QA_ENV)/bin/activate && \
	$(PYTHON) -m flake8

qa-pytest: qa-env
	. $(PYTHON_QA_ENV)/bin/activate && \
	$(PYTHON) -m pytest -vv
