import os
import shutil
from contextlib import contextmanager
from glob import glob
from tempfile import TemporaryDirectory

import pandas as pd

from osmatching.osmatching import (
    match,
    get_bool_index,
    pre_calculate_indices,
    get_eligible_matches,
    date_exclusions,
    greedily_pick_matches,
    get_date_offset,
    compare_populations,
    NOT_PREVIOUSLY_MATCHED,
)


@contextmanager
def set_up_output():
    """Copy the CSV files in tests/output to a temporary directory, and yield
    the path to this directory.

    This should be used as a context manager:

    with set_up_output() as output_path:
        match(output_path=output_path, **pneumonia)
        assert os.path.exists(
            os.path.join(output_path, "matching_report_input_pneumonia.txt")
        )
    """

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    with TemporaryDirectory() as dir_path:
        for path in glob(os.path.join(output_path, "*.csv")):
            shutil.copy(path, dir_path)
        yield dir_path


def test_match_smoke_test():
    """Test that match() runs and produces a matching report."""

    pneumonia = {
        "case_csv": "input_covid",
        "match_csv": "input_pneumonia",
        "matches_per_case": 1,
        "match_variables": {
            "sex": "category",
            "age": 1,
            "stp": "category",
            "indexdate": "month_only",
        },
        "closest_match_variables": ["age"],
        "index_date_variable": "indexdate",
        "date_exclusion_variables": {
            "died_date_ons": "before",
            "previous_vte_gp": "before",
            "previous_vte_hospital": "before",
            "previous_stroke_gp": "before",
            "previous_stroke_hospital": "before",
        },
        "output_suffix": "_pneumonia",
    }

    with set_up_output() as output_path:
        match(output_path=output_path, **pneumonia)
        assert os.path.exists(
            os.path.join(output_path, "matching_report_pneumonia.txt")
        )


def test_categorical_get_bool_index():
    """
    Runs get_eligible_matches on synthetic categorical data and compares the output
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
    Runs get_eligible_matches on synthetic integer data and compares the output
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
    Test that the output booleans match with a predetermined series for a simple
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
    Runs get_eligible_matches on synthetic data and compares the output with
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
    Runs date_exclusions on synthetic data and compares the output with
    manually entered boolean Series. It does this for both a single index_date
    and a Series of index_dates (with the same index as df1) - the function
    accepts either.
    """
    df1 = pd.DataFrame.from_records(
        [
            {"died_date": "2019-03-12", "previous_outcome": ""},
            {"died_date": "2020-02-01", "previous_outcome": ""},
            {"died_date": "2020-04-27", "previous_outcome": ""},
            {"died_date": "2020-04-27", "previous_outcome": "2019-06-11"},
            {"died_date": "2020-04-27", "previous_outcome": "2020-04-01"},
            {"died_date": "2019-03-12", "previous_outcome": "2019-06-30"},
        ]
    )
    df1["died_date"] = pd.to_datetime(df1["died_date"])
    df1["previous_outcome"] = pd.to_datetime(df1["previous_outcome"])
    date_exclusion_variables = {
        "died_date": "before",
        "previous_outcome": "before",
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
    assert excl_ser.equals(pd.Series([True, False, False, True, False, True]))


def test_greedily_pick_matches():
    """
    Runs greedily_pick_matches on synthetic data and compares the output with
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
    no_offset = get_date_offset("no_offset")
    one_year_before = get_date_offset("1_year_before")
    two_months_before = get_date_offset("2_months_before")
    three_days_before = get_date_offset("3_days_before")

    assert no_offset is None
    assert one_year_before == pd.DateOffset(years=1)
    assert two_months_before == pd.DateOffset(months=2)
    assert three_days_before == pd.DateOffset(days=3)
