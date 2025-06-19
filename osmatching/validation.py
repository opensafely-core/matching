from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:  # pragma: no cover
    # We are avoiding circular dependencies by using forward references for
    # type annotations where necessary, and this check so that type-checkin
    # imports are not executed at runtime.
    # https://peps.python.org/pep-0484/#forward-references
    # https://mypy.readthedocs.io/en/stable/runtime_troubles.html#import-cycles`
    from osmatching.utils import MatchConfig


def validate_required_vars(config):
    for var in config.required_vars():
        if getattr(config, var) is None:
            yield var


def parse_and_validate_config(config: "MatchConfig"):
    """
    Validate config values where possible in advance of any calculations
    """
    # ensure output_path is a Path
    config.output_path = Path(config.output_path)

    errors = defaultdict(list)

    for missing in validate_required_vars(config):
        errors[missing].append(f"Not found: `{missing}` is a required config variable")

    # validate min matches per case
    if (
        config.matches_per_case is not None
        and config.min_matches_per_case > config.matches_per_case
    ):
        errors["min_matches_per_case"].append(
            f"`min_matches_per_case` ({config.min_matches_per_case}) cannot be greater than `matches_per_case` ({config.matches_per_case})"
        )

    return config, errors
