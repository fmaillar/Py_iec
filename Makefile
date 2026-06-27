.PHONY: run lint test doc type coverage

run:
	python -m py_iec --example

lint:
	ruff check src tests

test:
	pytest

doc:
	pdoc src/py_iec -o docs


type:
	mypy src

coverage:
	pytest --cov=py_iec --cov-report=term-missing
