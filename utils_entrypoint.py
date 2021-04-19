

def load_default_args(match_config):
    """ loads default args into the config"""

    if "closest_match_variable" not in match_config:
        match_config["closest_match_variable"] = None

    if "date_exclusion_variables" not in match_config:
        match_config["date_exclusion_variables"] = None

    if "min_matches_per_case" not in match_config:
        match_config["min_matches_per_case"] = 0

    if "replace_match_index_date_with_case" not in match_config:
        match_config["replace_match_index_date_with_case"] = None

    if "output_suffix" not in match_config:
        match_config["output_suffix"] = ""

    if "indicator_variable_name" not in match_config:
        match_config["indicator_variable_name"] = "case"

    if "output_path" not in match_config:
        match_config["output_path"] = "tests/test_output"

    if "input_path" not in match_config:
        match_config["input_path"] = "tests/test_data"

    if "drop_cases_from_matches" not in match_config:
        match_config["drop_cases_from_matches"] = False

    return match_config