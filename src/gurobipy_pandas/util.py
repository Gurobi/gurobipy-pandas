import pandas as pd

from gurobipy_pandas.index_mappers import create_mapper

gppd_global_options = {"eager_updates": False}


def align_series(series: pd.Series, index: pd.Index, err_label: str):
    """
    Align :series with :index and return it.

    Raise a KeyError on any mismatch between the index of :series and :index
    (reordering is ok).

    Raise a ValueError if there is any missing data once the series is aligned.
    """

    if index is None:
        aligned = series
    else:
        if not index.sort_values().equals(series.index.sort_values()):
            raise KeyError(f"'{err_label}' series not aligned with index")
        aligned = series.loc[index]

    if aligned.isnull().any():
        raise ValueError(f"'{err_label}' series has missing values")

    return aligned


def _format_index(index):
    if isinstance(index, tuple):
        return ",".join(map(str, index))
    return str(index)


def create_names(prefix, index, index_formatter):
    mapper = create_mapper(index_formatter)
    return [f"{prefix}[{_format_index(entry)}]" for entry in mapper(index)]
