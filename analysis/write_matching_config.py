import json
from pathlib import Path


config = {
    "matches_per_case": 3,
    "match_variables": {"sex": "category", "age": 5},
    "index_date_variable": "indexdate",
    "closest_match_variables": ["age"],
    "generate_match_index_date": "no_offset",
    "output_suffix": "_with_config_file",
}

Path("output/config.json").write_text(json.dumps(config, indent=2))
