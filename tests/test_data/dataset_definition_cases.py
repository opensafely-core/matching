from ehrql import create_dataset
from ehrql.tables.core import clinical_events, ons_deaths, patients
from ehrql.tables.tpp import apcs, practice_registrations


start_date = "2020-01-01"

dataset = create_dataset()
dataset.configure_dummy_data(population_size=20, timeout=120)

dataset.sex = patients.sex
dataset.age = patients.age_on(start_date)
dataset.indexdate = apcs.sort_by(apcs.admission_date).first_for_patient().admission_date

registration = practice_registrations.for_patient_on(start_date)
dataset.stp = registration.practice_stp
dataset.practice_id = registration.practice_pseudo_id
dataset.region = registration.practice_nuts1_region_name

dataset.has_diagnosis = clinical_events.where(
    clinical_events.snomedct_code.is_in(
        ["1064811000000103", "1064811000000104", "1064811000000105"]
    )
).exists_for_patient()
dataset.died_date_ons = ons_deaths.date
dataset.previous_event = (
    clinical_events.where(clinical_events.date > "2024-12-31")
    .sort_by(clinical_events.date)
    .first_for_patient()
    .date
)

dataset.define_population(
    dataset.indexdate.is_on_or_between("2020-01-01", "2024-12-31")
    & (dataset.age > 16)
    & (dataset.died_date_ons > start_date)
    & dataset.has_diagnosis
    & (dataset.region == "North West")
)
