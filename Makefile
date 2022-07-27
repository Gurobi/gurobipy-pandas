.PHONY: wheel sdist

wheel:
	python -m build --wheel

sdist:
	python -m build --sdist

develop:
	python -m pip install -e .
	python -m pip install -r docs/requirements.txt

test:
	python -m unittest
	cd docs && make html
