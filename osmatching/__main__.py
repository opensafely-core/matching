"""Command line tool for using match"""

import argparse
import json
from pathlib import Path

from osmatching.osmatching import match
from osmatching.utils import MatchConfig, file_suffix, load_config, load_dataframe


class LoadMatchingConfig(argparse.Action):
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

        config = load_config(config)
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


def load_matching_config(
    cases: str, controls: str, config: MatchConfig, output_format: str
):
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

    # add configuration arg

    parser.add_argument(
        "--config",
        required=True,
        help="The configuration for the matching action",
        action=LoadMatchingConfig,
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
