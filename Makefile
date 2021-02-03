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
	poetry install --no-root

.PHONY: test
test: venvcheck		## Run the TOX tests in a TOX environment
	poetry run tox

.PHONY: dev-test
dev-test: venvcheck		## Run the tests in dev environment
	poetry run pytest --cov=pyshacl test/

.PHONY: format
format: venvcheck	## Run Black and isort Formatters
ifeq ("$(FilePath)", "")
	poetry run black --config=./pyproject.toml --verbose pyshacl
	poetry run isort pyshacl
else
	poetry run black --config=./pyproject.toml --verbose "$(FilePath)"
	poetry run isort "$(FilePath)"
endif

.PHONY: lint
lint: venvcheck	## Validate with Black and isort in check-only mode
ifeq ("$(FilePath)", "")
	poetry run flake8 pyshacl
	poetry run black --config=./pyproject.toml --check --verbose pyshacl
	poetry run isort --check-only pyshacl
else
	poetry run flake8 "$(FilePath)"
	poetry run black --config=./pyproject.toml --check --verbose "$(FilePath)"
	poetry run isort --check-only "$(FilePath)"
endif

.PHONY: type-check
type-check: venvcheck	## Validate with Black and isort in check-only mode
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

.PHONY: publish
publish: venvcheck	## Build and publish to PYPI
	poetry build
	poetry publish
