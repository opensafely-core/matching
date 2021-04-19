
```yaml
inputs: 
  cases: input_cases.csv
  controls: input_control.csv
config:
  matches_per_case: 3
  match_variables: 
    sex: category 
    age: 5
  index_variable: indexdate
  closest_match_columns: [age]
  input_path: tests/test_data
  output_path: tests/test_1/test_output
```