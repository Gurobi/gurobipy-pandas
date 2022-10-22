"""
The index mappers convert indexes and multi indexes to iterables of values
or tuples with optional formatting applied.

The main use case is applying the default mapper, which will produce LP file
compliant strings.

These are not called directly by users, rather users should pass their own
mapper in to var/constr adder methods if they want to change the behaviour.
"""

from functools import partial

import pandas as pd


def create_mapper(arg):
    """Entry point for index mapping/formatting. Takes an argument the user
    would pass to top level functions, and returns a callable which should
    be applied to indexes before using them to create var/constr names."""
    if arg == "disable":
        # Pass through unchanged
        return lambda index: index
    elif arg == "default":
        # Apply default mapping at every level of the index
        return partial(_map_index_entries, mapper=_default_mapper)
    elif callable(arg):
        # Apply the callable at every level of the index
        return partial(_map_index_entries, mapper=arg)
    else:
        # Expects a dict-like object. Adds the default mapper as a fallback
        # if needed. Mappers are applied level-wise by names in the dict.
        arg = dict(arg)
        if None not in arg:
            arg[None] = _default_mapper
        return partial(_map_index_entries, mapper=arg)


def _default_mapper(index):
    """Level mapper to be applied by default. Just does basic cleanup to avoid
    LP format issues."""
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


def _map_index_entries(index: pd.Index, mapper):
    """Convert an index to a list of values (single) or tuples (multi), with
    string conversions where needed to support clean variable and constraint
    naming.
    """
    assert isinstance(index, pd.Index)

    if mapper is None:
        # Nothing to do
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
        # if isinstance(index, pd.MultiIndex):
        levels = [index.get_level_values(i) for i in range(index.nlevels)]
        mapped_levels = []

        # This function is not used directly, but wrapped by create_mapper,
        # which will always add a fallback 'None' key.
        default_map_func = mapper[None]

        for level in levels:
            if level.name in mapper:
                map_func = mapper[level.name]
            else:
                map_func = default_map_func

            if map_func is None:
                mapped_levels.append(level)
            else:
                mapped_levels.append(map_func(level))

        if isinstance(index, pd.MultiIndex):
            return pd.MultiIndex.from_arrays(mapped_levels)
        else:
            assert len(levels) == 1
            return mapped_levels[0]
