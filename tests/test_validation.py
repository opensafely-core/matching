from pathlib import Path

import pytest

from osmatching.utils import MatchConfig, parse_and_validate_config
from osmatching.validation import get_match_index_date_offset


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
    assert not config.validated

    config, errors = parse_and_validate_config(config)
    assert config.validated
    assert errors == {}


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
        (
            2,
            [
                "`min_matches_per_case` (2) cannot be greater than `matches_per_case` (1)"
            ],
        ),
    ],
)
def test_min_matches_per_case(min_matches, error):
    config = get_match_config({"min_matches_per_case": min_matches})
    config, errors = parse_and_validate_config(config)
    assert errors.get("min_matches_per_case") == error


@pytest.mark.parametrize(
    "config_vars,error_keys",
    [
        (
            {
                "matches_per_case": 1,
            },
            ["match_variables", "index_date_variable"],
        ),
        (
            {
                "index_date_variable": "index_date",
                "match_variables": {"age": 5},
            },
            ["matches_per_case"],
        ),
        ({}, ["matches_per_case", "match_variables", "index_date_variable"]),
    ],
)
def test_missing_required_vars(config_vars, error_keys):
    config = MatchConfig(**config_vars)
    config, errors = parse_and_validate_config(config)
    assert list(errors.keys()) == error_keys


def test_replace_none_with_default():
    config = get_match_config(
        {"date_exclusion_variables": None, "closest_match_variables": None}
    )
    config, errors = parse_and_validate_config(config)
    assert errors == {}
    assert config.date_exclusion_variables == {}
    assert config.closest_match_variables == []


def test_date_exclusions_invalid_type():
    config = get_match_config(
        {
            "date_exclusion_variables": {
                "died_date": "on_or_before",
                "event_date": "on_or_after",
                "hospitalisation_date": "before",
            }
        }
    )
    config, errors = parse_and_validate_config(config)
    assert errors == {
        "date_exclusion_variables": [
            "Invalid exclusion type 'on_or_before' for variable 'died_date'. Allowed types are 'before' or 'after'",
            "Invalid exclusion type 'on_or_after' for variable 'event_date'. Allowed types are 'before' or 'after'",
        ]
    }


def test_match_variables_types():
    config = get_match_config(
        {
            "match_variables": {
                "died_date": "month_only",
                "age": 5,
                "sex": "category",
                "negative": -4,
                "region": "London",
                "score": 1.5,
                "none": None,
            }
        }
    )
    config, errors = parse_and_validate_config(config)
    assert errors == {
        "match_variables": [
            "Invalid match type 'London' for variable `region`. Allowed are 'category', 'month_only', and integers.",
            "Invalid match type '1.5' for variable `score`. Allowed are 'category', 'month_only', and integers.",
            "Invalid match type 'None' for variable `none`. Allowed are 'category', 'month_only', and integers.",
        ]
    }


@pytest.mark.parametrize(
    "offset_str, offset",
    [
        ("", None),
        (None, None),
        ("no_offset", ("no_offset", "", 0)),
        ("1_day_earlier", ("days", "earlier", 1)),
        ("4_days_later", ("days", "later", 4)),
        ("2_month_earlier", ("months", "earlier", 2)),  # deliberate typo
        ("4_months_later", ("months", "later", 4)),
        ("2_years_earlier", ("years", "earlier", 2)),
        ("1_year_later", ("years", "later", 1)),
    ],
)
def test_get_match_index_date_offset(offset_str, offset):
    assert get_match_index_date_offset(offset_str) == offset


@pytest.mark.parametrize(
    "offset_str,error",
    [
        ("1_year", "Date offset '1_year' could not be parsed"),
        ("1 year earlier", "Date offset '1 year earlier' could not be parsed"),
        ("1_quarters_earlier", "Date offset units 'quarters' not implemented"),
        ("before_2_months", "Date offset 'before_2_months' could not be parsed"),
        ("two_days_later", "Date offset 'two_days_later' could not be parsed"),
        ("2_months_before", "Date offset type 'before' not implemented"),
    ],
)
def test_generate_match_index_date_error(offset_str, error):
    config = get_match_config({"generate_match_index_date": offset_str})
    config, errors = parse_and_validate_config(config)
    assert errors["generate_match_index_date"] == [error]
