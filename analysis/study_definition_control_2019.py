from cohortextractor import StudyDefinition, patients, codelist, codelist_from_csv
from common_variables import common_variable_define
from codelists import *

start_date = "2019-02-01"
common_variables = common_variable_define(start_date)

study = StudyDefinition(
    default_expectations={
        "date": {"earliest": "1900-01-01", "latest": "today"},
        "rate": "exponential_increase",
        "incidence": 0.7,
    },
    population=patients.satisfying(
        """
            has_follow_up
        AND (age >=18 AND age <= 110)
        AND (sex = "M" OR sex = "F")
        AND imd > 0
        """,
        has_follow_up=patients.registered_with_one_practice_between(
            "2018-02-01", "2019-02-01"
        ),
    ),
    **common_variables
)
