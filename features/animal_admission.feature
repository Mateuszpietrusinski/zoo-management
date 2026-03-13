# language: en
# Process 2: Animal Admission to Enclosure (Phase 4)
# architecture.md C4.4 Process 2; bdd-scenarios.md Process 1

Feature: Animal Admission to Enclosure
  As a zoo manager
  I want to admit a new animal to a suitable enclosure
  So that it is correctly housed and has an assigned caretaker

  Scenario: Admit internal animal without health check
    Given an internal lion "animal-lion-1" exists but is not placed
    And a mammal enclosure "enc-mammal-1" exists in zoo "zoo-1"
    When the zoo admits animal "animal-lion-1" to zoo "zoo-1"
    Then the animal is placed in enclosure "enc-mammal-1"
    And an admission record is created

  Scenario: Admit external animal with health check — cleared
    Given an external penguin "animal-penguin-ext" exists but is not placed
    And a bird enclosure "enc-bird-1" exists in zoo "zoo-1"
    And a veterinarian "emp-vet-1" exists in zoo "zoo-1"
    When the zoo admits animal "animal-penguin-ext" to zoo "zoo-1" with vet "emp-vet-1" result "healthy"
    Then the animal is placed in enclosure "enc-bird-1"
    And a health check record is created
    And an admission record is created with health_check_record_id

  Scenario: Admit external animal fails — not cleared
    Given an external lion "animal-lion-ext" exists but is not placed
    And a mammal enclosure "enc-mammal-1" exists in zoo "zoo-1"
    And a veterinarian "emp-vet-1" exists in zoo "zoo-1"
    When the zoo attempts to admit "animal-lion-ext" with vet "emp-vet-1" result "critical"
    Then the admission fails with HealthCheckNotClearedError
    And the animal remains unplaced

  Scenario: Admission fails — no suitable enclosure
    Given an internal crocodile "animal-croc-1" exists but is not placed
    And no reptile enclosure exists in zoo "zoo-1"
    When the zoo attempts to admit "animal-croc-1" to zoo "zoo-1"
    Then the admission fails with NoSuitableEnclosureError

  Scenario: Admission fails — animal already placed (ADR-013)
    Given a lion "animal-lion-placed" already placed in enclosure "enc-mammal-1"
    When the zoo attempts to admit "animal-lion-placed" to zoo "zoo-1"
    Then the admission fails with AnimalAlreadyPlacedError
