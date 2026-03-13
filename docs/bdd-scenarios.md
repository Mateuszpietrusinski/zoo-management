# BDD Scenarios — Zoo Management System

Scenarios derived from the business processes in [business-processes-detailed.md](business-processes-detailed.md).  
Written in Gherkin (Given / When / Then) for use with pytest-bdd, behave, or similar.

**Business rules** (health check trigger, enclosure suitability, feeding due, initiator, records, etc.) are resolved and documented in [PRD.md](PRD.md) §5 and §8 and in the “Resolved business rules” section of [business-processes-detailed.md](business-processes-detailed.md).

---

## Process 1: Animal Admission to Enclosure

### Scenario: New animal admitted without health check (in-zoo birth)
```gherkin
Given the zoo has an enclosure "Savanna" suitable for mammals
And the zoo has a zookeeper "Alice" with no enclosure assigned
And a new mammal "Leo" is registered in the system but not in any enclosure
When the zoo admits "Leo" to enclosure "Savanna" without health check
And the zoo assigns zookeeper "Alice" to enclosure "Savanna"
Then "Leo" is in enclosure "Savanna"
And "Alice" is assigned to enclosure "Savanna"
And the admission is complete
```

### Scenario: New animal admitted with health check — cleared
```gherkin
Given the zoo has an enclosure "Predator House" suitable for lions
And the zoo has a veterinarian "Dr. Bob" and a zookeeper "Alice"
And a new lion "Simba" is registered but not in any enclosure
And health check is required for "Simba"
When the veterinarian "Dr. Bob" performs a health check on "Simba"
And the result is "Cleared"
And the zoo places "Simba" in enclosure "Predator House"
And the zoo assigns zookeeper "Alice" to enclosure "Predator House"
Then "Simba" is in enclosure "Predator House"
And "Alice" is assigned to enclosure "Predator House"
And the admission is complete
```

### Scenario: New animal not admitted — health check not cleared
```gherkin
Given the zoo has an enclosure "Predator House" suitable for lions
And a new lion "Scar" is registered but not in any enclosure
And health check is required for "Scar"
When the veterinarian performs a health check on "Scar"
And the result is "Not cleared"
Then "Scar" is not placed in any enclosure
And the admission is not complete
And "Scar" is marked for quarantine or follow-up
```

### Scenario: Admission fails — no suitable enclosure
```gherkin
Given the zoo has no enclosure suitable for crocodiles
And a new crocodile "Snappy" is registered but not in any enclosure
When the zoo attempts to admit "Snappy"
Then the admission fails
And "Snappy" remains not in any enclosure
And the system indicates no suitable enclosure available
```

### Scenario: Animal placed in enclosure that already has assigned zookeeper
```gherkin
Given the zoo has an enclosure "Aviary" suitable for birds with zookeeper "Charlie" already assigned
And a new eagle "Sky" is registered and health-check cleared
When the zoo places "Sky" in enclosure "Aviary"
Then "Sky" is in enclosure "Aviary"
And "Charlie" remains assigned to enclosure "Aviary"
And no new zookeeper assignment is required
```

---

## Process 2: Execute Feeding Round

### Scenario: Zookeeper successfully executes feeding for assigned enclosure
```gherkin
Given the zoo has an enclosure "Lion Enclosure" with animals "Leo" and "Luna"
And a feeding schedule exists for "Lion Enclosure" at "10:00" with diet "meat"
And zookeeper "Alice" is assigned to "Lion Enclosure"
When the zookeeper "Alice" executes the feeding round for "Lion Enclosure" at "10:00"
Then all animals in "Lion Enclosure" are fed
And the feeding for "Lion Enclosure" at "10:00" is recorded as completed
And the feeding schedule reflects the execution
```

### Scenario: Feeding round — enclosure has no animals
```gherkin
Given the zoo has an enclosure "Empty Enclosure" with no animals
And a feeding schedule exists for "Empty Enclosure" at "10:00"
And zookeeper "Alice" is assigned to "Empty Enclosure"
When the zookeeper "Alice" executes the feeding round for "Empty Enclosure" at "10:00"
Then no animals are fed
And the feeding is recorded as completed with note "no animals to feed"
```

### Scenario: Feeding round fails — zookeeper not assigned to enclosure
```gherkin
Given the zoo has an enclosure "Lion Enclosure" with animal "Leo"
And a feeding schedule exists for "Lion Enclosure" at "10:00"
And zookeeper "Alice" is not assigned to "Lion Enclosure"
When the zookeeper "Alice" attempts to execute the feeding round for "Lion Enclosure"
Then the feeding round is not performed
And the system indicates zookeeper is not assigned to this enclosure
```

### Scenario: Feeding not due — schedule indicates different time
```gherkin
Given a feeding schedule exists for "Lion Enclosure" at "10:00" only
And current time is "09:00"
When the system checks if feeding is due for "Lion Enclosure"
Then feeding is not due
And no feeding round is executed
```

---

