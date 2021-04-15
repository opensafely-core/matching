
```yaml
inputs: 
  cases: tests/test_data/input_cases.csv
  controls: tests/test_data/input_control.csv
config:
  matches_per_case: 3
  match_variables: 
    sex: category 
    age: 5
  index_variable: indexdate
  closest_match_columns: [age]
```