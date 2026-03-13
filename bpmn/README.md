# BPMN Diagrams — Zoo Management System

Valid BPMN 2.0 XML diagrams for the five core business processes.  
Import into [BPMN.io](https://bpmn.io) (or any BPMN 2.0–compliant tool) for viewing and editing.

## Files

| File | Process | Description |
|------|---------|-------------|
| `01_animal_admission.bpmn` | Animal Admission to Enclosure | New animal → optional health check → place in enclosure → assign zookeeper |
| `02_execute_feeding_round.bpmn` | Execute Feeding Round | Schedule trigger → select enclosure → feed animals → record completed |
| `03_conduct_health_check.bpmn` | Conduct Health Check | Request → examine animal → record result → Healthy / Follow-up / Critical |
| `04_assign_zookeeper.bpmn` | Assign Zookeeper to Enclosure | Identify enclosure and zookeeper → validate → create association → confirm |
| `05_conduct_guided_tour.bpmn` | Conduct Guided Tour | Schedule tour → assign guide → get route → start → visit enclosures → end |

## How to use in BPMN.io

1. Open [https://demo.bpmn.io](https://demo.bpmn.io) (or your BPMN.io–based editor).
2. Use **File → Open** (or drag-and-drop) and select one of the `.bpmn` files.
3. The diagram will load with tasks, exclusive gateways, and end events laid out.
4. Edit as needed and export again as BPMN 2.0 XML.

## Relationship to other docs

- **Process definitions:** `docs/business-processes-detailed.md`
- **BDD scenarios:** `docs/bdd-scenarios.md` and `features/*.feature`

The BPMN flows match the steps and gateways described in the business process definitions and underpin the BDD scenarios.
