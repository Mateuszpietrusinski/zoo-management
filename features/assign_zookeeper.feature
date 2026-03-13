# language: en
# Process 4: Assign Zookeeper to Enclosure (phase-3)
# From bdd-scenarios.md Process 4

Feature: Assign Zookeeper to Enclosure
  As a zoo manager
  I want to assign a zookeeper to an enclosure
  So that feeding and daily care are clearly owned

  Scenario: Successfully assign zookeeper to enclosure
    Given an enclosure "enc-mammal-1" exists in zoo "zoo-1"
    And a zookeeper "emp-zk-1" exists in zoo "zoo-1"
    When the zoo assigns zookeeper "emp-zk-1" to enclosure "enc-mammal-1" in zoo "zoo-1"
    Then enclosure "enc-mammal-1" has zookeeper "emp-zk-1" assigned

  Scenario: Reassign enclosure to different zookeeper (idempotent, ADR-031)
    Given an enclosure "enc-mammal-1" exists in zoo "zoo-1" with zookeeper "emp-zk-1" assigned
    And a zookeeper "emp-zk-2" exists in zoo "zoo-1"
    When the zoo assigns zookeeper "emp-zk-2" to enclosure "enc-mammal-1" in zoo "zoo-1"
    Then enclosure "enc-mammal-1" has zookeeper "emp-zk-2" assigned

  Scenario: Assignment fails — enclosure not in zoo
    Given an enclosure "enc-mammal-1" exists in zoo "zoo-1"
    And a zookeeper "emp-zk-1" exists in zoo "zoo-1"
    When the zoo attempts to assign zookeeper "emp-zk-1" to enclosure "enc-mammal-1" in zoo "zoo-other"
    Then the assignment fails with EnclosureNotInZooError

  Scenario: Assignment fails — employee is not a zookeeper
    Given an enclosure "enc-mammal-1" exists in zoo "zoo-1"
    And a guide "emp-guide-1" exists in zoo "zoo-1"
    When the zoo attempts to assign employee "emp-guide-1" as zookeeper to enclosure "enc-mammal-1" in zoo "zoo-1"
    Then the assignment fails with InvalidEmployeeRoleError
