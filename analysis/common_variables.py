from cohortextractor import filter_codes_by_category, patients
from codelists import *
from datetime import datetime, timedelta


def days_before(s, days):
    date = datetime.strptime(s, "%Y-%m-%d")
    modified_date = date - timedelta(days=days)
    return datetime.strftime(modified_date, "%Y-%m-%d")


def common_variable_define(start_date):
    common_variables = dict(
        previous_vte_gp=patients.with_these_clinical_events(
            vte_codes_gp,
            returning="date",
            date_format="YYYY-MM-DD",
            find_first_match_in_period=True,
            return_expectations={"incidence": 0.05,},
        ),
        previous_vte_hospital=patients.admitted_to_hospital(
            with_these_diagnoses=vte_codes_hospital,
            returning="date_admitted",
            date_format="YYYY-MM-DD",
            find_first_match_in_period=True,
            return_expectations={"incidence": 0.05,},
        ),
        previous_stroke_gp=patients.with_these_clinical_events(
            stroke,
            returning="date",
            date_format="YYYY-MM-DD",
            find_first_match_in_period=True,
            return_expectations={"incidence": 0.05,},
        ),
        previous_stroke_hospital=patients.admitted_to_hospital(
            with_these_diagnoses=stroke_hospital,
            returning="date_admitted",
            date_format="YYYY-MM-DD",
            find_first_match_in_period=True,
            return_expectations={"incidence": 0.05,},
        ),
        died_date_ons=patients.died_from_any_cause(
            on_or_after=start_date,
            returning="date_of_death",
            date_format="YYYY-MM-DD",
            return_expectations={"date": {"earliest": start_date}},
        ),
        age=patients.age_as_of(
            start_date,
            return_expectations={
                "rate": "universal",
                "int": {"distribution": "population_ages"},
            },
        ),
        sex=patients.sex(
            return_expectations={
                "rate": "universal",
                "category": {"ratios": {"M": 0.49, "F": 0.51}},
            }
        ),
        practice_id=patients.registered_practice_as_of(
            start_date,
            returning="pseudo_id",
            return_expectations={
                "int": {"distribution": "normal", "mean": 1000, "stddev": 100},
                "incidence": 1,
            },
        ),
        stp=patients.registered_practice_as_of(
            start_date,
            returning="stp_code",
            return_expectations={
                "rate": "universal",
                "category": {
                    "ratios": {
                        "STP1": 0.1,
                        "STP2": 0.1,
                        "STP3": 0.1,
                        "STP4": 0.1,
                        "STP5": 0.1,
                        "STP6": 0.1,
                        "STP7": 0.1,
                        "STP8": 0.1,
                        "STP9": 0.1,
                        "STP10": 0.1,
                    }
                },
            },
        ),
        region=patients.registered_practice_as_of(
            start_date,
            returning="nuts1_region_name",
            return_expectations={
                "rate": "universal",
                "category": {
                    "ratios": {
                        "North East": 0.1,
                        "North West": 0.1,
                        "Yorkshire and The Humber": 0.1,
                        "East Midlands": 0.1,
                        "West Midlands": 0.1,
                        "East": 0.1,
                        "London": 0.2,
                        "South East": 0.1,
                        "South West": 0.1,
                    },
                },
            },
        ),
        imd=patients.address_as_of(
            start_date,
            returning="index_of_multiple_deprivation",
            round_to_nearest=100,
            return_expectations={
                "rate": "universal",
                "category": {"ratios": {"100": 0.1, "200": 0.2, "300": 0.7}},
            },
        ),
    )
    return common_variables
