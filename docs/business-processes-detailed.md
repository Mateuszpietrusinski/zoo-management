# Zoo Management System — Detailed Business Process Definitions

Each process is defined one at a time with triggers, steps, actors, decisions, and domain mapping.

**Resolved business rules (from business analysis, see PRD §5 and §8):**

- **Health check for admission:** Required when animal **origin is "external"** (delivery, transfer); not required when **origin is "internal"** (e.g. in-zoo birth). Animal or admission request carries `origin: external | internal`.
- **Enclosure suitability:** Enclosure type must match animal’s taxonomic type (Mammal, Bird, Reptile). Enclosure has type (e.g. mammal, bird, reptile); animal type from class hierarchy.
- **Feeding “due”:** Exact time match with scheduled time (no tolerance window for MVP).
- **Admission initiator:** Only **zoo manager** initiates admission.
- **Zookeeper–enclosure:** At most one zookeeper per enclosure; one zookeeper may be assigned to multiple enclosures.
- **Tour route:** One default tour route per zoo (ordered list of enclosures).
- **Records for MVP:** AdmissionRecord, HealthCheckRecord, and Tour (guide, route, start/end time) are required as persisted entities.

---

## Process 1: Animal Admission to Enclosure

### Purpose
Formally register a new animal in the zoo, ensure it is medically cleared (if required), place it in a suitable enclosure, and assign a responsible zookeeper.

### Trigger
- New animal arrives at the zoo (delivery, transfer, or birth on-site).
- **Zoo manager** records the request to admit the animal (only zoo manager initiates admission).

### Actors / Roles
| Role | Responsibility |
|------|----------------|
| **Zoo manager** | Initiates admission; records request; selects enclosure; assigns zookeeper if needed. |
| **Zoo** (system/organization) | Owns enclosures, employs staff, validates admission. |
| **Veterinarian** | Performs health check and clears (or flags) the animal when origin is external. |
| **Zookeeper** | Will be assigned to manage the enclosure where the animal is placed. |

### Preconditions
- At least one **Enclosure** exists and is suitable for the animal’s species/type (e.g. predator enclosure for Lion, aviary for Eagle).
- The **Zoo** has at least one **Zookeeper** and (for health check) one **Veterinarian** available.
- The **Animal** instance is created (species, name, etc.) but not yet assigned to an enclosure.

### Main Flow (Steps)

1. **Record admission request**  
   - Input: animal data (species, name, origin, etc.).  
   - Output: admission request registered; **Animal** object exists in the system.

2. **Determine if health check is required**  
   - **Rule (resolved):** Health check required when animal **origin is "external"** (delivery, transfer from outside); not required when **origin is "internal"** (e.g. in-zoo birth). Animal or admission request must have `origin: external | internal`.  
   - Decision (gateway): *Health check required?*

3. **Perform health check** (if yes)  
   - **Veterinarian** examines the animal (in temporary holding or designated area).  
   - Result: *Cleared* or *Not cleared* (e.g. quarantine, treatment needed).  
   - If not cleared: process can end with “Animal not admitted” or “Held for quarantine” (exception path).

4. **Select suitable enclosure**  
   - Zoo manager or system selects an **Enclosure** by criteria: **enclosure type matches animal’s taxonomic type** (Mammal, Bird, Reptile).  
   - Validation: enclosure exists, is part of the **Zoo**, and its type is appropriate for the animal (e.g. mammal enclosure for Lion, aviary for Eagle).

5. **Place animal in enclosure**  
   - Animal is added to the enclosure’s list of animals (aggregation: Enclosure ◇── Animal).  
   - Enclosure state is updated (e.g. animal count, capacity).

6. **Assign zookeeper to enclosure** (if not already assigned)  
   - **Zoo** assigns a **Zookeeper** to manage this **Enclosure** (association: Zookeeper ── Enclosure).  
   - If the enclosure already has an assigned zookeeper, skip or confirm.

7. **Confirm admission**  
   - Record that admission is complete; animal is now “in zoo” and managed.  
   - Optional: notify feeding schedule to include new animal.

### Gateways / Decisions
- **Health check required?** (after step 1) → Yes → step 3; No → step 4.  
- **Animal cleared?** (after step 3) → Yes → step 4; No → exception (quarantine / not admitted).  
- **Enclosure already has zookeeper?** (before step 6) → Yes → skip assignment; No → assign zookeeper.

### Exception / Alternative Paths
- Health check not passed → animal not admitted or moved to quarantine (separate process or end state).  
- No suitable enclosure available → admission postponed or exception handling (e.g. create/allocate enclosure).

