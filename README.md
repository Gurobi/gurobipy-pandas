[![PyPI - Version](https://img.shields.io/pypi/v/gurobipy-pandas.svg)](https://pypi.org/project/gurobipy-pandas)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/gurobipy-pandas.svg)](https://pypi.org/project/gurobipy-pandas)
[![Tests](https://github.com/Gurobi/gurobipy-pandas/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/Gurobi/gurobipy-pandas/actions/workflows/test.yml?query=branch%3Amain++)
[![Docs](https://readthedocs.com/projects/gurobi-optimization-gurobipy-pandas/badge/?version=latest)](https://gurobipy-pandas.readthedocs.io/en/stable/)

# gurobipy-pandas: Convenience wrapper for building optimization models from pandas data

`gurobipy-pandas` is a convenient (optional) wrapper to connect pandas with gurobipy. It enables users to more easily and efficiently build mathematical optimization models from data stored in DataFrames and Series, and to read solutions back directly as pandas objects.

`gurobipy-pandas` is aimed at experienced pandas users who are familiar with methods to transform, group, and aggregate data stored in dataframes. It expects some familiarity with optimization modelling, but does not require deep experience with gurobipy.

## Features

`gurobipy-pandas` allows users to:

- create gurobipy variables tied to the index of a series or dataframe
- construct constraints row-wise using algebraic expressions
- read model solutions and constraint slacks natively as pandas series

## Installation

```console
pip install gurobipy-pandas
```

## Dependencies

- [gurobipy: Python modelling interface for the Gurobi Optimizer](https://pypi.org/project/gurobipy/)
- [pandas: powerful Python data analysis toolkit](https://pypi.org/project/pandas/)

## Documentation

Full documentation for `gurobipy-pandas` is hosted on [readthedocs](https://gurobipy-pandas.readthedocs.io/en/stable/).

## License

`gurobipy-pandas` is distributed under the terms of the [Apache License 2.0](https://spdx.org/licenses/Apache-2.0.html).

## Contact Us

For questions related to using gurobipy-pandas please use the [Gurobi Community Forum](https://support.gurobi.com/hc/en-us/community/topics/10373864542609-GitHub-Projects>).

For reporting bugs, issues and feature requests, specific to `gurobipy-pandas`, please [open an issue](https://github.com/Gurobi/gurobipy-pandas/issues).

If you encounter issues with Gurobi or `gurobipy` please contact [Gurobi Support](https://support.gurobi.com/hc/en-us).

## Contributors

- Simon Bowly (maintainer)
- Robert Luce (maintainer)
- [Irv Lustig](https://github.com/Dr-Irv) [Princeton Consultants](http://www.princetonoptimization.com)
- [Robert Randall](https://github.com/rrandall1471) [Princeton Consultants](http://www.princetonoptimization.com)

## Webinar

Slides for the 2023 webinars presenting this package can be found at [webinar/webinar.ipynb](https://github.com/Gurobi/gurobipy-pandas/blob/main/webinar/webinar.ipynb). The notebook will be presented as RISE slides, but can also be executed in Jupyter.
