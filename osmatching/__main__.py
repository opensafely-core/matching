"""Command line tool for using match"""

import argparse
import json
import sys
from pathlib import Path

from osmatching.osmatching import match
from osmatching.utils import (
    MatchConfig,
    file_suffix,
    load_config,
    load_dataframe,
    report_validation_errors,
)
from osmatching.validation import ValidationType


class BaseLoadMatchingConfig(argparse.Action):
    def load_json(self, values):  # pragma: no cover
        return NotImplemented

    def __call__(self, parser, namespace, values, option_string=None):
        # values can be a path to a file, or a json string
        config = self.load_json(values)
        config, errors = load_config(config)
        if errors:
            report_validation_errors(errors, validation_type=ValidationType.CONFIG)
            sys.exit(2)
        setattr(namespace, self.dest, config)


class LoadMatchingConfigString(BaseLoadMatchingConfig):
    def load_json(self, values):
        try:
            return json.loads(values)
        except json.JSONDecodeError as exc:
            raise argparse.ArgumentTypeError(f"Could not parse {values}\n{exc}")


class LoadMatchingConfigFile(BaseLoadMatchingConfig):
    def load_json(self, values):
        path = Path(values)
        if not path.exists():
            raise argparse.ArgumentTypeError(f"Config file not found: {values}")
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            raise argparse.ArgumentTypeError(
                f"Could not load json from config file: {values}\n{exc}"
            )


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


def run_matching(
    cases: str, controls: str, config: MatchConfig, output_format: str | None = None
):
    # an explicitly provided command line output_format takes precedence over config value
    if output_format is not None:
        config.output_format = output_format
    match(
        case_df=cases,
        match_df=controls,
        match_config=config,
    )


def main():
    """
    Command line tool for running matching.
    """
    # make args parser
    parser = argparse.ArgumentParser(
        description="Matches cases to controls if provided with 2 datasets"
    )

    # add configuration arg; one of config or config-file is required
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--config",
        help="The configuration for the matching action (a JSON string)",
        action=LoadMatchingConfigString,
        dest="config",
    )
    group.add_argument(
        "--config-file",
        help="Path to the configuration JSON file for the matching action",
        action=LoadMatchingConfigFile,
        dest="config",
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
    )

    # parse args
    args = parser.parse_args()

    # run matching
    run_matching(
        cases=args.cases,
        controls=args.controls,
        config=args.config,
        output_format=args.output_format,
    )


if __name__ == "__main__":
    main()
