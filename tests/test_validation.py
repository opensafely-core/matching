from pathlib import Path

from osmatching.utils import MatchConfig, parse_and_validate_config


CONFIG_DICT_DEFAULTS = {
    "matches_per_case": 1,
    "index_date_variable": "index_date",
    "match_variables": {"age": 5},
}


def test_output_path():
    test_data = {**CONFIG_DICT_DEFAULTS, "output_path": "test_output"}
    config = MatchConfig(**test_data)
    assert isinstance(config.output_path, str)

    parse_and_validate_config(config)
    assert isinstance(config.output_path, Path)
