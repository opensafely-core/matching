""" Command line tool for using match """
import argparse
import json

from osmatching import match
from utils_entrypoint import load_config

def load_matching_config(input_files, match_config):

    processed_match_config = load_config(match_config)

    match(case_csv=input_files['cases'],
          match_csv=input_files['controls'],
          matches_per_case=processed_match_config['matches_per_case'],
          match_variables=processed_match_config["match_variables"],
          index_date_variable=processed_match_config["index_variable"],
          closest_match_variables=processed_match_config["closest_match_variable"],
          date_exclusion_variables=processed_match_config["date_exclusion_variables"],
          min_matches_per_case=processed_match_config["min_matches_per_case"],
          replace_match_index_date_with_case=processed_match_config["replace_match_index_date_with_case"],
          indicator_variable_name=processed_match_config["indicator_variable_name"],
          output_path=processed_match_config['output_path'],
          input_path=processed_match_config["input_path"],
          drop_cases_from_matches=processed_match_config["drop_cases_from_matches"],
          output_suffix=processed_match_config["output_suffix"]
          )


def main():
    """
    Command line tool for running matching.
    """
    # make args parser
    parser = argparse.ArgumentParser(description="Matches cases to controls if provided with 2 datasets")

    # version
    parser.add_argument("--version", action='version', version="osmatching 0.0.1")

    # configurations
    parser.add_argument("config", type=str, help="XXX add something here")

    # parse args
    args = parser.parse_args()

    kwargs = vars(args)
    json_path = kwargs.pop("config")

    # TODO: Make sure file exists
    with open(json_path) as json_file:
        instructions = json.load(json_file)

    # run matching
    load_matching_config(input_files=instructions['inputs'], match_config=instructions['config'])



if __name__ == "__main__":
    main()
