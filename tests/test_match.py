import os
import shutil
from contextlib import contextmanager
from glob import glob
from tempfile import TemporaryDirectory

import pandas as pd

from analysis.match import match, pre_calculate_indices


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
        "closest_match_columns": ["age"],
        "index_date_variable": "indexdate",
        "date_exclusion_variables": {
            "died_date_ons": "before",
            "previous_vte_gp": "before",
            "previous_vte_hospital": "before",
            "previous_stroke_gp": "before",
            "previous_stroke_hospital": "before",
        },
    }

    with set_up_output() as output_path:
        match(output_path=output_path, **pneumonia)
        assert os.path.exists(
            os.path.join(output_path, "matching_report_pneumonia.txt")
        )


def test_pre_calculate_indices():
    cases = pd.DataFrame.from_records([["F"], ["M"]], columns=["sex"])
    matches = pd.DataFrame.from_records(
        [["F"], ["M"], ["F"], ["M"], ["F"]], columns=["sex"]
    )
    match_variables = {"sex": "category"}

    indices_dict = pre_calculate_indices(cases, matches, match_variables)

    assert indices_dict["sex"]["F"].equals(pd.Series([True, False, True, False, True]))
    assert indices_dict["sex"]["M"].equals(pd.Series([False, True, False, True, False]))
