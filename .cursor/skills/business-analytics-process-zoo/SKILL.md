---
name: business-analytics-process-zoo
description: Supports business analysis by asking clarifying and discovery questions, designing and improving business processes, and applying zoo keeper domain knowledge (enclosures, animals, zookeepers, veterinarians, guides, admission, feeding, health checks, tours). Use when gathering requirements, designing or mapping processes, writing user stories or BDD scenarios, or working in zoo/wildlife care operations.
---

# Business Analytics — Questions, Process Design, Zoo Keeper Domain

Apply this skill when doing business analysis: discovering requirements, designing or improving processes, or working in the zoo keeper domain. The agent asks good questions, designs clear processes, and uses consistent zoo/keeper terminology.

## When to Apply

- Eliciting or clarifying requirements (stakeholders, goals, rules, exceptions)
- Designing or mapping business processes (flows, actors, decisions, outcomes)
- Writing or refining user stories, acceptance criteria, or BDD scenarios (e.g. Gherkin)
- Discussing zoo operations: admission, feeding, health checks, zookeeper assignment, guided tours
- Identifying edge cases, validation rules, or missing steps in a process

---

## Asking Good Questions

Ask questions that clarify scope, actors, rules, and exceptions. Prefer concrete, scenario-based questions over vague ones.

### Discovery and scope
- **Goal**: What is the process trying to achieve? Who benefits?
- **Trigger**: What starts the process? (e.g. new animal arrives, scheduled time, manager action)
- **Outcome**: What does “done” look like? What is recorded or updated?
- **Who**: Which roles initiate, perform, or approve steps? (zoo manager, zookeeper, veterinarian, guide)

### Rules and validation
- **Preconditions**: What must be true before the process can run? (e.g. enclosure exists and is suitable; zookeeper is employed)
- **Business rules**: What is allowed or forbidden? (e.g. one zookeeper per enclosure; health check required for external arrivals)
- **Decisions**: Where does the flow branch? (e.g. health check cleared vs not cleared; feeding due vs not due)

### Exceptions and edge cases
- **Failure paths**: What happens when validation fails? (e.g. no suitable enclosure → admission fails; zookeeper not assigned → feeding round blocked)
- **Missing resources**: No enclosure, no free zookeeper, no guide — how should the system respond?
- **Reassignment and overrides**: Can a zookeeper be reassigned? Can a manager override a rule? When?

### Zoo-domain specifics
- **Suitability**: How is “suitable enclosure” defined? (species, space, safety)
- **Health vs admission**: When is a health check required before admission? When is quarantine or follow-up needed?
- **Feeding**: Who can execute a feeding round? What if the enclosure is empty or the time is wrong?
- **Tours**: What defines a route? What if a guide is unavailable at tour time?

Use these question types to fill gaps before writing scenarios or process diagrams.

---

## Designing Business Processes

Structure processes so they are testable and map cleanly to BDD scenarios and BPMN.

1. **Name the process** and state the **goal** and **primary actor** (e.g. “Animal Admission”, goal: house animal and assign caretaker; actor: zoo manager).
2. **Identify triggers** (e.g. new animal registered, external transfer, in-zoo birth).
3. **List main steps** in order: validation → optional sub-processes (e.g. health check) → core action (e.g. place in enclosure, assign zookeeper) → recording.
4. **Mark decision points** and outcomes (e.g. health cleared → admit; not cleared → quarantine/follow-up; no suitable enclosure → fail with clear message).
5. **Define exception paths**: validation failures, missing resources, role violations — each with a clear system response.
6. **State postconditions**: what is persisted or updated (e.g. animal in enclosure, zookeeper assigned, admission complete).

Align process steps with Given/When/Then: **Given** preconditions and state, **When** actor performs action, **Then** observable outcome and system state.

---

## Zoo Keeper Domain — Core Concepts

Use this terminology consistently in questions, process design, and scenarios.

### Actors
- **Zoo manager**: Admits animals, assigns zookeepers to enclosures, oversees operations.
- **Zookeeper**: Assigned to one or more enclosures; executes feeding rounds, daily care.
- **Veterinarian**: Performs health checks; results drive admission (cleared/not cleared) and follow-up.
- **Guide**: Leads guided tours along a defined route of enclosures.

### Key entities
- **Zoo**: Top-level; has enclosures and employees.
- **Enclosure**: Has type/suitability (e.g. for mammals, birds, reptiles); holds animals; has at most one assigned zookeeper.
- **Animal**: Has species/type (mammal, bird, reptile); may be “registered but not in enclosure”; placed in a suitable enclosure after admission.
- **Feeding schedule**: Per enclosure; time and diet (e.g. 10:00, meat); feeding round “due” at that time.
- **Tour route**: Ordered list of enclosures; guide visits in sequence.

### Processes (align with project features)
1. **Animal admission**: Register animal → optional health check (if required) → if cleared, place in suitable enclosure → assign or keep zookeeper for enclosure. Fail if no suitable enclosure or health not cleared (quarantine/follow-up).
2. **Feeding round**: Zookeeper executes feeding for assigned enclosure at scheduled time; recorded as completed; blocked if zookeeper not assigned to enclosure or time not due.
3. **Health check**: Veterinarian examines animal; result (Healthy / Need follow-up / Critical) recorded; may trigger follow-up or escalation.
4. **Assign zookeeper**: Manager assigns zookeeper to enclosure; one zookeeper per enclosure; reassignment replaces previous. Fails if enclosure or zookeeper not part of zoo.
5. **Guided tour**: Guide follows route in order; tour completed when all enclosures visited; fails to start if no guide available.

### Common rules
- Enclosure suitability by species/type; animal only in suitable enclosure.
- At most one zookeeper per enclosure; zookeeper must be zoo employee.
- Feeding round only by zookeeper assigned to that enclosure; only at scheduled time (or as defined).
- Health check can be required before admission; “not cleared” blocks placement and may imply quarantine or follow-up.

---

## Outputs and Next Steps

- **User stories**: “As a [role], I want [action] so that [benefit]” — one per process or variant.
- **BDD scenarios**: Given/When/Then with concrete data (enclosure names, animal names, roles); cover happy path, key decisions, and main failure/exception paths.
- **Process maps**: BPMN or Mermaid flowcharts with actors, steps, and decision points (see architect skill for diagram syntax).

For detailed question lists and zoo glossary, see [reference.md](reference.md).
