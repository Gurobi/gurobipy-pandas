.PHONY: wheel sdist

wheel:
	python -m build

develop:
	python -m pip install -e .
	python -m pip install -r docs/requirements.txt
	python -m pip install flake8
	pre-commit install

check:
	python -m flake8 . --count --select=E9,F63,F7,F82,F811,F401 --show-source --statistics

test:
	python -m unittest discover -b
	python -m jupytext --set-kernel python3 --execute --to ipynb docs/source/examples/*.md

format:
	pre-commit run --all-files
	python -m jupytext --opt notebook_metadata_filter=-kernelspec --from myst --to myst docs/source/examples/*.md
