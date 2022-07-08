.PHONY: wheel sdist

wheel:
	python -m build --wheel

sdist:
	python -m build --sdist

develop:
	python -m pip install -e .

test:
	python -m unittest
