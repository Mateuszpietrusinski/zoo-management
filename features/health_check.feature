# language: en
# Process 4: Conduct Health Check (Phase 6)
# Business process: veterinarian examines an animal and the result is recorded

Feature: Conduct Health Check
  As a veterinarian
  I want to conduct a health check on an animal and record the result
  So that the zoo can track health and schedule follow-up

  Scenario: Health check result is Healthy
    Given an animal "animal-lion-1" exists in the system
    And a veterinarian "emp-vet-1" exists in the system
    When veterinarian "emp-vet-1" conducts a health check on "animal-lion-1" with result "healthy"
    Then a health check record is created with result "healthy"

  Scenario: Health check result is Need Follow-Up
    Given an animal "animal-penguin-1" exists in the system
    And a veterinarian "emp-vet-1" exists in the system
    When veterinarian "emp-vet-1" conducts a health check on "animal-penguin-1" with result "need_follow_up"
    Then a health check record is created with result "need_follow_up"

  Scenario: Health check result is Critical
    Given an animal "animal-lion-1" exists in the system
    And a veterinarian "emp-vet-1" exists in the system
    When veterinarian "emp-vet-1" conducts a health check on "animal-lion-1" with result "critical"
    Then a health check record is created with result "critical"

  Scenario: Health check fails — employee is not a veterinarian
    Given an animal "animal-lion-1" exists in the system
    And a zookeeper "emp-zk-1" exists in the system
    When zookeeper "emp-zk-1" attempts to conduct a health check on "animal-lion-1"
    Then the health check fails with InvalidEmployeeRoleError
