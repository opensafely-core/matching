from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from osmatching.osmatching import (
    NOT_PREVIOUSLY_MATCHED,
    date_exclusions,
    get_bool_index,
    get_date_offset,
    get_eligible_matches,
    greedily_pick_matches,
    match,
    pre_calculate_indices,
)
from osmatching.utils import MatchConfig, load_dataframe, parse_and_validate_config


FIXTURE_PATH = Path(__file__).parent / "test_data" / "fixtures"


@pytest.mark.parametrize(
    "input_cases_file,input_control_file,output_format,output_ext",
    [
        # default output ext is arrow
        ("input_cases.csv", "input_controls.csv", None, "arrow"),
        ("input_cases.csv.gz", "input_controls.csv.gz", "csv", "csv"),
        ("input_cases.csv", "input_controls.csv.gz", "csv.gz", "csv.gz"),
        ("input_cases.arrow", "input_controls.arrow", "arrow", "arrow"),
    ],
)
def test_match_smoke_test(
    tmp_path, input_cases_file, input_control_file, output_format, output_ext
):
    """Test that match() runs and produces a matching report and outputs."""

    test_matching = {
        "matches_per_case": 1,
        "match_variables": {
            "sex": "category",
            "age": 1,
            "region": "category",
            "indexdate": "month_only",
        },
        "closest_match_variables": ["age"],
        "index_date_variable": "indexdate",
        "date_exclusion_variables": {
            "died_date_ons": "before",
            "previous_event": "before",
        },
        "output_suffix": "_test",
        "output_path": tmp_path / "test_output",
    }
    if output_format is not None:
        test_matching["output_format"] = output_format

    match(
        case_df=load_dataframe(FIXTURE_PATH / input_cases_file),
        match_df=load_dataframe(FIXTURE_PATH / input_control_file),
        match_config=MatchConfig(**test_matching),
    )
    report_path = test_matching["output_path"] / "matching_report_test.txt"
    assert report_path.exists()
    report_text = report_path.read_text()
    # Check that we've got the expect first line
    assert "Matching started at:" in report_text
    # And the last block
    assert "Number of available matches per case" in report_text

    for output_file_stem in [
        "matched_cases_test",
        "matched_matches_test",
        "matched_combined_test",
    ]:
        output_filepath = (
            test_matching["output_path"] / f"{output_file_stem}.{output_ext}"
        )
        assert output_filepath.exists()

    # rerun and check that our report text is the same length (not identical, because
    # timestamps are different, but it has overwritten the file rather than appending on
    # a new run)
    match(
        case_df=load_dataframe(FIXTURE_PATH / input_cases_file),
        match_df=load_dataframe(FIXTURE_PATH / input_control_file),
        match_config=MatchConfig(**test_matching),
    )
    report_text1 = report_path.read_text()
    assert report_text1 != report_text
    assert len(report_text.split("\n")) == len(report_text1.split("\n"))


@pytest.mark.parametrize(
    "min_per_case,match_count",
    [
        (10, 3),
        (5, 4),
    ],
)
def test_match_min_matches_per_case(tmp_path, min_per_case, match_count):
    """Test that match() runs and produces a matching report and outputs."""
    test_matching = {
        "matches_per_case": 10,
        "min_matches_per_case": min_per_case,
        "match_variables": {
            "sex": "category",
            "age": 5,
        },
        "index_date_variable": "indexdate",
        "date_exclusion_variables": {
            "died_date_ons": "before",
            "previous_event": "before",
        },
        "output_suffix": "_test",
        "output_path": tmp_path / "test_output",
    }
    _, matched_matches = match(
        case_df=load_dataframe(FIXTURE_PATH / "input_cases.csv"),
        match_df=load_dataframe(FIXTURE_PATH / "input_controls.csv"),
        match_config=MatchConfig(**test_matching),
    )

    # set_id is the id of the case that this match matched
    unique_matched_cases = matched_matches.set_id.unique()
    assert len(unique_matched_cases) == match_count
    for set_id in unique_matched_cases:
        assert len(matched_matches[matched_matches.set_id == set_id]) >= min_per_case


