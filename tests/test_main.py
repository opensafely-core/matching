import json
import sys
from pathlib import Path

import pytest

from osmatching.__main__ import main


FIXTURE_PATH = Path(__file__).parent / "test_data"


@pytest.fixture
def cli_ouput_path(tmp_path):
    """
    Mock command line args to fixture data and yield temporary
    path to use as output path
    """
    # rewrite config output path to our temp path
    with open(FIXTURE_PATH / "config.json") as configfile:
        config = json.load(configfile)
        config["output_path"] = str(tmp_path)
    with open(tmp_path / "config.json", "w") as test_configfile:
        json.dump(config, test_configfile)

    original_argv = sys.argv
    sys.argv = [
        "match",
        "--cases",
        str(FIXTURE_PATH / "input_cases.csv"),
        "--controls",
        str(FIXTURE_PATH / "input_controls.csv"),
        "--config",
        str(tmp_path / "config.json"),
    ]
    yield tmp_path
    sys.argv = original_argv


def test_main(cli_ouput_path):
    output_path = cli_ouput_path
    main()
    assert (output_path / "matching_report_test.txt").exists()
