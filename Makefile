init:
	pip install -e '.[dev,bench]'

test:
	pytest -q

lint:
	ruff check .

type:
	mypy src/fast_sim --ignore-missing-imports

examples:
	python examples/sir_minimal.py

bench:
	fastsim bench --quick

dist:
	python -m build