def test_match_closest_match_variables_empty(tmp_path):
    """Test that match() runs and produces a matching report and outputs."""
    test_matching = {
        "matches_per_case": 1,
        "match_variables": {
            "sex": "category",
            "age": 5,
        },
        "index_date_variable": "indexdate",
        "output_suffix": "_test",
        "output_path": tmp_path / "test_output",
    }
    case_matches_1, matched_matches_1 = match(
        case_df=load_dataframe(FIXTURE_PATH / "input_cases.csv"),
        match_df=load_dataframe(FIXTURE_PATH / "input_controls.csv"),
        match_config=MatchConfig(**test_matching),
    )

    test_matching.update({"closest_match_variables": []})
    case_matches_2, matched_matches_2 = match(
        case_df=load_dataframe(FIXTURE_PATH / "input_cases.csv"),
        match_df=load_dataframe(FIXTURE_PATH / "input_controls.csv"),
        match_config=MatchConfig(**test_matching),
    )

    pd.testing.assert_frame_equal(case_matches_1, case_matches_2)
    pd.testing.assert_frame_equal(matched_matches_1, matched_matches_2)

    test_matching.update({"closest_match_variables": None})
    with pytest.raises(TypeError):
        match(
            case_df=load_dataframe(FIXTURE_PATH / "input_cases.csv"),
            match_df=load_dataframe(FIXTURE_PATH / "input_controls.csv"),
            match_config=MatchConfig(**test_matching),
        )


@pytest.mark.parametrize("drop_cases_from_matches", [True, False])
def test_match_drop_cases(tmp_path, drop_cases_from_matches):
    test_matching = {
        "matches_per_case": 1,
        "match_variables": {
            "sex": "category",
            "age": 1,
            "region": "category",
            "indexdate": "month_only",
        },
        "closest_match_variables": ["age"],
        "index_date_variable": "indexdate",
        "date_exclusion_variables": {
            "died_date_ons": "before",
            "previous_event": "before",
        },
        "output_suffix": "_test",
        "output_path": tmp_path / "test_output",
        "drop_cases_from_matches": drop_cases_from_matches,
    }

    case_df = load_dataframe(FIXTURE_PATH / "input_cases.csv")
    match_df = load_dataframe(FIXTURE_PATH / "input_controls.csv")
    match(
        case_df,
        match_df,
        match_config=MatchConfig(**test_matching),
    )
    report_path = test_matching["output_path"] / "matching_report_test.txt"
    report_text = report_path.read_text().split("\n")
    # Find the drop section of the report
    drop_section = report_text.index("Dropping cases from matches:")
    # Title line is followed by timestamp and number of cases, so we want the 3rd line
    matches_after_drop = int(report_text[drop_section + 3].split("Matches")[1].strip())
    if drop_cases_from_matches:
        assert len(match_df) > matches_after_drop
    else:
        assert len(match_df) == matches_after_drop


@pytest.mark.parametrize(
    "offset,expected_indexdate",
    [
        # These input files and config produce one match, for a case with indexdate 2020-07-29
        ("no_offset", datetime(2020, 7, 29)),
        ("1_day_earlier", datetime(2020, 7, 28)),
        ("3_months_later", datetime(2020, 10, 29)),
        ("2_years_earlier", datetime(2018, 7, 29)),
    ],
)
def test_generate_match_index_date(tmp_path, offset, expected_indexdate):
    test_matching = {
        "matches_per_case": 1,
        "match_variables": {
            "sex": "category",
            "age": 1,
            "region": "category",
            "indexdate": "month_only",
        },
        "closest_match_variables": ["age"],
        "index_date_variable": "indexdate",
        "output_path": tmp_path,
        "drop_cases_from_matches": True,
        "generate_match_index_date": offset,
    }

    case_df = load_dataframe(FIXTURE_PATH / "input_cases.csv")
    match_df = load_dataframe(FIXTURE_PATH / "input_controls.csv")
    config = MatchConfig(**test_matching)
    config, errors = parse_and_validate_config(config)
    assert errors == {}
    _, matched_matches = match(case_df, match_df, match_config=config)

    assert matched_matches.iloc[0].indexdate == expected_indexdate


