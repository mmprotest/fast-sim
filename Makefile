init:
	pip install -e ".[dev,bench,viz]"

test:
	pytest -q

lint:
	ruff check .

type:
	mypy src/fast_sim --ignore-missing-imports

examples:
	fsim run --config examples/configs/sir_demo.yaml --steps 10 --seed 123

bench:
	fsim bench --quick

dist:
	python -m build
