"""Main program that does matching"""

import copy
from datetime import datetime
from typing import Optional

import pandas as pd

from osmatching.utils import MatchConfig, report_validation_errors, write_output_file
from osmatching.validation import (
    ValidationType,
    parse_and_validate_config,
    validate_input_data,
)


NOT_PREVIOUSLY_MATCHED = -9


def import_data(
    cases: pd.DataFrame,
    matches: pd.DataFrame,
    match_config: MatchConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Sets the correct data types for the matching variables.
    """
    assert match_config.match_variables is not None  # guaranteed by validation
    match_variables = copy.deepcopy(match_config.match_variables)
    ## Set data types for matching variables
    month_only = []
    for var, match_type in match_variables.items():
        if match_type == "category":
            # arrow files already have category types, so we don't need to convert them
            if cases[var].dtype.name == "category":
                continue
            cases[var] = cases[var].astype("category")
            matches[var] = matches[var].astype("category")
        ## Extract month from month_only variables
        elif match_type == "month_only":
            month_only.append(var)
            # Ensure our datetimes are strings before slicing
            cases[var] = cases[var].astype("str")
            matches[var] = matches[var].astype("str")
            cases[f"{var}_m"] = cases[var].str.slice(start=5, stop=7).astype("category")
            matches[f"{var}_m"] = (
                matches[var].str.slice(start=5, stop=7).astype("category")
            )
    for var in month_only:
        del match_variables[var]
        match_variables[f"{var}_m"] = "category"

    match_config.match_variables = match_variables

    ## Format exclusion variables as dates
    for var in match_config.date_exclusion_variables:
        cases[var] = pd.to_datetime(cases[var])
        matches[var] = pd.to_datetime(matches[var])

    # If there is no index_date_variable in the matches df, add an empty column for it
    if match_config.index_date_variable not in matches.columns:
        matches[match_config.index_date_variable] = ""

    ## Format index dates as date
    cases[match_config.index_date_variable] = pd.to_datetime(
        cases[match_config.index_date_variable]
    )
    matches[match_config.index_date_variable] = pd.to_datetime(
        matches[match_config.index_date_variable]
    )

    return cases, matches


def add_variables(
    cases: pd.DataFrame, matches: pd.DataFrame, indicator_variable_name: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Adds the following variables to the case and match tables:
    set_id - in the final table, this will be identify groups of matched cases
             and matches. Here it is set to the patient ID for cases, and a
             magic number denoting that a person has not been previously matched
             for matches.
    indicator_variable_name - a binary variable to indicate whether they are a case or
                              match. Default name is "case" but this can be changed as needed
    """
    cases["set_id"] = cases.index
    matches["set_id"] = NOT_PREVIOUSLY_MATCHED
    cases[indicator_variable_name] = 1
    matches[indicator_variable_name] = 0
    return cases, matches


def get_bool_index(
    match_type: str, value: int, match_var: str, matches: pd.DataFrame
) -> pd.Series:
    """
    Compares the value in the given case variable to the variable in
    the match dataframe, to generate a boolean Series. Comparisons vary
    according to the matching specification.
    """
    if match_type == "category":
        return matches[match_var] == value
    else:
        assert isinstance(match_type, int), "Unknown matching type '{match_type}'"
        return abs(matches[match_var] - value) <= match_type


def pre_calculate_indices(
    cases: pd.DataFrame, matches: pd.DataFrame, match_variables: dict
) -> dict[str, str]:
    """
    Loops over each of the values in the case table for each of the match
    variables and generates a boolean Series against the match table. These are
    returned in a dict.
    """
    indices_dict: dict = {}
    for match_var in match_variables:
        match_type = match_variables[match_var]
        indices_dict[match_var] = {}

        values = cases[match_var].unique()
        for value in values:
            index = get_bool_index(match_type, value, match_var, matches)
            indices_dict[match_var][value] = index
    return indices_dict


def get_eligible_matches(
    case_row: pd.DataFrame,
    matches: pd.DataFrame,
    match_variables: dict,
    indices: pd.DataFrame,
) -> pd.DataFrame:
    """
    Loops over the match_variables and combines the boolean Series
    from pre_calculate_indices into a single bool Series. Also removes previously
    matched patients.
    """
    eligible_matches = pd.Series(data=True, index=matches.index)
    for match_var in match_variables:
        variable_bool = indices[match_var][case_row[match_var]]
        eligible_matches = eligible_matches & variable_bool

    not_previously_matched = matches["set_id"] == NOT_PREVIOUSLY_MATCHED
    eligible_matches = eligible_matches & not_previously_matched
    return eligible_matches


def date_exclusions(df1: pd.DataFrame, date_exclusion_variables: dict, index_date: str):
    """
    Loops over the exclusion variables and creates a boolean Series corresponding
    to where there are exclusion variables that occur before the index date.
    index_date can be either a single value, or a pandas Series whose index
    matches df1.
    """
    exclusions = pd.Series(data=False, index=df1.index)
    for exclusion_var, before_after in date_exclusion_variables.items():
        match before_after:
            case "before":
                variable_bool = df1[exclusion_var] < index_date
            case "after":
                variable_bool = df1[exclusion_var] > index_date
            case _:  # pragma: no cover
                # This should be caught in config validation so we should never get here
                assert False, "Invalid date exclusion type"
        exclusions = exclusions | variable_bool
    return exclusions


def greedily_pick_matches(
    matches_per_case: int,
    matched_rows: pd.DataFrame,
    case_row: pd.DataFrame,
    closest_match_variables: list,
) -> pd.Index:
    """
    Cuts the eligible_matches list to the number of matches specified. This is a
    greedy matching method, so if closest_match_variables are specified, it picks the
    values that deviate least from the case values (prioritised in the order they are
    specified). If there are more than matches_per_case matches who are identical,
    matches are randomly sampled.
    """
    # Ensure we're working with a copy of the matched_rows df
    matched_rows = matched_rows.copy()
    if closest_match_variables:
        sort_cols: list = []
        for var in closest_match_variables:
            matched_rows[f"{var}_delta"] = abs(matched_rows[var] - case_row[var])
            sort_cols.append(f"{var}_delta")
        matched_rows = matched_rows.nsmallest(matches_per_case, sort_cols, keep="all")

    if len(matched_rows) > matches_per_case:
        matched_rows = matched_rows.sample(n=matches_per_case, random_state=123)
    return matched_rows.index


def get_date_offset(offset: tuple[str, str, int]) -> Optional[pd.DataFrame]:
    """
    Converts the tuple of unit and length given by match_index_date_offset
    to return a pr.DateOffset of the appropriate length.
    """
    unit, _, length = offset
    if unit == "no_offset":
        return None
    else:
        return pd.DateOffset(**{unit: length})


def match(
    case_df: str,
    match_df: str,
    match_config: MatchConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Wrapper function that calls functions to:
    - import data
    - find eligible matches
    - pick the correct number of randomly allocated matches
    - make exclusions that are based on index date
      - (this is not currently possible in a study definition, and will only ever be possible
        during matching for studies where the match index date comes from the case)
    - set the set_id as that of the case_id (this excludes them from being matched later)
    - set the index date of the match as that of the case (where desired)
    - save the results in the specified output format
    """
    # validate the config if we haven't already
    if not match_config.validated:
        match_config, errors = parse_and_validate_config(match_config)
        if errors:
            report_validation_errors(errors, validation_type=ValidationType.CONFIG)
            raise ValueError("There was an error in one or more config values")

    errors = validate_input_data(case_df, match_df, match_config)
    if errors:
        report_validation_errors(errors, validation_type=ValidationType.DATA)
        raise ValueError("Errors encountered in the input datasets")

    # Guaranteed by validation; assert not None to satisfy mypy
    assert match_config.match_variables is not None
    assert match_config.matches_per_case is not None

    # Make sure the output path exists
    match_config.output_path.mkdir(parents=True, exist_ok=True)

    report_path = (
        match_config.output_path / f"matching_report{match_config.output_suffix}.txt"
    )

    def matching_report(text_list: list, erase: bool = False) -> None:
        if erase and report_path.is_file():
            report_path.unlink()

        text_to_write = "\n".join(text_list)
        text_to_write += "\n\n"
        with report_path.open("a") as report_file:
            report_file.write(text_to_write)
        print(text_to_write)

    matching_report(
        [f"Matching started at: {datetime.now()}"],
        erase=True,
    )

    # Import_data; note match_config.match_variables may be updated with date variables that
    # are converted to month-only
    cases, matches = import_data(
        case_df,
        match_df,
        match_config,
    )

    matching_report(
        [
            "Data import:",
            f"Completed {datetime.now()}",
            f"Cases    {len(cases)}",
            f"Matches  {len(matches)}",
        ],
    )

    ## Drop cases from match population if specified
    if match_config.drop_cases_from_matches:
        matches = matches.drop(cases.index, errors="ignore")

    matching_report(
        [
            "Dropping cases from matches:",
            f"Completed {datetime.now()}",
            f"Cases    {len(cases)}",
            f"Matches  {len(matches)}",
        ]
    )

    ## Add set_id variable
    cases, matches = add_variables(cases, matches, match_config.indicator_variable_name)

    indices = pre_calculate_indices(cases, matches, match_config.match_variables)
    matching_report([f"Completed pre-calculating indices at {datetime.now()}"])

    if match_config.match_index_date_offset:
        date_offset = get_date_offset(match_config.match_index_date_offset)

    if match_config.date_exclusion_variables:
        case_exclusions = date_exclusions(
            cases,
            match_config.date_exclusion_variables,
            cases[match_config.index_date_variable],
        )
        cases = cases.loc[~case_exclusions]
        matching_report(
            [
                "Date exclusions for cases:",
                f"Completed {datetime.now()}",
                f"Cases    {len(cases)}",
                f"Matches  {len(matches)}",
            ]
        )

    ## Sort cases by index date
    cases = cases.sort_values(match_config.index_date_variable)

    for case_id, case_row in cases.iterrows():
        ## Get eligible matches
        eligible_matches = get_eligible_matches(
            case_row, matches, match_config.match_variables, indices
        )
        matched_rows = matches.loc[eligible_matches]

        ## Determine match index date
        if not match_config.match_index_date_offset:
            index_date = matched_rows[match_config.index_date_variable]
        else:
            unit, offset_type, _ = match_config.match_index_date_offset

            if unit == "no_offset":
                index_date = case_row[match_config.index_date_variable]
            elif offset_type == "earlier":
                index_date = case_row[match_config.index_date_variable] - date_offset
            elif offset_type == "later":
                index_date = case_row[match_config.index_date_variable] + date_offset
            else:
                assert False, f"Date offset type '{offset_type}' not recognised"

        ## Index date based match exclusions (faster to do this after get_eligible_matches)
        if match_config.date_exclusion_variables:
            exclusions = date_exclusions(
                matched_rows, match_config.date_exclusion_variables, index_date
            )
            matched_rows = matched_rows.loc[~exclusions]

        ## Pick random matches
        matched_rows = greedily_pick_matches(
            match_config.matches_per_case,
            matched_rows,
            case_row,
            match_config.closest_match_variables,
        )

        ## Report number of matches for each case
        num_matches = len(matched_rows)
        cases.loc[case_id, "match_counts"] = num_matches
        ## Label matches with case ID if there are enough
        if num_matches >= match_config.min_matches_per_case:
            matches.loc[matched_rows, "set_id"] = case_id

        ## Set index_date of the match where needed
        if match_config.generate_match_index_date:
            matches.loc[matched_rows, match_config.index_date_variable] = index_date

    ## Drop unmatched cases/matches
    matched_cases = cases.loc[
        cases["match_counts"] >= match_config.min_matches_per_case
    ]
    matched_matches = matches.loc[matches["set_id"] != NOT_PREVIOUSLY_MATCHED]

    ## Describe population differences
    scalar_comparisons = compare_populations(
        matched_cases, matched_matches, match_config.closest_match_variables
    )

    matching_report(
        [
            "After matching:",
            f"Completed {datetime.now()}",
            f"Cases    {len(matched_cases)}",
            f"Matches  {len(matched_matches)}\n",
            "Number of available matches per case:",
            cases["match_counts"].value_counts().to_string(),
        ]
        + scalar_comparisons
    )

    ## Write output files
    file_suffix_ext = f"{match_config.output_suffix}.{match_config.output_format}"
    write_output_file(
        matched_cases, match_config.output_path / f"matched_cases{file_suffix_ext}"
    )
    write_output_file(
        matched_matches, match_config.output_path / f"matched_matches{file_suffix_ext}"
    )
    combined = pd.concat(
        [df for df in [matched_cases, matched_matches] if not df.empty]
    )
    write_output_file(
        combined, match_config.output_path / f"matched_combined{file_suffix_ext}"
    )

    # return the matched dataframes, for ease of testing
    return matched_cases, matched_matches


def compare_populations(
    matched_cases: pd.DataFrame,
    matched_matches: pd.DataFrame,
    closest_match_variables: list,
) -> pd.DataFrame:
    """
    Takes the list of closest_match_variables and describes each of them for the matched
    case and matched control population, so that their similarity can be checked.
    Returns a list strings corresponding to the rows of the describe() test_data, to be
    passed to matching_report(). Returns empty list if no closest_match_variables are
    specified.
    """
    scalar_comparisons = []
    for var in closest_match_variables:
        scalar_comparisons.extend(
            [
                f"\n{var} comparison:",
                "Cases:",
                matched_cases[var].describe().to_string(),
                "Matches:",
                matched_matches[var].describe().to_string(),
            ]
        )
    return scalar_comparisons
