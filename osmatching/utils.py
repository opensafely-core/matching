from pathlib import Path
from typing import Any

import pandas as pd


DEFAULTS = {
    "closest_match_variable": None,
    "date_exclusion_variables": None,
    "min_matches_per_case": 0,
    "replace_match_index_date_with_case": None,
    "output_suffix": "",
    "indicator_variable_name": "case",
    "output_path": "output",
    "drop_cases_from_matches": False,
    "output_format": "arrow",
}


DATAFRAME_READER: dict[str, tuple] = {
    ".csv": ("read_csv", {"engine": "pyarrow"}),
    ".arrow": ("read_feather", {}),
}
DATAFRAME_WRITER: dict[str, str] = {".csv": "to_csv", ".arrow": "to_feather"}


def load_config(match_config: dict) -> dict[str, Any]:
    """
    Takes in match configuration and changes these key-value pairs
    where indicated by the match config. All other key-value pairs
    are left as default values

    Args:
        match_config (dict): dictionary of the match configuration
            taken from json

    Returns:
        dict (cfg): Configuration dictionary to be passed to entry point.
    """
    cfg = DEFAULTS.copy()
    cfg.update(match_config)
    return cfg


def file_suffix(file_path: Path):
    return "".join(file_path.suffixes)


def load_dataframe(file_path: Path):
    suffix = file_suffix(file_path).split(".gz")[0]
    read_method, kwargs = DATAFRAME_READER[suffix]
    dataframe = getattr(pd, read_method)(file_path, **kwargs)
    dataframe.set_index("patient_id", inplace=True)
    return dataframe


def write_output_file(df, file_path):
    suffix = file_suffix(file_path).split(".gz")[0]
    # feather requires that we reset the index before writing
    writer = getattr(df.reset_index(), DATAFRAME_WRITER[suffix])
    writer(file_path)
