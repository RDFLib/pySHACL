.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: venvcheck ## Check if venv is active
venvcheck:
ifeq ("$(VIRTUAL_ENV)","")
	@echo "Venv is not activated!"
	@echo "Activate venv first."
	@echo
	exit 1
endif

.PHONY: env
env: venvcheck  ## Double check environment variables
	env

.PHONY: install
install: venvcheck  ## Install the dependencies, but not dev-dependencies
	poetry install --no-dev

.PHONY: dev
dev: venvcheck  ## Install dependencies and dev-dependencies, but not this project itself
	poetry install --no-root --extras "js dev-lint dev-type-checking dev-coverage"

.PHONY: test
test: venvcheck		## Run the TOX tests in a TOX environment
	poetry run tox

.PHONY: dev-test
dev-test: venvcheck		## Run the tests in dev environment
	poetry run pytest --cov=pyshacl test/

.PHONY: format
format: venvcheck	## Run Black and isort Formatters
ifeq ("$(FilePath)", "")
	poetry run ruff check --select I --fix ./pyshacl #isort fix
	poetry run black --config=./pyproject.toml --verbose pyshacl
else
	poetry run ruff check --select I --fix "$(FilePath)" #isort fix
	poetry run black --config=./pyproject.toml --verbose "$(FilePath)"
endif

.PHONY: lint
lint: venvcheck	## Validate with Black and isort in check-only mode
ifeq ("$(FilePath)", "")
	poetry run ruff check ./pyshacl  #flake8
	poetry run ruff check --select I ./pyshacl  #isort
	poetry run black --config=./pyproject.toml --check --verbose pyshacl
else
	poetry run ruff check ./"$(FilePath)"  #flake8
	poetry run ruff check --select I ./"$(FilePath)" #isort
	poetry run black --config=./pyproject.toml --check --verbose "$(FilePath)"
endif

.PHONY: type-check
type-check: venvcheck	## Validate with MyPy in check-only mode
ifeq ("$(FilePath)", "")
	poetry run python3 -m mypy --ignore-missing-imports pyshacl
else
	poetry run python3 -m mypy --ignore-missing-imports "$(FilePath)"
endif

.PHONY: upgrade
upgrade: venvcheck	## Upgrade the dependencies
	poetry update

.PHONY: downgrade
downgrade: venvcheck ## Downgrade the dependencies
	git checkout pyproject.toml && git checkout poetry.lock
	poetry install --no-root --extras "js dev-lint dev-type-checking dev-coverage"

.PHONY: publish
publish: venvcheck	## Build and publish to PYPI
	poetry build
	poetry publish
