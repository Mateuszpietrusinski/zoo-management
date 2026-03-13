# language: en
# Process 2: Execute Feeding Round (phase-5)
# From phase-5-feature-feeding-round.md

Feature: Execute Feeding Round
  As a zookeeper
  I want to execute a feeding round for my assigned enclosure
  So that animals are fed on time

  Scenario: Successfully execute feeding round with animals
    Given enclosure "enc-mammal-1" in zoo "zoo-1" has lion "animal-lion-1"
    And zookeeper "emp-zk-1" is assigned to enclosure "enc-mammal-1"
    And a feeding schedule exists for "enc-mammal-1" at "09:00:00" with diet "meat"
    When zookeeper "emp-zk-1" executes feeding round for "enc-mammal-1" at "09:00:00"
    Then the feeding round succeeds with fed_count 1
    And the note contains "Fed 1 animals (diets: carnivore)"

  Scenario: Feeding round for empty enclosure
    Given enclosure "enc-bird-1" in zoo "zoo-1" has no animals
    And zookeeper "emp-zk-1" is assigned to enclosure "enc-bird-1"
    And a feeding schedule exists for "enc-bird-1" at "10:00:00" with diet "fish"
    When zookeeper "emp-zk-1" executes feeding round for "enc-bird-1" at "10:00:00"
    Then the feeding round succeeds with fed_count 0
    And the note is "no animals to feed"

  Scenario: Feeding fails — not due (time mismatch)
    Given a feeding schedule exists for "enc-mammal-1" at "09:00:00"
    When zookeeper "emp-zk-1" attempts feeding for "enc-mammal-1" at "10:00:00"
    Then the feeding fails with FeedingNotDueError

  Scenario: Feeding fails — zookeeper not assigned
    Given enclosure "enc-mammal-1" has zookeeper "emp-zk-other" assigned
    And a feeding schedule exists for "enc-mammal-1" at "09:00:00"
    When zookeeper "emp-zk-1" attempts feeding for "enc-mammal-1" at "09:00:00"
    Then the feeding fails with ZookeeperNotAssignedError
