# CONTRIBUTING

### The PySHACL project encourages submissions from anyone who wishes to contribute

There are some strict submission quality requirements:

## Code Format

PySHACL uses the `black` code style. https://github.com/psf/black

Specifically, we use v20.8b1 in `py36` mode, with line length of `119`, and `skip-string-normalization = true`.

## Code Linting

PySHACL requires all code to pass the Flake8 linter. In the internal test suite, we use Flake8 v3.8.0.

In addition to Flake8, we use `isort` to keep the import strings at the top of each source file in a consistent sorted order. The version if isort used is v5.7.0 and it is configured with the isort settings listed in the pyproject.toml file.

## Type Checking

PySHACL uses MyPy to run static type analysis checks on the code. Not all parts of PySHACL have type annotations, but those parts that do should be annotated correctly to pass the MyPy test.

The internal test suite uses MyPy v0.800.

## Testing

The best way to comprehensively test PySHACL is to use [Tox](https://tox.readthedocs.io/en/latest/).

It is a simple matter of running `pip3 install tox` then `tox` on the commandline in the project root.

This will run a whole suite of tests, including pytest, flake8, mypy, black and isort.

All tests in the PySHACL pytest test suite should pass without errors.

## Makefile

There is also a Makefile in the project root that you can for covenience to kick off tests with `make test`, as well as some non-tox commands that can be invoked with `make format`, `make list` and `make type-check`.


