PYTHON=python3

PYTHON_ENV_ROOT=envs
PYTHON_PACKAGING_VENV=$(PYTHON_ENV_ROOT)/$(PYTHON)-packaging-env
PYTHON_QA_ENV=$(PYTHON_ENV_ROOT)/$(PYTHON)-qa-env

# packaging environment #######################################################
.PHONY: packaging-env build _release

$(PYTHON_PACKAGING_VENV)/.created:
	rm -rf $(PYTHON_PACKAGING_VENV) && \
	$(PYTHON) -m venv $(PYTHON_PACKAGING_VENV) && \
	. $(PYTHON_PACKAGING_VENV)/bin/activate && \
	$(PYTHON) -m pip install --upgrade pip && \
	$(PYTHON) -m pip install build twine
	date > $(PYTHON_PACKAGING_VENV)/.created

.PHONY: packaging-env build _release

packaging-env: $(PYTHON_PACKAGING_VENV)/.created

build: packaging-env
	. $(PYTHON_PACKAGING_VENV)/bin/activate && \
	rm -rf dist *.egg-info && \
	$(PYTHON) -m build

_release: build
	. $(PYTHON_PACKAGING_VENV)/bin/activate && \
	$(PYTHON) -m twine upload dist/*

# helper ######################################################################
.PHONY: clean envs

clean:
	rm -rf $(PYTHON_ENV_ROOT)

envs: packaging-env qa-env

# testing #####################################################################
.PHONY: qa qa-env qa-codespell qa-pytest qa-ruff

$(PYTHON_QA_ENV)/.created:
	rm -rf $(PYTHON_QA_ENV) && \
	$(PYTHON) -m venv $(PYTHON_QA_ENV) && \
	. $(PYTHON_QA_ENV)/bin/activate && \
	$(PYTHON) -m pip install pip --upgrade && \
	$(PYTHON) -m pip install codespell ruff pytest pytest-mock  && \
	date > $(PYTHON_QA_ENV)/.created

qa-env: $(PYTHON_QA_ENV)/.created

qa: qa-codespell qa-pytest qa-ruff

qa-codespell: qa-env
	. $(PYTHON_QA_ENV)/bin/activate && \
	codespell

qa-codespell-fix: qa-env
	. $(PYTHON_QA_ENV)/bin/activate && \
	codespell -w

qa-pytest: qa-env
	. $(PYTHON_QA_ENV)/bin/activate && \
	$(PYTHON) -m pytest -vv

qa-ruff: qa-env
	. $(PYTHON_QA_ENV)/bin/activate && \
	ruff format --check --diff && ruff check

qa-ruff-fix: qa-env
	. $(PYTHON_QA_ENV)/bin/activate && \
	ruff format && ruff check --fix
