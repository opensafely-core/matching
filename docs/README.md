# Matching Action 

### Action Summary
This is an action that can be called into the 
`project.yaml`. It matches cases and controls. 
It requires two input csv files, one for cases, and one 
for controls. 

There are a few options on how to match which will be covered
further down. 

### Using Matching Action 
The following example blocks should be included 
in the `project.yaml` file. 

Example `project.yaml`
```yaml 
actions: 
  match_cohorts:
    run: match:latest --cases input_case.csv --controls input_controls.csv
config:
  matches_per_case: 3
  match_variables:
    sex: category
    age: 5
  index_variable: indexdate
  closest_match_columns:
      - age
  input_path: tests/test_data
  output_path: tests/test_output/test_1
```

### Methodological notes
This is a work in progress and is implemented for one or two specific study designs, but is intended to be generalisable to other projects, with new features implemented as needed.

- The algorithm currently does matching without replacement. Implementing an option for with replacement should be relatively easy. Make an issue if you need it.
- For a scalar variable, where a range is specified (e.g. within 5 years when matching on age), the algorithm can optionally (see `closest_match_variables`) use a greedy matching algorithm to find the closest match. Greedy matching is where the best match is found for each patient sequentially. This means that later matches may end up with less close matches due to having a smaller pool of potential matches.
- Matches are made in order of the index date of the case/exposed group. This is done to eliminate biases caused by matching people "from the future" before matching people whose index date is earlier. Ask Krishnan Bhaskaran for a more complete/better explanation.
- Cases that do not get the specified number of matches (as specified by `matches_per_case`) are retained by default. This can be changed using the `min_matches_per_case` option.
- Matches are picked at random, but with a set seed, meaning that running twice on the same dataset should yield the same results.
- This was originally implemented by passing a dictionary of options to the function - this is still possible - see [here](#passing-a-dict-of-options-instead).


### Matching Configuration Options
#### Required Arguments
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

#### Optional arguments

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

`input_path` (default: `"inputs"`)
The folder where the input csv files are. Specifying this in the 
yaml means you don't have to type a path when calling the action. 

`drop_cases_from_matches` (default: `False`)\
If `True`, all `patient_id`s in the case CSV are dropped from the match CSV before matching starts.
