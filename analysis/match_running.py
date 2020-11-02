from match import match

pneumonia = {
    "case_csv": "input_covid",
    "match_csv": "input_pneumonia",
    "matches_per_case": 1,
    "match_variables": {
        "sex": "category",
        "age": 1,
        "stp": "category",
        "indexdate": "month_only",
    },
    "closest_match_columns": ["age"],
    "index_date_variable": "indexdate",
    "date_exclusion_variables": {
        "died_date_ons": "before",
        "previous_vte_gp": "before",
        "previous_vte_hospital": "before",
        "previous_stroke_gp": "before",
        "previous_stroke_hospital": "before",
    },
}
match(pneumonia)


control_2019 = {
    "case_csv": "input_covid",
    "match_csv": "input_control_2019",
    "matches_per_case": 2,
    "match_variables": {
        "sex": "category",
        "age": 1,
        "stp": "category",
    },
    "closest_match_columns": ["age"],
    "replace_match_index_date_with_case": "1_year_earlier",
    "index_date_variable": "indexdate",
    "date_exclusion_variables": {
        "died_date_ons": "before",
        "previous_vte_gp": "before",
        "previous_vte_hospital": "before",
        "previous_stroke_gp": "before",
        "previous_stroke_hospital": "before",
    },
}
match(control_2019)


control_2020 = {
    "case_csv": "input_covid",
    "match_csv": "input_control_2020",
    "matches_per_case": 2,
    "match_variables": {
        "sex": "category",
        "age": 1,
        "stp": "category",
    },
    "closest_match_columns": ["age"],
    "replace_match_index_date_with_case": "no_offset",
    "index_date_variable": "indexdate",
    "date_exclusion_variables": {
        "died_date_ons": "before",
        "previous_vte_gp": "before",
        "previous_vte_hospital": "before",
        "previous_stroke_gp": "before",
        "previous_stroke_hospital": "before",
    },
}
match(control_2020)
