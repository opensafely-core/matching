#!/bin/bash
set -eou pipefail

opensafely exec ehrql:v1 generate-dataset dataset_definition_cases.py --output fixtures/input_cases.csv
opensafely exec ehrql:v1 generate-dataset dataset_definition_controls.py --output fixtures/input_controls.csv

opensafely exec ehrql:v1 generate-dataset dataset_definition_cases.py --output fixtures/input_cases.csv.gz
opensafely exec ehrql:v1 generate-dataset dataset_definition_controls.py --output fixtures/input_controls.csv.gz

opensafely exec ehrql:v1 generate-dataset dataset_definition_cases.py --output fixtures/input_cases.arrow
opensafely exec ehrql:v1 generate-dataset dataset_definition_controls.py --output fixtures/input_controls.arrow
