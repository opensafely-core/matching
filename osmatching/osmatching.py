import os
import copy
from datetime import datetime
import pandas as pd

NOT_PREVIOUSLY_MATCHED = -9


def import_csvs(
    case_csv,
    match_csv,
    match_variables,
    date_exclusion_variables,
    index_date_variable,
    output_path,
    replace_match_index_date_with_case=None,
):
    """
    Imports the two csvs specified under case_csv and match_csv.
    Also sets the correct data types for the matching variables.
    """
    cases = pd.read_csv(
        os.path.join(output_path, f"{case_csv}.csv"),
        index_col="patient_id",
    )
    matches = pd.read_csv(
        os.path.join(output_path, f"{match_csv}.csv"),
        index_col="patient_id",
    )

    ## Set data types for matching variables
    month_only = []
    for var, match_type in match_variables.items():
        if match_type == "category":
            cases[var] = cases[var].astype("category")
            matches[var] = matches[var].astype("category")
        ## Extract month from month_only variables
        elif match_type == "month_only":
            month_only.append(var)
            cases[f"{var}_m"] = cases[var].str.slice(start=5, stop=7).astype("category")
            matches[f"{var}_m"] = (
                matches[var].str.slice(start=5, stop=7).astype("category")
            )
    for var in month_only:
        del match_variables[var]
        match_variables[f"{var}_m"] = "category"

    ## Format exclusion variables as dates
    if date_exclusion_variables is not None:
        for var in date_exclusion_variables:
            cases[var] = pd.to_datetime(cases[var])
            matches[var] = pd.to_datetime(matches[var])
    ## Format index date as date
    cases[index_date_variable] = pd.to_datetime(cases[index_date_variable])
    if replace_match_index_date_with_case is None:
        matches[index_date_variable] = pd.to_datetime(matches[index_date_variable])

    return cases, matches


def add_variables(cases, matches, indicator_variable_name="case"):
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


def get_bool_index(match_type, value, match_var, matches):
    """
    Compares the value in the given case variable to the variable in
    the match dataframe, to generate a boolean Series. Comparisons vary
    according to the matching specification.
    """
    if match_type == "category":
        bool_index = matches[match_var] == value
    elif isinstance(match_type, int):
        bool_index = abs(matches[match_var] - value) <= match_type
    else:
        raise Exception(f"Matching type '{match_type}' not yet implemented")
    return bool_index


def pre_calculate_indices(cases, matches, match_variables):
    """
    Loops over each of the values in the case table for each of the match
    variables and generates a boolean Series against the match table. These are
    returned in a dict.
    """
    indices_dict = {}
    for match_var in match_variables:
        match_type = match_variables[match_var]
        indices_dict[match_var] = {}

        values = cases[match_var].unique()
        for value in values:
            index = get_bool_index(match_type, value, match_var, matches)
            indices_dict[match_var][value] = index
    return indices_dict


def get_eligible_matches(case_row, matches, match_variables, indices):
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


def date_exclusions(df1, date_exclusion_variables, index_date):
    """
    Loops over the exclusion variables and creates a boolean Series corresponding
    to where there are exclusion variables that occur before the index date.
    index_date can be either a single value, or a pandas Series whose index
    matches df1.
    """
    exclusions = pd.Series(data=False, index=df1.index)
    for exclusion_var, before_after in date_exclusion_variables.items():
        if before_after == "before":
            variable_bool = df1[exclusion_var] < index_date
        elif before_after == "after":
            variable_bool = df1[exclusion_var] > index_date
        else:
            raise Exception(f"Date exclusion type '{exclusion_var}' invalid")
        exclusions = exclusions | variable_bool
    return exclusions


def greedily_pick_matches(
    matches_per_case,
    matched_rows,
    case_row,
    closest_match_variables=None,
):
    """
    Cuts the eligible_matches list to the number of matches specified. This is a
    greedy matching method, so if closest_match_variables are specified, it picks the
    values that deviate least from the case values (prioritised in the order they are
    specified). If there are more than matches_per_case matches who are identical,
    matches are randomly sampled.
    """
    if closest_match_variables is not None:
        sort_cols = []
        for var in closest_match_variables:
            matched_rows[f"{var}_delta"] = abs(matched_rows[var] - case_row[var])
            sort_cols.append(f"{var}_delta")
        matched_rows = matched_rows.nsmallest(matches_per_case, sort_cols, keep="all")

    if len(matched_rows) > matches_per_case:
        matched_rows = matched_rows.sample(n=matches_per_case, random_state=123)
    return matched_rows.index


def get_date_offset(offset_str):
    """
    Parses the string given by replace_match_index_date_with_case
    to determine the unit and length of offset.
    Returns a pr.DateOffset of the appropriate length.
    """
    if offset_str == "no_offset":
        offset = None
    else:
        length = int(offset_str.split("_")[0])
        unit = offset_str.split("_")[1]
        if unit in ("year", "years"):
            offset = pd.DateOffset(years=length)
        elif unit in ("month", "months"):
            offset = pd.DateOffset(months=length)
        elif unit in ("day", "days"):
            offset = pd.DateOffset(days=length)
        else:
            raise Exception(f"Date offset '{unit}' not implemented")
    return offset


