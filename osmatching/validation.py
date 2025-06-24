from collections import defaultdict
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd


if TYPE_CHECKING:  # pragma: no cover
    # We are avoiding circular dependencies by using forward references for
    # type annotations where necessary, and this check so that type-checking
    # imports are not executed at runtime.
    # https://peps.python.org/pep-0484/#forward-references
    # https://mypy.readthedocs.io/en/stable/runtime_troubles.html#import-cycles
    from osmatching.utils import MatchConfig


class ValidationType(Enum):
    CONFIG = "configuration"
    DATA = "input data"


def validate_required_vars(config):
    for var in config.required_vars():
        if getattr(config, var) is None:
            yield var


def replace_none_with_default(config, name, default):
    if getattr(config, name) is None:
        setattr(config, name, default)


def validate_date_exclusions(date_exclusion_variables):
    for exclusion_var, when in date_exclusion_variables.items():
        if when not in ["before", "after"]:
            yield exclusion_var, when


def validate_match_variables(match_variables):
    """
    validate types for match variables - currently category or scalar (int) only
    Note that month_only matches are converted to month categories
    """
    if match_variables is None:
        return

    for match_var, match_type in match_variables.items():
        if match_type in ["category", "month_only"]:
            continue
        if not isinstance(match_type, int):
            yield match_var, match_type


def get_match_index_date_offset(offset_str):
    match offset_str:
        case "" | None:
            return None
        case "no_offset":
            return ("no_offset", "", 0)
        case _:
            try:
                length, unit, offset_type = offset_str.split("_")
                length = int(length)
            except ValueError:
                raise ValueError(f"Date offset '{offset_str}' could not be parsed")

            unit = unit.strip("s") + "s"
            if unit not in ["years", "months", "days"]:
                raise ValueError(f"Date offset units '{unit}' not implemented")

            if offset_type not in ["earlier", "later"]:
                raise ValueError(f"Date offset type '{offset_type}' not implemented")

            return (unit, offset_type, length)


def parse_and_validate_config(config: "MatchConfig"):
    """
    Validate config values where possible in advance of any calculations
    and convert replace_match_index_date_with_case strings into component
    args for later use.
    """
    # ensure output_path is a Path
    config.output_path = Path(config.output_path)

    errors = defaultdict(list)

    for missing in validate_required_vars(config):
        errors[missing].append(f"Not found: `{missing}` is a required config variable")

    # validate min matches per case
    if (
        config.matches_per_case is not None
        and config.min_matches_per_case > config.matches_per_case
    ):
        errors["min_matches_per_case"].append(
            f"`min_matches_per_case` ({config.min_matches_per_case}) cannot be greater than `matches_per_case` ({config.matches_per_case})"
        )

    # ensure we don't have None values where we expect empty lists/dicts
    replace_none_with_default(config, "closest_match_variables", [])
    replace_none_with_default(config, "date_exclusion_variables", {})

    # validate date exclusion types
    for exclusion_var, invalid_when in validate_date_exclusions(
        config.date_exclusion_variables
    ):
        errors["date_exclusion_variables"].append(
            f"Invalid exclusion type '{invalid_when}' for variable '{exclusion_var}'. Allowed types are 'before' or 'after'"
        )

    # Validate that match_variable are of allowed types
    for match_var, invalid_type in validate_match_variables(config.match_variables):
        errors["match_variables"].append(
            f"Invalid match type '{invalid_type}' for variable `{match_var}`. Allowed are 'category', 'month_only', and integers."
        )

    # validate offset units for replace_match_index_date_with_case
    # and populate the match_index_date_offset tuple
    try:
        config.match_index_date_offset = get_match_index_date_offset(
            config.generate_match_index_date
        )
    except ValueError as error:
        errors["generate_match_index_date"] = [str(error)]

    # Flag this config as validated. We expect that match() will only be called from the
    # command line, which will always call this method to parse and validate the provided config
    # dict. However, in the event that the module is used from a shell, we may need to check
    # that it has been validated and re-validate if necessary.
    config.validated = True
    return config, errors


def validate_input_data(
    cases_df: pd.DataFrame, matches_df: pd.DataFrame, config: "MatchConfig"
):
    """
    Perfom some basic checks on the input dataframes before we start the calculations.
    These checks just ensure that we have the appropriate columns present in the two
    datasets. We don't yet perform any column type validation here.

    1) config.index_date_variable must be a column in cases_df
    2) config.index_date_variable must be present in matches_df *unless*
       config.generate_match_index_date is specified
    3) Any matching variables specified (excluding index_date_variable) must be present
       in both datasets, that is, any variables in:
       - match_variables.keys()
       - closest_match_variables
       - date_exclusion_variables.keys()
    """
    errors = defaultdict(list)

    if config.index_date_variable not in cases_df.columns:
        errors["index_date_variable"].append(
            f"column `{config.index_date_variable}` not found in cases dataset"
        )

    if (
        not config.generate_match_index_date
        and config.index_date_variable not in matches_df.columns
    ):
        errors["index_date_variable"].append(
            f"column `{config.index_date_variable}` not found in matches dataset (required when `generate_match_index_date` is not specified)"
        )

    # Explicit empty set for match_variables because it has a None default
    match_variables = set(config.match_variables) if config.match_variables else set()
    # required columns are any of those in match_variables, closest_match_variables and
    # date_exclusion_variables
    required_columns = match_variables.union(
        set(config.closest_match_variables), set(config.date_exclusion_variables)
    ) - {config.index_date_variable}

    def format_missing_columns(df):
        missing = required_columns - set(df.columns)
        if missing:
            return ", ".join([f"`{col}`" for col in sorted(missing)])

    columns_missing_from_cases = format_missing_columns(cases_df)
    if columns_missing_from_cases:
        errors["required_columns"].append(
            f"column(s) {columns_missing_from_cases} not found in cases dataset"
        )
    columns_missing_from_matches = format_missing_columns(matches_df)
    if columns_missing_from_matches:
        errors["required_columns"].append(
            f"column(s) {columns_missing_from_matches} not found in matches dataset"
        )

    return errors