### Postconditions
- **Animal** is associated with exactly one **Enclosure** (aggregation).  
- **Enclosure** is part of **Zoo** (composition).  
- At least one **Zookeeper** is associated with that **Enclosure** (association).  
- **Animal** is in a state “admitted” / “in enclosure”.

### Data / Objects Involved
- **Animal** (concrete type: Lion, Elephant, Eagle, etc.; **origin: external | internal** for admission).  
- **Enclosure** (id, type/category e.g. mammal/bird/reptile, capacity).  
- **Zoo** (owns enclosures, employs employees).  
- **Veterinarian**, **Zookeeper** (Employee subclasses).  
- **AdmissionRecord** (required for MVP): date, animal, enclosure, zookeeper, vet (if health check performed).

### Domain Model Mapping
- **Composition:** Zoo ◆── Enclosure (select enclosure from zoo).  
- **Aggregation:** Enclosure ◇── Animal (add animal to enclosure); Zoo ◇── Employee (vet, zookeeper).  
- **Association:** Zookeeper ── Enclosure (assign zookeeper to enclosure).  
- **Inheritance:** Animal hierarchy (Mammal/Bird/Reptile); Employee hierarchy (Zookeeper, Veterinarian).  
- **Polymorphism:** “Suitable enclosure” and “health check” can depend on concrete animal type.  
- **Abstraction:** Animal (ABC); Employee (ABC).

---

## Process 2: Execute Feeding Round

### Purpose
Ensure animals in an enclosure are fed according to the zoo’s feeding schedule, with a zookeeper performing the feeding for a specific enclosure at the scheduled time.

### Trigger
- **FeedingSchedule** indicates that a given **Enclosure** (or animal group) is due to be fed at a certain time (e.g. 10:00 for Lion Enclosure).
- Trigger can be time-based (scheduler) or manual (staff initiates “feeding round” for an enclosure).

### Actors / Roles
| Role | Responsibility |
|------|----------------|
| **Zookeeper** | Executes the feeding: retrieves schedule, goes to enclosure, feeds animals. |
| **FeedingSchedule** | Defines what, when, and for which enclosure/animals. |
| **Enclosure** | Contains the animals to be fed. |

### Preconditions
- A **FeedingSchedule** exists for the enclosure (or for the animal types in that enclosure) with a time slot that is due.
- The **Zookeeper** is assigned to that **Enclosure** (association) or is otherwise authorized to feed there.
- **Enclosure** contains at least one **Animal** (aggregation).
- Feeding supplies (food) are available — can be assumed or modeled as a simple check.

### Main Flow (Steps)

1. **Retrieve feeding schedule for enclosure**  
   - Zookeeper triggers a feeding round for a **specific enclosure** (API: `POST /enclosures/{enclosure_id}/feeding-rounds`); the enclosure is already identified from the request.  
   - Retrieve the **FeedingSchedule** for that enclosure: scheduled time, diet type / portion.  
   - Encapsulation: schedule details (e.g. diet, frequency) are properties of **FeedingSchedule**.

2. **Check feeding due**  
   - **Rule (resolved):** Feeding is due when current time **exactly matches** the scheduled time (no tolerance window for MVP).  
   - Gateway: *Current time = scheduled time?* → No → end “Not due / Feeding not executed”; Yes → continue.

3. **Check zookeeper assigned to enclosure**  
   - Validate that the requesting **Zookeeper** is assigned to this **Enclosure** (association Zookeeper–Enclosure).  
   - Gateway: *Zookeeper assigned?* → No → abort “Zookeeper not assigned”; Yes → continue.

4. **Feed animals in enclosure**  
   - Gateway: *Any animals in enclosure?* → No → skip to recording (note: “no animals to feed”); Yes → proceed.  
   - For each **Animal** in the enclosure (aggregation), apply feeding (e.g. mark as fed, or record feed event).  
   - Polymorphism: different animal types have different feeding behavior (e.g. `get_diet_type()`).

5. **Record feeding completed**  
   - Create a record: feeding for this enclosure at this time is done (including “no animals to feed” case).  
   - Optional: update animal or enclosure state (e.g. “last_fed_at”).

### Gateways / Decisions
- **Current time = scheduled time?** (after step 1) → No → end “Not due”; Yes → step 3.  
- **Zookeeper assigned to this enclosure?** (step 3) → No → abort; Yes → step 4.  
- **Any animals in enclosure?** (step 4) → No → record “no animals to feed”; Yes → perform feeding.

