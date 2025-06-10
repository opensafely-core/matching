from typing import Any, Dict


DEFAULTS = {
    "closest_match_variable": None,
    "date_exclusion_variables": None,
    "min_matches_per_case": 0,
    "replace_match_index_date_with_case": None,
    "output_suffix": "",
    "indicator_variable_name": "case",
    "output_path": "outputs/",
    "input_path": "inputs/",
    "drop_cases_from_matches": False,
}


def load_config(match_config: Dict) -> Dict[str, Any]:
    """
    Takes in match configuration and changes these key-value pairs
    where indicated by the match config. All other key-value pairs
    are left as default values

    Args:
        match_config (dict): dictionary of the match configuration
            taken from json

    Returns:
        Dict (cfg): Configuration dictionary to be passed to entry point.
    """
    cfg = DEFAULTS.copy()
    cfg.update(match_config)
    return cfg
