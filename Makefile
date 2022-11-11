.PHONY: wheel sdist

wheel:
	python -m build --wheel

sdist:
	python -m build --sdist

develop:
	python -m pip install -e .
	python -m pip install -r docs/requirements.txt
	python -m pip install black==22.6.0
	pre-commit install

test:
	python -m unittest discover -b
	python -m jupytext --set-kernel python3 --execute --to ipynb docs/source/examples/*.md

format:
	python -m black src/ tests/
	python -m jupytext --opt notebook_metadata_filter=-kernelspec --from myst --to myst docs/source/examples/*.md