### Exception / Alternative Paths
- No schedule for enclosure → skip or create schedule (separate process).  
- Zookeeper not available → reassign or postpone (exception).  
- Animal refuses food / special case → log and optionally alert vet (optional branch).

### Postconditions
- Feeding for the selected enclosure at the given time is recorded as executed.  
- **Enclosure** and **Animal**(s) state reflect that feeding occurred (if modeled).  
- **FeedingSchedule** may have “last_executed” or equivalent updated.

### Data / Objects Involved
- **FeedingSchedule** (enclosure, time, diet/frequency).  
- **Zookeeper** (assigned to enclosure).  
- **Enclosure** (holds list of animals).  
- **Animal** (multiple; may implement feeding-related behavior).

### Domain Model Mapping
- **Aggregation:** Enclosure ◇── Animal (iterate animals to feed); Zoo ◇── Employee (zookeeper).  
- **Association:** Zookeeper ── Enclosure (zookeeper performs feeding at enclosure).  
- **Encapsulation:** FeedingSchedule holds schedule details; Enclosure holds animal list.  
- **Polymorphism:** Animal subclasses can override feeding-related methods.  
- **Inheritance:** Zookeeper extends Employee; Animal hierarchy.

---

## Process 3: Conduct Health Check

### Purpose
A veterinarian examines an animal (in its enclosure or in a treatment area) and records the result so the zoo can track health status and decide on follow-up (e.g. treatment, quarantine, or no action).

### Trigger
- **Scheduled** health check (e.g. monthly for elephants).  
- **On-demand**: animal shows signs of illness or injury; or post-admission check (see Process 1).  
- **Request** from zookeeper or curator to have an animal examined.

### Actors / Roles
| Role | Responsibility |
|------|----------------|
| **Veterinarian** | Performs examination, decides outcome, records result. |
| **Zoo** | Employs veterinarian; may assign which vet handles which area/animal. |
| **Enclosure** | Location where animal is kept (examination may be in enclosure or in clinic). |

### Preconditions
- **Animal** to be checked is in the system and assigned to an **Enclosure**.  
- At least one **Veterinarian** is available (employed by Zoo — aggregation).  
- Animal is accessible for examination (in enclosure or moved to treatment area; movement can be out of scope and assumed).

### Main Flow (Steps)

1. **Create or receive health check request**  
   - Input: animal (id or reference), reason (scheduled / on-demand), optional priority.  
   - Output: health check task created and assigned to a **Veterinarian**.

2. **Veterinarian retrieves animal record**  
   - Resolve the **Animal** to be examined (health check is performed on the animal).  
   - Optional: determine examination location (in enclosure vs. clinic).

3. **Perform examination**  
   - **Veterinarian** examines the animal.  
   - Polymorphism: examination logic can differ by animal type (e.g. Mammal vs. Bird vs. Reptile — different checks or risk factors).  
   - Abstraction: e.g. `Animal.perform_health_check(veterinarian)` or `Veterinarian.examine(animal)` with behavior depending on concrete animal class.

4. **Determine result**  
   - Outcome: **Healthy**, **Need follow-up**, or **Critical** (or similar).  
   - Gateway: result type drives next steps.

5. **Record result**  
   - Store result as **HealthCheckRecord** (required for MVP): date, animal, veterinarian, result (Healthy / Need follow-up / Critical), optional notes.  
   - Animal’s health-related state updated via methods/properties (e.g. last check date).

6. **Follow-up (conditional)**  
   - If **Need follow-up** or **Critical**: schedule treatment or alert (can be another process or end state “scheduled for treatment”).  
   - If **Healthy**: process ends.

### Gateways / Decisions
- **Examination result?** (after step 3) → Healthy → record and end; Need follow-up → record and schedule follow-up; Critical → record and escalate.  
- **Examination location?** (optional, step 2) → In enclosure vs. clinic (can be a simple task variant).

### Exception / Alternative Paths
- Animal cannot be safely examined → postpone and record reason.  
- Veterinarian unavailable → reassign or reschedule.

### Postconditions
- **Animal** has updated health status and/or last check date.  
- **HealthCheckRecord** is created (required for MVP).  
- If follow-up needed, a follow-up task or process is triggered (or documented).

### Data / Objects Involved
- **Animal** (concrete type: Lion, Elephant, Penguin, etc.).  
- **Veterinarian** (Employee subclass).  
- **Enclosure** (animal’s current location).  
- **HealthCheckRecord** (required for MVP): animal, vet, date, result (Healthy / Need follow-up / Critical), notes.