def test_no_control_index_date(tmp_path):
    # If match input data has no index date variable, one is added
    test_matching = {
        "matches_per_case": 3,
        "match_variables": {"sex": "category"},
        "index_date_variable": "indexdate",
        "output_path": tmp_path,
        "generate_match_index_date": "no_offset",
    }

    case_df = pd.DataFrame.from_records(
        [
            [1, datetime(2021, 1, 1), "F"],
            [2, datetime(2022, 2, 1), "M"],
        ],
        columns=["patient_id", "indexdate", "sex"],
    )
    match_df = pd.DataFrame.from_records(
        [[4, "F"], [5, "M"], [6, "F"], [7, "M"], [8, "F"]],
        columns=["patient_id", "sex"],
    )
    config, _ = parse_and_validate_config(MatchConfig(**test_matching))
    _, matched_matches = match(
        case_df,
        match_df,
        match_config=config,
    )

    # match index date is generated from the case
    for f_index in [0, 2, 4]:
        assert matched_matches.iloc[f_index].indexdate == datetime(2021, 1, 1)
    for m_index in [1, 3]:
        assert matched_matches.iloc[m_index].indexdate == datetime(2022, 2, 1)


def test_categorical_get_bool_index():
    """
    Runs get_eligible_matches on synthetic categorical data and compares the test_data
    with manually entered boolean Series.
    """
    match_type = "category"
    value = "F"
    match_var = "sex"
    matches = pd.DataFrame.from_records(
        [["F"], ["M"], ["F"], ["M"], ["F"]], columns=["sex"]
    )

    bool_index = get_bool_index(match_type, value, match_var, matches)

    assert bool_index.equals(pd.Series([True, False, True, False, True]))


def test_scalar_get_bool_index():
    """
    Runs get_eligible_matches on synthetic integer data and compares the test_data
    with manually entered boolean Series.
    """
    match_type = 5
    value = 36
    match_var = "age"
    matches = pd.DataFrame.from_records([[30], [36], [39], [61], [75]], columns=["age"])

    bool_index = get_bool_index(match_type, value, match_var, matches)

    assert bool_index.equals(pd.Series([False, True, True, False, False]))


def test_pre_calculate_indices():
    """
    Test that the test_data booleans match with a predetermined series for a simple
    categorical variable with 2 categories. (other comparison types are tested in
    get_bool_index)
    """
    cases = pd.DataFrame.from_records([["F"], ["M"]], columns=["sex"])
    matches = pd.DataFrame.from_records(
        [["F"], ["M"], ["F"], ["M"], ["F"]], columns=["sex"]
    )
    match_variables = {"sex": "category"}

    indices_dict = pre_calculate_indices(cases, matches, match_variables)

    assert indices_dict["sex"]["F"].equals(pd.Series([True, False, True, False, True]))
    assert indices_dict["sex"]["M"].equals(pd.Series([False, True, False, True, False]))


def test_get_eligible_matches():
    """
    Runs get_eligible_matches on synthetic data and compares the test_data with
    manually entered boolean Series.
    """
    cases = pd.DataFrame.from_records(
        [
            {"sex": "M", "age": 36},
        ]
    )
    case_row = cases.iloc[0]
    matches = pd.DataFrame.from_records(
        [
            {"sex": "M", "age": 37, "set_id": NOT_PREVIOUSLY_MATCHED},
            {"sex": "M", "age": 57, "set_id": NOT_PREVIOUSLY_MATCHED},
            {"sex": "F", "age": 32, "set_id": NOT_PREVIOUSLY_MATCHED},
            {"sex": "F", "age": 81, "set_id": NOT_PREVIOUSLY_MATCHED},
            {"sex": "M", "age": 37, "set_id": 1},
        ]
    )
    match_variables = {"sex": "category", "age": 5}
    indices = {
        "sex": {"M": pd.Series([True, True, False, False, True])},
        "age": {36: pd.Series([True, False, True, False, True])},
    }

    eligible_matches = get_eligible_matches(case_row, matches, match_variables, indices)

    assert eligible_matches.equals(pd.Series([True, False, False, False, False]))


