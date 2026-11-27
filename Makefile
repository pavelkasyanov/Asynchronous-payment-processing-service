PROJECT = payment-processing-service
DB_NAME = payment-processing-service
SRC_DIR := app
VENV_DIR = .venv
PYTHON := python3
RUN := . $(VENV_DIR)/bin/activate;
.DEFAULT_GOAL := init

venv_init:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		$(PYTHON) -m venv $(VENV_DIR) --prompt $(PROJECT); \
	fi

venv: venv_init
	$(RUN) pip install -r requirements.txt

init: venv	

lint:
	$(RUN) ruff check .

fixmycode:
	$(RUN) ruff check --fix . &&  $(RUN) ruff format .
