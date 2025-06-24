from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from osmatching.validation import ValidationType, parse_and_validate_config


@dataclass
class MatchConfig:
    matches_per_case: int | None = None
    match_variables: dict | None = None
    index_date_variable: str | None = None
    closest_match_variables: list[str] = field(default_factory=list)
    date_exclusion_variables: dict[Any, Any] = field(default_factory=dict)
    min_matches_per_case: int = 0
    generate_match_index_date: str = ""
    match_index_date_offset: tuple[str, str, int] | None = None
    output_suffix: str = ""
    indicator_variable_name: str = "case"
    output_path: Path = Path("output")
    drop_cases_from_matches: bool = False
    output_format: str = "arrow"
    validated: bool = False

    @classmethod
    def from_dict(cls, config_dict):
        output_path = Path(config_dict.pop("output_path", None) or "output")
        closest_match_variables = config_dict.pop("closest_match_variables", None) or []
        date_exclusion_variables = (
            config_dict.pop("date_exclusion_variables", None) or {}
        )
        return cls(
            **config_dict,
            output_path=output_path,
            closest_match_variables=closest_match_variables,
            date_exclusion_variables=date_exclusion_variables,
        )

    @staticmethod
    def required_vars():
        return ["matches_per_case", "match_variables", "index_date_variable"]


DATAFRAME_READER: dict[str, tuple] = {
    ".csv": ("read_csv", {"engine": "pyarrow"}),
    ".arrow": ("read_feather", {}),
}
DATAFRAME_WRITER: dict[str, str] = {".csv": "to_csv", ".arrow": "to_feather"}


def load_config(match_config: dict) -> MatchConfig:
    """
    Converts a match configuration dictionary to a MatchConfig
    object.

    Args:
        match_config (dict): dictionary of the match configuration
            taken from json

    Returns:
        tuple of MatchConfig, errors (dict)
        - MatchConfig: Configuration instance to be passed to entry point
        - errors: a dict of MatchConfig fields tp validation errors
    """
    return parse_and_validate_config(MatchConfig.from_dict(match_config))


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


def report_validation_errors(errors: dict[str, list], validation_type: ValidationType):
    print(f"\nErrors were found in the provided {validation_type.value}:")
    for key, errorlist in errors.items():
        print(f"\n  {key}")
        for error in errorlist:
            print(f"  * {error}")
    print("\nPlease correct these errors and try again")
