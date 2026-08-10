# Overnight run

Cohort: 8 tasks
## Stage 1 - authoring draft contracts (Qwen, read-only)
- registry-iter: draft already present, kept
- magicmock-factory: authored
- async-cm-enter: authored
- local-pings: authored
- flask-extensions: authored
- stringified-annotations: authored
- fastapi-get-registry: authored
- autowire: authored

8/8 drafts.
## qwen27b-draft-contract
exit 0
## gemma12b-draft-contract
exit 0
## gemma12b-brief-32k (maxTokens 8192 -> 32768)
exit 0

models.json restored. Elapsed 5.5h.

Morning: audit authoring transcripts for firewall reaches, run tools/audit_attempt.py on every new screen dir, then tools/report_screen.py, then score against PREDICTIONS.
