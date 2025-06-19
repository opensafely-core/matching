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
    return MatchConfig(**test_data)


def test_output_path():
    test_data = {**CONFIG_DICT_DEFAULTS, "output_path": "test_output"}
    config = MatchConfig.from_dict(test_data)
    assert isinstance(config.output_path, Path)


def test_defaults():
    test_data = {**CONFIG_DICT_DEFAULTS, "closest_match_variables": None}
    config = MatchConfig.from_dict(test_data)
    assert config.closest_match_variables == []
    assert config.date_exclusion_variables == {}


@pytest.mark.parametrize("min_matches,error", [(0, False), (1, False), (2, True)])
def test_min_matches_per_case(min_matches, error):
    config = get_match_config({"min_matches_per_case": min_matches})
    if error:
        with pytest.raises(
            ValueError,
            match="min_matches_per_case cannot be greater than matches_per_case",
        ):
            parse_and_validate_config(config)
    else:
        parse_and_validate_config(config)
