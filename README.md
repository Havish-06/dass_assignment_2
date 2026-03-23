# DASS Assignment 2 Submission
**Git Repository Link:** [https://github.com/Havish-06/dass_assignment_2.git](https://github.com/Havish-06/dass_assignment_2.git)

This repository contains the complete implementation, testing suites, and analytical reports for the Black-Box, White-Box, and Integration testing environments.

---

## 🚀 How to Run the Code and Tests

### Prerequisites
Ensure you have Python 3 installed. The black-box testing suite utilizes `pytest` and `requests`, while the white-box and integration suites utilize Python's built-in `unittest` framework.
```bash
pip install pytest requests
```

### 1. Black-Box Testing
The black-box assignment comprehensively validates a REST API framework focusing on functional boundaries and equivalence partitioning.
**Running the Test Suite:**
```bash
cd blackbox
python3 -m pytest tests/ -v
```

### 2. White-Box Testing (MoneyPoly Engine)
The white-box assignment mathematically structures and asserts internal pathing logic (branch and statement coverage) for an interactive Monopoly game wrapper.
**Running the Game Engine:**
```bash
cd whitebox
python3 -m moneypoly.main
```
**Running the White-Box Unittests:**
```bash
cd whitebox
python3 -m unittest discover -s tests -v
```

### 3. Integration Testing (StreetRace Manager)
The integration assignment handles sophisticated cross-module functional integration, tying together domain logic, database operations, and maintenance dependencies.
**Running the Interactive CLI Application:**
```bash
cd integration/code
python3 -m streetrace.cli
```
**Running the Integration Test Suite:**
```bash
cd integration
python3 -m unittest discover -s tests -v
```

---
*Note: All architectural diagrams (CFGs, Call Graphs) and formal analysis reports are available inside each respective module folder (`diagrams/` and `report.pdf`) satisfying the precise academic directory tree submission rules.*