### Domain Model Mapping
- **Polymorphism:** Different animal types can have different examination behavior (e.g. different criteria or methods).  
- **Abstraction:** Animal (ABC) with abstract or overridable health-check-related method.  
- **Encapsulation:** Animal holds health state; Veterinarian holds examination logic.  
- **Aggregation:** Zoo ◇── Employee (Veterinarian); Enclosure ◇── Animal.  
- **Inheritance:** Veterinarian extends Employee; Animal subclasses (Mammal, Bird, Reptile).

---

## Process 4: Assign Zookeeper to Enclosure

### Purpose
Establish or change which zookeeper is responsible for managing a specific enclosure so that feeding, cleaning, and daily care are clearly assigned. At most one zookeeper per enclosure; one zookeeper may be assigned to multiple enclosures.

### Trigger
- **New zookeeper** joins and needs an enclosure assignment.  
- **Reorganization**: change of responsibility (e.g. swap enclosures between two zookeepers).  
- **New enclosure** opened and needs an assigned zookeeper.  
- **Coverage**: temporary assignment when usual zookeeper is absent.

### Actors / Roles
| Role | Responsibility |
|------|----------------|
| **Zoo** (management / system) | Decides and performs the assignment (Zookeeper ↔ Enclosure). |
| **Zookeeper** | Employee who will be associated with the enclosure. |
| **Enclosure** | The enclosure that will be managed by the zookeeper. |

### Preconditions
- **Zoo** exists and has at least one **Enclosure** (composition) and at least one **Zookeeper** (aggregation).  
- The **Enclosure** and **Zookeeper** are part of the same Zoo.  
- Optional: enclosure has no current zookeeper, or we allow reassignment (overwrite current association).

### Main Flow (Steps)

1. **Identify enclosure**  
   - Select the **Enclosure** that needs an assigned zookeeper (e.g. by id or name).  
   - Validate: enclosure belongs to Zoo (composition).

2. **Identify zookeeper**  
   - Select the **Zookeeper** to assign (e.g. by id or name).  
   - Validate: zookeeper is employed by Zoo (aggregation).

3. **Check current assignment (optional)**  
   - If enclosure already has an assigned zookeeper: decide whether to replace (reassignment) or keep.  
   - Gateway: *Replace existing assignment?* or *Enclosure already assigned?*

4. **Create or update association**  
   - Set association: **Zookeeper** ── **Enclosure**. One enclosure has at most one zookeeper; one zookeeper can be linked to multiple enclosures (e.g. enclosure.assigned_zookeeper = zookeeper, or zookeeper.assigned_enclosures.add(enclosure)).  
   - If replacing: remove or overwrite previous association for that enclosure.

5. **Confirm assignment**  
   - Record that the zookeeper is now responsible for the enclosure (e.g. for feeding rounds, daily checks).  
   - Optional: notify zookeeper or update duty roster.

### Gateways / Decisions
- **Enclosure already has assigned zookeeper?** → Yes → replace or abort; No → create new assignment.  
- **Zookeeper already at capacity?** (if one zookeeper can manage multiple enclosures) → Yes → choose different zookeeper or reassign; No → proceed.

### Exception / Alternative Paths
- Enclosure not found or not in Zoo → error, end.  
- Zookeeper not found or not employed by Zoo → error, end.  
- Policy: “one enclosure per zookeeper” and zookeeper already assigned → unassign from old enclosure first, then assign to new.

### Postconditions
- **Zookeeper** is associated with the **Enclosure** (association).  
- **Enclosure** “knows” its responsible zookeeper (and vice versa if bidirectional).  
- Any previous assignment for this enclosure (if replaced) is cleared.

### Data / Objects Involved
- **Zoo** (owns enclosures, employs employees).  
- **Enclosure** (id, type, optional: assigned_zookeeper).  
- **Zookeeper** (id, name, optional: assigned_enclosures or current_enclosure).

### Domain Model Mapping
- **Association:** Zookeeper ── Enclosure (main relationship demonstrated).  
- **Composition:** Zoo ◆── Enclosure (enclosure must belong to zoo).  
- **Aggregation:** Zoo ◇── Employee (zookeeper is employee).  
- **Inheritance:** Zookeeper extends Employee (ABC).

---

## Process 5: Conduct Guided Tour

### Purpose
A guide leads a group of visitors through a defined set of enclosures in order, providing information and ensuring a consistent visitor experience. The zoo has **one default tour route** (ordered list of enclosures) for MVP.

