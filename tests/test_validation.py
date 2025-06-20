from pathlib import Path

from osmatching.utils import MatchConfig


CONFIG_DICT_DEFAULTS = {
    "matches_per_case": 1,
    "index_date_variable": "index_date",
    "match_variables": {"age": 5},
}


def test_output_path():
    test_data = {**CONFIG_DICT_DEFAULTS, "output_path": "test_output"}
    config = MatchConfig.from_dict(test_data)
    assert isinstance(config.output_path, Path)


def test_defaults():
    test_data = {**CONFIG_DICT_DEFAULTS, "closest_match_variables": None}
    config = MatchConfig.from_dict(test_data)
    assert config.closest_match_variables == []
    assert config.date_exclusion_variables == {}
