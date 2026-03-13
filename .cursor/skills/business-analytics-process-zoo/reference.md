# Business Analytics — Reference (Questions, Zoo Glossary)

## Question Bank by Phase

### Before defining a process
- What is the name and goal of this process?
- Who starts it (role and trigger)?
- What must be true before it can run (preconditions)?
- What does “success” look like? What is stored or updated?
- Who else is involved (other roles, systems)?

### When designing steps
- What is the exact action the user performs? (verb + object)
- Are there decisions in the flow? What are the criteria and outcomes?
- What validations run before or during the step? What message or state when they fail?
- Can this step be skipped or repeated? Under what conditions?

### Zoo-specific discovery
- **Admission**: Is a health check required for this animal/source? Who decides “suitable enclosure”? What if there is no suitable enclosure?
- **Feeding**: Who may execute a feeding round? What if the enclosure is empty? What if the time is wrong or the zookeeper is not assigned?
- **Health check**: Who can perform it? What result values exist? What happens for each (follow-up, escalation, block admission)?
- **Zookeeper assignment**: Can one zookeeper have multiple enclosures? What happens to the previous zookeeper when reassigning?
- **Tours**: How is the route defined and changed? What happens if an enclosure is closed or a guide is unavailable?

### Edge cases and exceptions
- What happens when a required resource is missing (enclosure, zookeeper, veterinarian, guide)?
- What happens when the same operation is attempted twice (e.g. admit same animal again, assign same zookeeper)?
- Are there time or ordering constraints (e.g. feeding only at scheduled time, tour in route order)?

---

## Zoo Keeper Domain — Glossary

| Term | Meaning |
|------|--------|
| **Admission** | Process of registering an animal and placing it in a suitable enclosure, optionally after a health check; may include assigning a zookeeper to the enclosure. |
| **Enclosure** | A contained area in the zoo for housing animals; has type/suitability (e.g. mammal, bird, reptile); can have one assigned zookeeper. |
| **Suitable enclosure** | Enclosure that matches the animal’s species/type and any other zoo rules; animal can only be placed in a suitable enclosure. |
| **Feeding round** | Execution of feeding for one enclosure at a scheduled time by the zookeeper assigned to that enclosure; recorded when completed. |
| **Feeding schedule** | Per enclosure: time(s) and diet; defines when a feeding round is “due”. |
| **Health check** | Examination of an animal by a veterinarian; result (e.g. Healthy, Need follow-up, Critical) is recorded; may be required before admission or trigger follow-up/quarantine. |
| **Cleared / Not cleared** | Health check outcome for admission: cleared → animal can be placed; not cleared → admission blocked, quarantine or follow-up. |
| **Assign zookeeper** | Zoo manager links a zookeeper to an enclosure; that zookeeper is responsible for feeding and care; at most one zookeeper per enclosure. |
| **Guided tour** | A guide leads visitors along a defined route (ordered list of enclosures); tour is complete when all enclosures in the route are visited. |
| **Tour route** | Ordered list of enclosures that the guide visits in sequence. |
| **Registered (animal)** | Animal is in the system but not yet placed in an enclosure (e.g. before admission or when admission failed). |

---

## Process–Scenario Alignment

When writing BDD scenarios from a process:

- **Given**: Preconditions and current state (enclosures, animals, assignments, schedules, roles).
- **When**: One main action by one actor (admit, execute feeding, conduct health check, assign zookeeper, start tour).
- **Then**: Observable outcome (state changes, records, messages) and optional side effects (e.g. “admission complete”, “feeding recorded as completed”).

Cover at least: happy path, one or two main decision branches (e.g. health cleared vs not cleared), and one or two failure paths (e.g. no suitable enclosure, zookeeper not assigned). Use the glossary so scenario language matches the domain.
