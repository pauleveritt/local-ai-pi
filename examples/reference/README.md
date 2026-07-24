# Reference Solutions

This directory contains spec-compliant reference solutions for each AgentClinic
phase. They deliberately contain **no** pytest workarounds — no
`tests/__init__.py`, no `sys.path` manipulation, no `conftest.py`. They exist
to validate the acceptance oracle: `tests/test_oracle.py` provisions each
reference solution through the real harness and requires the oracle to accept
it before any measurement batch is trusted.