def test_date_exclusions():
    """
    Runs date_exclusions on synthetic data and compares the test_data with
    manually entered boolean Series. It does this for both a single index_date
    and a Series of index_dates (with the same index as df1) - the function
    accepts either.
    """
    df1 = pd.DataFrame.from_records(
        [
            # excluded on died date
            {"died_date": "2019-03-12", "previous_outcome": "", "later_outcome": ""},
            # excluded on later outcome
            {
                "died_date": "2020-02-01",
                "previous_outcome": "",
                "later_outcome": "2024-02-01",
            },
            # not excluded
            {"died_date": "2020-04-27", "previous_outcome": "", "later_outcome": ""},
            # excluded on previous outcome
            {
                "died_date": "2020-04-27",
                "previous_outcome": "2019-06-11",
                "later_outcome": "",
            },
            # not excluded
            {
                "died_date": "2020-04-27",
                "previous_outcome": "2020-04-01",
                "later_outcome": "",
            },
            # excluded on all
            {
                "died_date": "2019-03-12",
                "previous_outcome": "2019-06-30",
                "later_outcome": "2024-02-01",
            },
        ]
    )
    df1["died_date"] = pd.to_datetime(df1["died_date"])
    df1["previous_outcome"] = pd.to_datetime(df1["previous_outcome"])
    df1["later_outcome"] = pd.to_datetime(df1["later_outcome"])
    date_exclusion_variables = {
        "died_date": "before",
        "previous_outcome": "before",
        "later_outcome": "after",
    }
    index_date = "2020-02-01"
    index_date_series = pd.to_datetime(
        pd.Series(
            [
                "2019-11-01",
                "2019-12-01",
                "2020-01-01",
                "2020-02-01",
                "2020-03-01",
                "2020-04-12",
            ]
        )
    )

    excl = date_exclusions(df1, date_exclusion_variables, index_date)
    excl_ser = date_exclusions(df1, date_exclusion_variables, index_date_series)

    assert excl.equals(pd.Series([True, True, False, True, False, True]))
    assert excl_ser.equals(pd.Series([True, True, False, True, False, True]))


def test_greedily_pick_matches():
    """
    Runs greedily_pick_matches on synthetic data and compares the test_data with
    hand picked rows.
    """
    matches_per_case = 2
    matched_rows = pd.DataFrame.from_records(
        [
            {"age": 36},
            {"age": 35},
            {"age": 37},
            {"age": 31},
            {"age": 40},
        ]
    )
    cases = pd.DataFrame.from_records([{"age": 36}])
    case_row = cases.iloc[0]
    closest_match_columns = ["age"]

    matches = greedily_pick_matches(
        matches_per_case, matched_rows, case_row, closest_match_columns
    )

    test_matches = matched_rows.iloc[[0, 1, 2]]
    test_matches = test_matches.sample(n=matches_per_case, random_state=123).index

    assert matches.equals(test_matches)


def test_get_date_offset():
    """
    Tests that the pd.DateOffset produced by various combinations of input
    strings is correct.
    """
    no_offset = get_date_offset(("no_offset", "", 0))
    one_year_before = get_date_offset(("years", "before", 1))
    two_months_before = get_date_offset(("months", "before", 2))
    three_days_before = get_date_offset(("days", "before", 3))

    assert no_offset is None
    assert one_year_before == pd.DateOffset(years=1)
    assert two_months_before == pd.DateOffset(months=2)
    assert three_days_before == pd.DateOffset(days=3)
