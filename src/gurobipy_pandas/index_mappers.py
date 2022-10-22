"""
The index mappers convert indexes and multi indexes to iterables of values
or tuples with optional formatting applied.

The main use case is applying the default mapper, which will produce LP file
compliant strings.

These are not called directly by users, rather users should pass their own
mapper in to var/constr adder methods if they want to change the behaviour.
"""

import pandas as pd


def default_mapper(index):
    """Mapper to be applied by default by var/constr adders"""
    if pd.api.types.is_integer_dtype(index):
        # Integers will always be string-formatted sanely later, no need to
        # do any heavy string manipulation here.
        return index
    elif pd.api.types.is_datetime64_any_dtype(index):
        # Map to an LP file friendly format
        mapped = pd.Series(index.values).dt.strftime("%Y_%m_%dT%H_%M_%S")
        return mapped.values
    else:
        return index.map(str).str.replace(r"[\+\-\*\^\:\s]+", "_", regex=True)


def map_index_entries(index: pd.Index, mapper=None):
    """Convert an index to a list of values (single) or tuples (multi), with
    string conversions where needed to support clean variable and constraint
    naming.
    """
    assert isinstance(index, pd.Index)

    if mapper is None:
        return index
    elif callable(mapper):
        # Apply mapper to index. If a multi-index, apply by level and reconstruct
        if isinstance(index, pd.MultiIndex):
            levels = [index.get_level_values(i) for i in range(index.nlevels)]
            mapped_levels = [mapper(level) for level in levels]
            return pd.MultiIndex.from_arrays(mapped_levels)
        else:
            return mapper(index)