def match(
    case_csv,
    match_csv,
    matches_per_case,
    match_variables,
    index_date_variable,
    closest_match_variables=None,
    date_exclusion_variables=None,
    min_matches_per_case=0,
    replace_match_index_date_with_case=None,
    indicator_variable_name="case",
    output_suffix="",
    output_path="output",
    drop_cases_from_matches=False
):
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
    - save the results as a csv
    """
    if min_matches_per_case > matches_per_case:
        raise ValueError("min_matches_per_case cannot be greater than matches_per_case")

    report_path = os.path.join(
        output_path,
        f"matching_report{output_suffix}.txt",
    )

    def matching_report(text_to_write, erase=False):
        if erase and os.path.isfile(report_path):
            os.remove(report_path)
        with open(report_path, "a") as txt:
            for line in text_to_write:
                txt.writelines(f"{line}\n")
                print(line)
            txt.writelines("\n")
            print("\n")

    matching_report(
        [f"Matching started at: {datetime.now()}"],
        erase=True,
    )

    ## Deep copy match_variables
    match_variables = copy.deepcopy(match_variables)

    ## Import_data
    cases, matches = import_csvs(
        case_csv,
        match_csv,
        match_variables,
        date_exclusion_variables,
        index_date_variable,
        output_path,
        replace_match_index_date_with_case,
    )

    matching_report(
        [
            "CSV import:",
            f"Completed {datetime.now()}",
            f"Cases    {len(cases)}",
            f"Matches  {len(matches)}",
        ],
    )

    ## Drop cases from match population if specified
    if drop_cases_from_matches:
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
    cases, matches = add_variables(cases, matches, indicator_variable_name)

    indices = pre_calculate_indices(cases, matches, match_variables)
    matching_report([f"Completed pre-calculating indices at {datetime.now()}"])

    if replace_match_index_date_with_case is not None:
        offset_str = replace_match_index_date_with_case
        date_offset = get_date_offset(replace_match_index_date_with_case)

    if date_exclusion_variables is not None:
        case_exclusions = date_exclusions(
            cases, date_exclusion_variables, cases[index_date_variable]
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
    cases = cases.sort_values(index_date_variable)

    for case_id, case_row in cases.iterrows():
        ## Get eligible matches
        eligible_matches = get_eligible_matches(
            case_row, matches, match_variables, indices
        )
        matched_rows = matches.loc[eligible_matches]

        ## Determine match index date
        if replace_match_index_date_with_case is None:
            index_date = matched_rows[index_date_variable]
        else:
            if offset_str == "no_offset":
                index_date = case_row[index_date_variable]
            elif offset_str.split("_")[2] == "earlier":
                index_date = case_row[index_date_variable] - date_offset
            elif offset_str.split("_")[2] == "later":
                index_date = case_row[index_date_variable] + date_offset
            else:
                raise Exception(f"Date offset type '{offset_str}' not recognised")

        ## Index date based match exclusions (faster to do this after get_eligible_matches)
        if date_exclusion_variables is not None:
            exclusions = date_exclusions(
                matched_rows, date_exclusion_variables, index_date
            )
            matched_rows = matched_rows.loc[~exclusions]

        ## Pick random matches
        matched_rows = greedily_pick_matches(
            matches_per_case,
            matched_rows,
            case_row,
            closest_match_variables,
        )

        ## Report number of matches for each case
        num_matches = len(matched_rows)
        cases.loc[case_id, "match_counts"] = num_matches

        ## Label matches with case ID if there are enough
        if num_matches >= min_matches_per_case:
            matches.loc[matched_rows, "set_id"] = case_id

        ## Set index_date of the match where needed
        if replace_match_index_date_with_case is not None:
            matches.loc[matched_rows, index_date_variable] = index_date

    ## Drop unmatched cases/matches
    matched_cases = cases.loc[cases["match_counts"] >= min_matches_per_case]
    matched_matches = matches.loc[matches["set_id"] != NOT_PREVIOUSLY_MATCHED]

    ## Describe population differences
    scalar_comparisons = compare_populations(
        matched_cases, matched_matches, closest_match_variables
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

    ## Write to csvs
    matched_cases.to_csv(os.path.join(output_path, f"matched_cases{output_suffix}.csv"))
    matched_matches.to_csv(
        os.path.join(output_path, f"matched_matches{output_suffix}.csv")
    )
    appended = matched_cases.append(matched_matches)
    appended.to_csv(os.path.join(output_path, f"matched_combined{output_suffix}.csv"))


def compare_populations(matched_cases, matched_matches, closest_match_variables):
    """
    Takes the list of closest_match_variables and describes each of them for the matched
    case and matched control population, so that their similarity can be checked.
    Returns a list strings corresponding to the rows of the describe() output, to be
    passed to matching_report(). Returns empty list if no closest_match_variables are
    specified.
    """
    scalar_comparisons = []
    if closest_match_variables is not None:
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
