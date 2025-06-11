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
    # ADD config output_format
    config["output_format"] = output_format
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
