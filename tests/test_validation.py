from pathlib import Path

import pytest

from osmatching.utils import MatchConfig, parse_and_validate_config


CONFIG_DICT_DEFAULTS = {
    "matches_per_case": 1,
    "index_date_variable": "index_date",
    "match_variables": {"age": 5},
}


def get_match_config(test_config):
    test_data = {**CONFIG_DICT_DEFAULTS, **test_config}
    return MatchConfig.from_dict(test_data)


def test_output_path():
    config = get_match_config({"output_path": "test_output"})
    assert isinstance(config.output_path, Path)


def test_defaults():
    test_data = {**CONFIG_DICT_DEFAULTS, "closest_match_variables": None}
    config = MatchConfig.from_dict(test_data)
    assert config.closest_match_variables == []
    assert config.date_exclusion_variables == {}


@pytest.mark.parametrize(
    "min_matches,error",
    [
        (0, None),
        (1, None),
        (2, ["min_matches_per_case (2) cannot be greater than matches_per_case (1)"]),
    ],
)
def test_min_matches_per_case(min_matches, error):
    config = get_match_config({"min_matches_per_case": min_matches})
    config, errors = parse_and_validate_config(config)
    assert errors.get("min_matches_per_case") == error
