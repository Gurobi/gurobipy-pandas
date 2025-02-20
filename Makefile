.PHONY: wheel sdist

wheel:
	python -m build

develop:
	python -m pip install -e .
	python -m pip uninstall -y -qq gurobi-sphinxtheme
	python -m pip install -r docs/requirements.txt
	python -m pip install flake8
	pre-commit install

check:
	python -m flake8 . --count --show-source --statistics

test:
	python -m unittest discover -b
	python -m jupytext --set-kernel python3 --execute --to ipynb docs/source/examples/*.md

format:
	pre-commit run --all-files
	python -m jupytext --opt notebook_metadata_filter=-kernelspec --from myst --to myst docs/source/examples/*.md