### Trigger
- **Scheduled** tour time (e.g. 11:00 daily).  
- **On-demand** tour requested by visitors (if supported).  
- **System or coordinator** assigns a guide and triggers “start tour”.

### Actors / Roles
| Role | Responsibility |
|------|----------------|
| **Guide** | Leads the tour, visits enclosures in sequence, presents animals. |
| **Zoo** | Has enclosures and employs the guide; may define tour route (ordered list of enclosures). |
| **Enclosure** | Stops on the tour; guide “visits” or “presents” each enclosure. |

### Preconditions
- **Zoo** has at least one **Guide** (aggregation: Zoo ◇── Employee, Guide subclass).  
- **Rule (resolved):** Zoo has **one default tour route** — ordered list of **Enclosure**(s) (e.g. [Savanna, Aviary, Reptile House]).  
- **Guide** is available at the scheduled time (no conflict with another tour or duty).

### Main Flow (Steps)

1. **Schedule or request tour**  
   - Input: tour time, optional group size or booking id.  
   - Output: tour slot created; guide assigned (if not already assigned in a previous step).

2. **Assign guide to tour**  
   - **Zoo** (or scheduler) assigns a **Guide** to this tour instance.  
   - Optional: guide has a default route or receives route for this tour.

3. **Get tour route**  
   - Retrieve the zoo’s **default tour route** (ordered list of enclosures).  
   - Enclosures are part of Zoo (composition).

4. **Start tour**  
   - Guide starts the tour (e.g. “Tour started” recorded).  
   - Visitors are with the guide (modeled only as “tour in progress” if no Visitor entity).

5. **Visit each enclosure (loop)**  
   - For each **Enclosure** in the route:  
     - Guide (and group) move to enclosure.  
     - Guide presents enclosure (and animals) — e.g. describe species, names, habits.  
     - Optional: record “visited” for this enclosure in this tour.  
   - Loop until all enclosures in route are visited.

6. **End tour**  
   - Guide ends the tour at the last enclosure or at a designated exit.  
   - Record: tour completed (time, guide, route).

### Gateways / Decisions
- **More enclosures in route?** (in loop) → Yes → next enclosure; No → end tour.  
- **Guide available?** (before step 2) → No → reschedule or assign different guide; Yes → proceed.

### Exception / Alternative Paths
- Enclosure temporarily closed → skip enclosure or alter route (optional branch in loop).  
- Guide unavailable at last minute → reassign guide or cancel tour.

### Postconditions
- **Tour** record is created (required for MVP): guide, route, start time, end time.  
- **Guide** has performed the tour; all enclosures in the route were “visited” in order.

### Data / Objects Involved
- **Guide** (Employee subclass).  
- **Zoo** (enclosures, employees; **default_tour_route**: ordered list of enclosures).  
- **Enclosure** (one or more, in order).  
- **Tour** (required for MVP): guide, route, start_time, end_time.

### Domain Model Mapping
- **Inheritance:** Guide extends Employee (ABC) — same as Zookeeper, Veterinarian.  
- **Association:** Guide ── Enclosure (or Guide ── Tour ── Enclosures): guide visits/presents enclosures.  
- **Composition:** Zoo ◆── Enclosure (route is list of zoo’s enclosures).  
- **Aggregation:** Zoo ◇── Employee (Guide).  
- **Encapsulation:** Tour route and tour state can be encapsulated in Zoo or in a Tour object.

---

## Summary Table

| Process                     | Trigger              | Main actor(s)     | Key domain objects              | Main relationship shown   |
|----------------------------|----------------------|-------------------|---------------------------------|---------------------------|
| Animal admission           | New animal arrives   | Vet, Zookeeper    | Animal, Enclosure, Zoo, Vet, Zookeeper | Composition, aggregation, association |
| Execute feeding round      | Schedule / time      | Zookeeper         | FeedingSchedule, Enclosure, Animal    | Aggregation, association  |
| Conduct health check       | Schedule / request   | Veterinarian      | Animal, Enclosure, Veterinarian | Polymorphism, abstraction  |
| Assign zookeeper to enclosure | New assignment need  | Zoo (system)      | Zoo, Zookeeper, Enclosure       | Association                |
| Conduct guided tour        | Schedule / request   | Guide             | Guide, Zoo, Enclosure           | Inheritance (Employee)     |

You can use these definitions as the basis for BPMN diagrams (one diagram per process or one collaboration with multiple pools) and for BDD scenarios (Given/When/Then per process).
