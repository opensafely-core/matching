""" Command line tool for using match """
import argparse
import json

from osmatching import match


def load_matching_config(input_files, match_config):
    print(match_config)
    match(case_csv=input_files['cases'],
          match_csv=input_files['controls'],
          matches_per_case=match_config['matches_per_case'],
          match_variables={
              "age": 5
          },
          index_date_variable=match_config["index_variable"],
          output_path="")


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
