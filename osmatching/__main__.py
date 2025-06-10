"""Command line tool for using match"""

import argparse
import json
from importlib.metadata import version
from pathlib import Path
from typing import Dict

from osmatching.osmatching import match
from osmatching.utils import load_config


class ActionConfig:
    def __init__(self, validator=None):
        self.validator = validator

    def __call__(self, file_or_string):
        path = Path(file_or_string)
        try:
            if path.exists():
                with path.open() as f:
                    config = json.load(f)
            else:
                config = json.loads(file_or_string)
        except json.JSONDecodeError as exc:
            raise argparse.ArgumentTypeError(f"Could not parse {file_or_string}\n{exc}")

        if self.validator:
            try:
                self.validator(config)
            except Exception as exc:
                raise argparse.ArgumentTypeError(f"Invalid action config:\n{exc}")

        return config

    @classmethod
    def add_to_parser(
        cls,
        parser,
        helptext="The configuration for the matching action",
        validator=None,
    ):
        parser.add_argument(
            "--config",
            required=True,
            help=helptext,
            type=ActionConfig(validator),
        )


def load_matching_config(cases: str, controls: str, config: Dict):
    processed_match_config = load_config(config)

    match(
        case_csv=cases,
        match_csv=controls,
        matches_per_case=processed_match_config["matches_per_case"],
        match_variables=processed_match_config["match_variables"],
        index_date_variable=processed_match_config["index_variable"],
        closest_match_variables=processed_match_config["closest_match_variable"],
        date_exclusion_variables=processed_match_config["date_exclusion_variables"],
        min_matches_per_case=processed_match_config["min_matches_per_case"],
        replace_match_index_date_with_case=processed_match_config[
            "replace_match_index_date_with_case"
        ],
        indicator_variable_name=processed_match_config["indicator_variable_name"],
        output_path=processed_match_config["output_path"],
        input_path=processed_match_config["input_path"],
        drop_cases_from_matches=processed_match_config["drop_cases_from_matches"],
        output_suffix=processed_match_config["output_suffix"],
    )


def main():
    """
    Command line tool for running matching.
    """
    # make args parser
    parser = argparse.ArgumentParser(
        description="Matches cases to controls if provided with 2 datasets"
    )

    # add configuration arg
    ActionConfig.add_to_parser(parser)

    # version
    parser.add_argument(
        "--version",
        action="version",
        version=f"opensafely-matching {version('opensafely-matching')}",
    )

    # Cases
    parser.add_argument("--cases", help="Data file that contains the cases")

    # Controls
    parser.add_argument(
        "--controls", help="Data file that contains the cohort for cases"
    )

    # parse args
    args = parser.parse_args()

    # run matching
    load_matching_config(cases=args.cases, controls=args.controls, config=args.config)


if __name__ == "__main__":
    main()
