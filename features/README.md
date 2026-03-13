# BDD Feature Files

Gherkin feature files for the Zoo Management System, one per business process.

| File | Process |
|------|--------|
| `animal_admission.feature` | Process 1: Animal Admission to Enclosure |
| `feeding_round.feature` | Process 2: Execute Feeding Round |
| `health_check.feature` | Process 3: Conduct Health Check |
| `assign_zookeeper.feature` | Process 4: Assign Zookeeper to Enclosure |
| `guided_tour.feature` | Process 5: Conduct Guided Tour |

## Running the scenarios

- **pytest-bdd**: Implement step definitions in `tests/` (e.g. `tests/step_defs/`) and run:  
  `pytest features/ -v`
- **behave**: Place step definitions in `steps/` next to `environment.py` and run:  
  `behave features/`

See project README and `docs/bdd-scenarios.md` for scenario descriptions and mapping to business processes.
