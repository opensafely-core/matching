from ehrql import create_dataset
from ehrql.tables.core import clinical_events, patients


start_date = "2020-01-01"

dataset = create_dataset()
dataset.configure_dummy_data(population_size=20)

dataset.sex = patients.sex
dataset.age = patients.age_on(start_date)
dataset.indexdate = (
    clinical_events.sort_by(clinical_events.date).first_for_patient().date
)

dataset.has_diagnosis = clinical_events.where(
    clinical_events.snomedct_code.is_in(
        ["1064811000000103", "1064811000000104", "1064811000000105"]
    )
).exists_for_patient()


dataset.define_population(
    dataset.indexdate.is_on_or_after(start_date) & dataset.has_diagnosis
)
