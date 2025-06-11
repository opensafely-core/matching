"""Command line tool for using match"""

import argparse
import json
from importlib.metadata import version
from pathlib import Path
from typing import Dict

from osmatching.osmatching import match
from osmatching.utils import file_suffix, load_config, load_dataframe


class ActionConfig(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        # values can be a path to a file, or a json string
        path = Path(values)
        try:
            if path.exists():
                with path.open() as f:
                    config = json.load(f)
            else:
                config = json.loads(values)
        except json.JSONDecodeError as exc:
            raise argparse.ArgumentTypeError(f"Could not parse {values}\n{exc}")
        setattr(namespace, self.dest, config)


class LoadDataframe(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        data_filepath = Path(values)
        if not data_filepath.exists():
            raise argparse.ArgumentTypeError(f"File {values} not found")
        if file_suffix(data_filepath) not in [".csv", ".csv.gz", ".arrow"]:
            raise argparse.ArgumentTypeError(
                "Invalid file type; provide a .arrow, .csv.gz or .csv file"
            )
        setattr(namespace, self.dest, load_dataframe(data_filepath))


def load_matching_config(cases: str, controls: str, config: Dict, output_format: str):
    processed_match_config = load_config(config)

    match(
        case_df=cases,
        match_df=controls,
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
        drop_cases_from_matches=processed_match_config["drop_cases_from_matches"],
        output_suffix=processed_match_config["output_suffix"],
        output_format=processed_match_config["output_format"],
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

    parser.add_argument(
        "--config",
        required=True,
        help="The configuration for the matching action",
        action=ActionConfig,
    )

    # version
    parser.add_argument(
        "--version",
        action="version",
        version=f"opensafely-matching {version('opensafely-matching')}",
    )

    # Cases
    parser.add_argument(
        "--cases", action=LoadDataframe, help="Data file that contains the cases"
    )

    # Controls
    parser.add_argument(
        "--controls",
        action=LoadDataframe,
        help="Data file that contains the cohort for cases",
    )

    parser.add_argument(
        "--output-format",
        choices=["arrow", "csv.gz", "csv"],
        help="Format for the output files",
        default="arrow",
    )

    # parse args
    args = parser.parse_args()

    # run matching
    load_matching_config(
        cases=args.cases,
        controls=args.controls,
        config=args.config,
        output_format=args.output_format,
    )


if __name__ == "__main__":
    main()
