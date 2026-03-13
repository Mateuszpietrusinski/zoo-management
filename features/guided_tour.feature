# language: en
# Process 5: Conduct Guided Tour (Phase 7)
# Business process: guide leads visitors through enclosures in a defined route

Feature: Conduct Guided Tour
  As a guide
  I want to conduct a guided tour through the zoo's enclosures
  So that visitors see all animals

  Scenario: Guide successfully conducts tour through all enclosures
    Given a guide "emp-guide-1" is available in zoo "zoo-1"
    And zoo "zoo-1" has tour route ["enc-mammal-1", "enc-bird-1", "enc-reptile-1"]
    And all enclosures in the route exist
    When guide "emp-guide-1" conducts a tour of zoo "zoo-1"
    Then a tour record is created with the full route
    And the guide "emp-guide-1" is no longer available

  Scenario: Tour fails — guide not available
    Given a guide "emp-guide-busy" exists in zoo "zoo-1" but is not available
    When guide "emp-guide-busy" attempts to conduct a tour of zoo "zoo-1"
    Then the tour fails with NoGuideAvailableError

  Scenario: Tour fails — guide not in zoo (ADR-026)
    Given a guide "emp-guide-other" exists in zoo "zoo-other"
    When guide "emp-guide-other" attempts to conduct a tour of zoo "zoo-1"
    Then the tour fails with GuideNotInZooError

  Scenario: Tour fails — employee is not a guide
    Given a zookeeper "emp-zk-1" exists in zoo "zoo-1"
    When zookeeper "emp-zk-1" attempts to conduct a tour of zoo "zoo-1"
    Then the tour fails with InvalidEmployeeRoleError
