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
    """Mapper to be applied by default by var/constr adders. Just does basic
    cleanup to avoid LP format issues."""
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


def map_index_entries(index: pd.Index, mapper):
    """Convert an index to a list of values (single) or tuples (multi), with
    string conversions where needed to support clean variable and constraint
    naming.
    """
    assert isinstance(index, pd.Index)

    if mapper is None:
        # Don't do any formatting.
        return index

    elif callable(mapper):
        # Apply mapper to index. If a multi-index, apply by level and reconstruct
        if isinstance(index, pd.MultiIndex):
            levels = [index.get_level_values(i) for i in range(index.nlevels)]
            mapped_levels = [mapper(level) for level in levels]
            return pd.MultiIndex.from_arrays(mapped_levels)
        else:
            return mapper(index)

    else:
        # mapper is a mapping from index level names -> mapper functions
        assert isinstance(index, pd.MultiIndex)
        levels = [index.get_level_values(i) for i in range(index.nlevels)]
        mapped_levels = []
        for level in levels:
            if level.name in mapper:
                map_func = mapper[level.name]
                if map_func is None:
                    mapped_levels.append(level)
                else:
                    mapped_levels.append(map_func(level))
            else:
                mapped_levels.append(default_mapper(level))
        return pd.MultiIndex.from_arrays(mapped_levels)
