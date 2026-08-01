# Spec: differential-validation

## ADDED Requirements

### Requirement: Differential harness compares py3 port against the frozen reference
The repository SHALL provide a harness (under `test/differential/`) that runs the frozen Docker fuzzingserver and the py3 fuzzingserver with identical test specifications, drives the same testee client against both, and produces a machine-readable diff of the resulting reports.

#### Scenario: Harness produces a comparable report pair
- **WHEN** the differential harness is run with a given spec and testee client
- **THEN** it outputs two normalized JSON report sets (reference and py3) and a diff summary listing any case whose outcome differs

### Requirement: Report normalization removes only environment noise
Report comparison SHALL normalize away run-specific fields (timestamps, durations, version strings, agent ordering) and nothing else; case identifiers, outcomes (pass/fail/non-strict/informational), close codes, and reported wire behavior SHALL be compared verbatim.

#### Scenario: Same behavior yields empty diff
- **WHEN** the same fuzzingserver implementation is run twice and reports are normalized
- **THEN** the diff between the two runs is empty

### Requirement: Behavioral equivalence gates acceptance
The py3 port SHALL NOT be declared complete until a differential run over the full case set (including 9.*, 12.*, 13.*) shows every case with an identical outcome and close code to the frozen reference, or every difference is explicitly triaged and documented as an accepted environment artifact in the harness's triage file.

#### Scenario: Untriaged difference blocks acceptance
- **WHEN** the differential run reports a case outcome differing from the reference and no triage entry covers it
- **THEN** the harness exits non-zero

#### Scenario: Triaged differences are visible
- **WHEN** all differences are covered by triage entries
- **THEN** the harness exits zero and prints the list of accepted, documented differences

### Requirement: Wire-level spot checks for byte-sensitive sections
For a defined sample of byte-sensitive cases (masking, fragmentation, and section 6 UTF-8 cases), the harness SHALL capture the actual frames sent by both implementations and compare them byte-for-byte, independent of report outcomes.

#### Scenario: Payload corruption caught despite matching outcomes
- **WHEN** both implementations mark a sampled case "pass" but the py3 server sent different payload bytes than the reference
- **THEN** the wire-level check reports the byte difference and the harness exits non-zero
