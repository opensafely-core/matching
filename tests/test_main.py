import json
import sys
from argparse import ArgumentTypeError
from pathlib import Path

import pytest

from osmatching.__main__ import main


FIXTURE_PATH = Path(__file__).parent / "test_data" / "fixtures"


@pytest.fixture(autouse=True)
def reset_sys_argv():
    original_argv = sys.argv
    yield
    sys.argv = original_argv


@pytest.fixture(params=["csv", "csv.gz", "arrow"])
def cli_ouput_path(request, tmp_path):
    """
    Mock command line args to fixture data and yield temporary
    path to use as output path
    """
    output_format = request.param
    # rewrite config output path to our temp path
    with open(FIXTURE_PATH / "config.json") as configfile:
        config = json.load(configfile)
        config["output_path"] = str(tmp_path)

    with open(tmp_path / "config.json", "w") as test_configfile:
        json.dump(config, test_configfile)

    sys.argv = [
        "match",
        "--cases",
        str(FIXTURE_PATH / f"input_cases.{output_format}"),
        "--controls",
        str(FIXTURE_PATH / f"input_controls.{output_format}"),
        "--config",
        str(tmp_path / "config.json"),
        "--output-format",
        output_format,
    ]
    yield tmp_path, output_format


def test_main(cli_ouput_path):
    output_path, output_format = cli_ouput_path
    main()
    assert (output_path / "matching_report_test.txt").exists()
    assert (output_path / f"matched_cases_test.{output_format}").exists()


@pytest.mark.parametrize("include_cli_arg", [True, False])
def test_cli_output_format(tmp_path, include_cli_arg):
    # The config default is arrow. If provided, a cli arg overrides it.
    config = {
        "matches_per_case": 1,
        "match_variables": {"age": "category"},
        "index_date_variable": "indexdate",
        "output_path": str(tmp_path),
        "output_format": "arrow",
    }
    sys.argv = [
        "match",
        "--cases",
        str(FIXTURE_PATH / "input_cases.arrow"),
        "--controls",
        str(FIXTURE_PATH / "input_controls.arrow"),
        "--config",
        json.dumps(config),
    ]
    if include_cli_arg:
        sys.argv.extend(["--output-format", "csv.gz"])
    main()
    assert (tmp_path / "matched_cases.csv.gz").exists() == include_cli_arg
    assert (tmp_path / "matched_cases.arrow").exists() == (not include_cli_arg)


def test_input_file_does_not_exist():
    sys.argv = [
        "match",
        "--cases",
        "unknown/path.csv",
        "--controls",
        str(FIXTURE_PATH / "input_controls.csv"),
        "--config",
        str(FIXTURE_PATH / "config.json"),
    ]
    with pytest.raises(ArgumentTypeError, match="File unknown/path.csv not found"):
        main()


def test_input_file_bad_type():
    sys.argv = [
        "match",
        "--cases",
        str(FIXTURE_PATH / "config.json"),
        "--controls",
        str(FIXTURE_PATH / "input_controls.csv"),
        "--config",
        str(FIXTURE_PATH / "config.json"),
    ]
    with pytest.raises(ArgumentTypeError, match="Invalid file type"):
        main()


def test_config_non_existent_file():
    sys.argv = [
        "match",
        "--cases",
        str(FIXTURE_PATH / "input_cases.csv"),
        "--controls",
        str(FIXTURE_PATH / "input_controls.csv"),
        "--config",
        "unknown/config.json",
    ]

    with pytest.raises(ArgumentTypeError, match="Could not parse unknown/config.json"):
        main()


def test_config_bad_json():
    sys.argv = [
        "match",
        "--cases",
        str(FIXTURE_PATH / "input_cases.csv"),
        "--controls",
        str(FIXTURE_PATH / "input_controls.csv"),
        "--config",
        "{foo}",
    ]

    with pytest.raises(ArgumentTypeError, match="Could not parse {foo}"):
        main()


def test_config_validation_errors(capsys):
    sys.argv = [
        "match",
        "--cases",
        str(FIXTURE_PATH / "input_cases.csv"),
        "--controls",
        str(FIXTURE_PATH / "input_controls.csv"),
        "--config",
        json.dumps(
            {
                "matches_per_case": 1,
                "min_matches_per_case": 2,
                "index_date_variable": "index_date",
                "match_variables": {"age": 5},
            }
        ),
    ]
    with pytest.raises(SystemExit):
        main()

    output = capsys.readouterr().out
    assert (
        output
        == """
Errors were found in the provided configuration:

  min_matches_per_case
  * `min_matches_per_case` (2) cannot be greater than `matches_per_case` (1)

Please correct these errors and try again
"""
    )
