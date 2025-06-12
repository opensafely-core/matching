[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7691460.svg)](https://doi.org/10.5281/zenodo.7691460)

# Simple categorical and scalar variable matching

This tool matches patients in one `.csv` to a specified number of matches in another `.csv`. It does this according to a specified list of categorical and/or scalar variables. 

## Methodological notes
This is a work in progress and is implemented for one or two specific study designs, but is intended to be generalisable to other projects, with new features implemented as needed.

- The algorithm currently does matching without replacement. Implementing an option for with replacement should be relatively easy. Make an issue if you need it.
- For a scalar variable, where a range is specified (e.g. within 5 years when matching on age), the algorithm can optionally (see `closest_match_variables`) use a greedy matching algorithm to find the closest match. Greedy matching is where the best match is found for each patient sequentially. This means that later matches may end up with less close matches due to having a smaller pool of potential matches.
- Matches are made in order of the index date of the case/exposed group. This is done to eliminate biases caused by matching people "from the future" before matching people whose index date is earlier. Ask Krishnan Bhaskaran for a more complete/better explanation.
- Cases that do not get the specified number of matches (as specified by `matches_per_case`) are retained by default. This can be changed using the `min_matches_per_case` option.
- Matches are picked at random, but with a set seed, meaning that running twice on the same dataset should yield the same results.
- This was originally implemented by passing a dictionary of options to the function - this is still possible - see [here](#passing-a-dict-of-options-instead).

## System requirements

Requires Python 3.8+

Install with:

```
pip install opensafely-matching
```

## Input data
This is expected to be in two CSVs - one `case_csv` for the case/exposed group and one `match_csv` for the population to be matched. These data must have all the variables that are specified in arguments when running, and can have any number of other variables (all of which are returned in the [output](#outputs) CSVs).

## Use

Matching is run by calling the match function with at least the required arguments, as per:
```py
from osmatching import match

match(
    case_csv="input_cases",
    match_csv="input_matches",
    matches_per_case=3,
    match_variables={
        "sex": "category",
        "age": 5,
    },
    index_date_variable="indexdate",
)
```
This matches 3 matches per case, on the variables `sex`, and `age` (±5 years).\
**Outputs:**\
`output/matched_cases.csv`\
`output/matched_matches.csv`\
`output/matched_combined.csv`\
`output/matching_report.txt`

### Required arguments

`case_csv`\
The name of the CSV containing case/exposed population.

`match_csv`\
The name of the CSV containing the population of patients to match onto the case/exposed population.

`matches_per_case`\
The integer number of matches to match to each case/exposed patient, where possible.

`match_variables`\
A Python dictionary containing a list of variables to match on as keys, while the associated values denote the type of match:
- `"category"` - a categorical variable (e.g. sex)
- _integer number_ - an integer scalar value that identifies the variable as a scalar, and sets the matching range (e.g. `0` for exact matches, `5` for matches within ±5)
- _float number_ - **not yet implemented**, make an issue if you need it, it should be straightforward.
- `"month_only"`  - a specially implemented categorical variable that extracts the month from a date variable (which should be in the format `"YYYY-MM-DD"`)

`index_date_variable`\
A string variable (format: "YYYY-MM-DD") relating to the index date for each case.


### Optional arguments

`closest_match_variables`(default: `None`)\
A Python list (e.g `["age", "months_since_diagnosis"]`) containing variables that you want to find the closest match on. The order given in the list determines the priority of sorting (first is highest priority).

`date_exclusion_variables`(default: `None`)\
A Python dictionary containing a list of date variables (as keys) to use to exclude patients, relative to the index date. Patients who have a date in the specified variable either `"before"` or `"after"` the index date are excluded. `"before"` or `"after"` is indicated by the values in the dictionary for each variable.

`min_matches_per_case` (default: 0)\
An integer that determines the minimum number of acceptable matches for each case. Sets of cases and matches where there are fewer than the specified number are dropped from the output data.

`replace_match_index_date_with_case` (default: `None`)\
When using for example a general population control, the match patients may not have an index date - meaning you want to pass the date from the case/exposed patient. This can be:
- the exact same date as the case - specified by `"no_offset"`
- with an offset in the format: `"n_unit_direction"`, where:
  - `n` is an integer number
  - `unit` is `year`, `month` or `day`
  - `direction` is `earlier` or `later`
  - For example: `1_year_earlier`.


`indicator_variable_name` (default: `"case"`)\
A binary variable (`0` or `1`) is included in the output data to indicate whether each patient is a "case" or "match". The default is set to fit the nomenclature of a case control study, but this might be changed to for example `"exposed"` to fit better with a cohort study.

`output_suffix` (default: `""`)\
If you are matching on multiple populations within the same project, you may want to specify a suffix to identify each output and prevent them being overwritten.

`output_path` (default: `"output"`)\
The folder where the outputs (CSVs and matching report) should be saved.

`drop_cases_from_matches` (default: `False`)\
If `True`, all `patient_id`s in the case CSV are dropped from the match CSV before matching starts.

## Outputs

### Datasets
All the below data outputs contain all of the columns that were in the input CSVs, plus:

- `set_id` - a variable identifying the groups of matched cases and matches. It is the same as the patient ID of the case.

- `case` - a binary variable (`0` or `1`) to indicate whether each patient is a "case" or "match". This is named `case` by default, but the name can be user defined (see `indicator_variable_name` above).

`{output_path}/matched_cases{output_suffix}.csv`\
Contains all the cases that were matched to the specified number of matches.


`{output_path}/matched_matches{output_suffix}.csv`\
Contains all the matches that were matched to cases/exposed patients.

`{output_path}/matched_combined{output_suffix}.csv`\
Contains the two datasets above appended together.

### Matching report
`{output_path}/matching_report{output_suffix}.txt`
This contains patient counts for each stage of the matching process, then basic summary stats about the matched populations. For example:
```
Matching started at: 2020-11-26 18:54:52.447761

CSV import:
Completed 2020-11-26 18:54:52.493762
Cases    100
Matches  10000

Dropping cases from matches:
Completed 2020-11-26 18:54:52.495763
Cases    100
Matches  9900

Completed pre-calculating indices at 2020-11-26 18:54:52.512761

Date exclusions for cases:
Completed 2020-11-26 18:54:52.514762
Cases    54
Matches  9900

After matching:
Completed 2020-11-26 18:54:53.027267
Cases    53
Matches  106

Number of available matches per case:
2.0    53
1.0     1

age comparison:
Cases:
count    53.000000
mean     40.301887
std      21.905027
min       1.000000
25%      23.000000
50%      43.000000
75%      58.000000
max      82.000000
Matches:
count    106.000000
mean      40.254717
std       21.783376
min        1.000000
25%       23.250000
50%       43.000000
75%       58.000000
max       83.000000
```

## More examples
Match COVID population to pneumonia population with:
 - 1 match
 - matching on sex, age, stp (an NHS administrative region), and the month of the index date.
 - greedy matching on age 
 - excluding patients who died or had various outcomes before their index date
```py
from osmatching import match

match(
    case_csv="input_covid",
    match_csv="input_pneumonia",
    matches_per_case=1,
    match_variables={
        "sex": "category",
        "age": 1,
        "stp": "category",
        "indexdate": "month_only",
    },
    index_date_variable="indexdate",
    closest_match_variables=["age"],
    date_exclusion_variables={
        "died_date_ons": "before",
        "previous_vte_gp": "before",
        "previous_vte_hospital": "before",
        "previous_stroke_gp": "before",
        "previous_stroke_hospital": "before",
    },
    output_suffix="_pneumonia",
    output_path="test_data",
)
```
**Outputs:**\
`output/matched_cases_pneumonia.csv`\
`output/matched_matches_pneumonia.csv`\
`output/matched_combined_pneumonia.csv`\
`output/matching_report_pneumonia.txt`

---

Match COVID population to general population from 2019 with:
 - 2 matches
 - matching on sex, age, stp (an NHS administrative region).
 - greedy matching on age 
 - excluding patients who died or had various outcomes before their index date
 - case/match groups where there isn't at least one match are excluded
```py
from osmatching import match

match(
    case_csv="input_covid",
    match_csv="input_control_2019",
    matches_per_case=2,
    match_variables={
        "sex": "category",
        "age": 1,
        "stp": "category",
    },
    index_date_variable="indexdate",
    closest_match_variables=["age"],
    min_matches_per_case=1,
    replace_match_index_date_with_case="1_year_earlier",
    date_exclusion_variables={
        "died_date_ons": "before",
        "previous_vte_gp": "before",
        "previous_vte_hospital": "before",
        "previous_stroke_gp": "before",
        "previous_stroke_hospital": "before",
    },
    output_suffix="_control_2019",
    output_path="test_data",
)
```
**Outputs:**\
`output/matched_cases_control_2019.csv`\
`output/matched_matches_control_2019.csv`\
`output/matched_combined_control_2019.csv`\
`output/matching_report_control_2019.txt`

---

Match COVID population to general population from 2020 with:
 - 2 matches
 - matching on sex, age, stp (an NHS administrative region).
 - greedy matching on age 
 - excluding patients who died or had various outcomes before their index date
```py
from osmatching import match

match(
    case_csv="input_covid",
    match_csv="input_control_2020",
    matches_per_case=2,
    match_variables={
        "sex": "category",
        "age": 1,
        "stp": "category",
    },
    closest_match_variables=["age"],
    replace_match_index_date_with_case="no_offset",
    index_date_variable="indexdate",
    date_exclusion_variables={
        "died_date_ons": "before",
        "previous_vte_gp": "before",
        "previous_vte_hospital": "before",
        "previous_stroke_gp": "before",
        "previous_stroke_hospital": "before",
    },
    output_suffix="_control_2020",
    output_path="test_data",
)
```
**Outputs:**\
`output/matched_cases_control_2020.csv`\
`output/matched_matches_control_2020.csv`\
`output/matched_combined_control_2020.csv`\
`output/matching_report_control_2020.txt`

## Passing a dict of options instead
Originally this was run by passing a Python dictionary to the function. This is still possible:
```py
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
    "closest_match_variables": ["age"],
    "index_date_variable": "indexdate",
    "date_exclusion_variables": {
        "died_date_ons": "before",
        "previous_vte_gp": "before",
        "previous_vte_hospital": "before",
        "previous_stroke_gp": "before",
        "previous_stroke_hospital": "before",
    },
    "output_suffix": "pneumonia",
    "output_path": "test_data",
}
match(**pneumonia)
```