## Process 3: Conduct Health Check

### Scenario: Veterinarian performs health check — animal healthy
```gherkin
Given the zoo has an elephant "Dumbo" in enclosure "Savanna"
And the zoo has a veterinarian "Dr. Bob"
When the veterinarian "Dr. Bob" conducts a health check on "Dumbo"
And the examination result is "Healthy"
Then the health check result for "Dumbo" is recorded as "Healthy"
And "Dumbo" has an updated last check date
And no follow-up is scheduled
```

### Scenario: Veterinarian performs health check — follow-up needed
```gherkin
Given the zoo has a penguin "Pingu" in enclosure "Ice World"
And the zoo has a veterinarian "Dr. Bob"
When the veterinarian "Dr. Bob" conducts a health check on "Pingu"
And the examination result is "Need follow-up"
Then the health check result for "Pingu" is recorded as "Need follow-up"
And a follow-up or treatment is scheduled for "Pingu"
```

### Scenario: Veterinarian performs health check — critical
```gherkin
Given the zoo has a lion "Leo" in enclosure "Predator House"
And the zoo has a veterinarian "Dr. Bob"
When the veterinarian "Dr. Bob" conducts a health check on "Leo"
And the examination result is "Critical"
Then the health check result for "Leo" is recorded as "Critical"
And the case is escalated or urgent treatment is scheduled
```

### Scenario: Health check uses animal-specific examination (polymorphism)
```gherkin
Given the zoo has a reptile "Croc" (crocodile) in enclosure "Reptile House"
And the zoo has a veterinarian "Dr. Bob"
When the veterinarian "Dr. Bob" conducts a health check on "Croc"
Then the examination follows reptile-specific checks
And the result is recorded for "Croc"
```

---

## Process 4: Assign Zookeeper to Enclosure

### Scenario: Zoo assigns zookeeper to empty enclosure
```gherkin
Given the zoo has an enclosure "Savanna" with no zookeeper assigned
And the zoo has a zookeeper "Alice" with no enclosure assigned
When the zoo assigns zookeeper "Alice" to enclosure "Savanna"
Then "Alice" is associated with enclosure "Savanna"
And enclosure "Savanna" has "Alice" as its assigned zookeeper
```

### Scenario: Zoo reassigns enclosure to different zookeeper
```gherkin
Given the zoo has an enclosure "Aviary" with zookeeper "Charlie" assigned
And the zoo has a zookeeper "Dana" with no enclosure assigned
When the zoo assigns zookeeper "Dana" to enclosure "Aviary"
Then "Dana" is associated with enclosure "Aviary"
And "Charlie" is no longer assigned to enclosure "Aviary"
```

### Scenario: Assign zookeeper fails — enclosure not in zoo
```gherkin
Given the zoo has a zookeeper "Alice"
And an enclosure "Orphan Enclosure" that does not belong to the zoo
When the zoo attempts to assign "Alice" to "Orphan Enclosure"
Then the assignment fails
And the system indicates enclosure is not part of the zoo
```

### Scenario: Assign zookeeper fails — zookeeper not employed by zoo
```gherkin
Given the zoo has an enclosure "Savanna"
And "Alice" is not an employee of the zoo
When the zoo attempts to assign "Alice" to enclosure "Savanna"
Then the assignment fails
And the system indicates zookeeper is not employed by the zoo
```

---

## Process 5: Conduct Guided Tour

### Scenario: Guide conducts tour through all enclosures in route
```gherkin
Given the zoo has a guide "Eve"
And the zoo has a tour route with enclosures "Savanna", "Aviary", "Reptile House" in that order
When the guide "Eve" starts the tour
And the guide visits each enclosure in the route in order
Then the guide has visited "Savanna" then "Aviary" then "Reptile House"
And the tour is recorded as completed
```

### Scenario: Tour cannot start — no guide available
```gherkin
Given the zoo has a tour route with enclosures "Savanna" and "Aviary"
And no guide is available at the scheduled tour time
When the system attempts to start the scheduled tour
Then the tour does not start
And the system indicates no guide available (reschedule or cancel)
```

### Scenario: Tour with single enclosure
```gherkin
Given the zoo has a guide "Eve"
And the zoo has a tour route with only enclosure "Savanna"
When the guide "Eve" starts the tour
And the guide visits the only enclosure "Savanna"
Then the tour is completed after one visit
And the tour is recorded as completed
```

---

## Summary: Scenarios per Process

| Process | Happy path | Alternatives / Exceptions | Total |
|---------|------------|---------------------------|-------|
| 1. Animal admission | 2 | 3 | 5 |
| 2. Execute feeding round | 1 | 3 | 4 |
| 3. Conduct health check | 1 | 3 | 4 |
| 4. Assign zookeeper | 1 | 3 | 4 |
| 5. Conduct guided tour | 2 | 1 | 3 |
| **Total** | **7** | **13** | **20** |

The corresponding Gherkin feature files are in `features/` and can be run with pytest-bdd or behave.
