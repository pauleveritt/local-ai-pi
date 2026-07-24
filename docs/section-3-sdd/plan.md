# SP2 — Part III (SDD on Pi) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Install Pi's shipped subagent extension, author an implementer specialist and orchestrator system prompt, and measure whether parent+implementer delegation beats the SP1 0/8 baseline.

**Architecture:** The shipped `subagent` extension provides the registered-tool mechanism and specialist discovery. The course authors two data files: `.pi/agents/implementer.md` (specialist with frontmatter + system prompt) and `prompts/orchestrator.md` (parent system prompt teaching packet-making). The SP1 harness gains a parameterized invocation profile so it can run SP2's parent sessions (different extensions, append-system-prompt, higher timeout). No TypeScript is written.

**Tech Stack:** Pi shipped subagent extension (`@earendil-works/pi-coding-agent/examples/extensions/subagent/`), Python 3.14+ (harness delta), pytest, `omlx/gemma-4-12B-it-MLX-8bit`.

## Global Constraints

- **Built-in Pi only.** The subagent mechanism is Pi's shipped example extension. No fork, no patch.
- **Model:** `omlx/gemma-4-12B-it-MLX-8bit` on oMLX (`http://127.0.0.1:8001/v1`).
- **Headless:** `stdin=subprocess.DEVNULL`; `--mode json -p --no-session`.
- **`agentScope: "both"` on every delegation.** Default `"user"` scope never reads `.pi/agents/`.
- **Success is harness-determined** (pytest + diff), never the child's self-report.
- **`--append-system-prompt`, not `--system-prompt`.** The child needs the base coding prompt.
- **Evidence-gated.** Every chapter measurement produces a dated research report.
- **No TypeScript written.** The shipped extension is installed, not modified.
- **Orchestrator prompt maps to `prompts/orchestrator.md`, not `.pi/agents/`.** Prevents self-delegation.
- **`implementer.md` agents is coped to `~/.pi/agent/agents` unless we can figure out why the `agentScope` `both` block is not working**

---

## File Structure

```
local-ai-pi/
  .pi/
    agents/
      implementer.md                       # CREATE: specialist
  prompts/
    orchestrator.md                        # CREATE: parent system prompt
  harness/
    __init__.py
    telemetry.py                           # MODIFY: no-delegation check
    session.py                             # MODIFY: invocation profile
    runner.py                              # MODIFY: pass profile, timeout
  tests/
    conftest.py                            # MODIFY: SP2 fixtures
    test_sp2_specialists.py                # CREATE: frontmatter tests
  docs/
    chapters/
      part3a-subagent-mechanism.md         # CREATE
      part3b-implementer-orchestrator.md   # CREATE
      part3c-lessons-from-handoff.md       # CREATE
      index.md                             # MODIFY: Part III entries
    superpowers/
      research/
        YYYY-MM-DD-sp2-baseline-phase-N.md # CREATE (Task 6)
```

---

### Task 0: R0 — Locate and verify the shipped subagent extension

**Files:**
- None created or modified (discovery task)

**Purpose:** Locate the shipped subagent extension in the installed Pi package, verify it loads and works with a trivial delegation, and record the install path. This is discovery, not implementation — its deliverable is a known-good path and a verified invocation.

- [ ] **Step 1: Find the installed Pi package root**

```bash
PI_PACKAGE=$(dirname $(dirname $(which pi)))/lib/node_modules/@earendil-works/pi-coding-agent
echo $PI_PACKAGE
ls $PI_PACKAGE/examples/extensions/subagent/index.ts
```
Expected: file exists.

- [ ] **Step 2: Verify the extension loads and registers the tool**

```bash
pi --no-session -p --extension "$PI_PACKAGE/examples/extensions/subagent/index.ts" \
   --model omlx/gemma-4-12B-it-MLX-8bit \
   --no-skills --no-prompt-templates --no-themes --no-context-files \
   "What tools are available?" < /dev/null 2>&1 | head -20
```
Expected: the parent can see a `subagent` tool. (May fail quickly if the model doesn't actually list tools, but the extension loading itself should not error.)

- [ ] **Step 3: Verify agentScope default behavior — empty agents list**

```bash
pi --no-session -p --extension "$PI_PACKAGE/examples/extensions/subagent/index.ts" \
   --model omlx/gemma-4-12B-it-MLX-8bit \
   --no-skills --no-prompt-templates --no-themes --no-context-files \
   "Call the subagent tool with agent: scout, task: list files in current directory" \
   < /dev/null 2>&1 | head -20
```
Expected: `Unknown agent: "scout"` or `Available agents: none` — no `.pi/agents/` files exist yet.

- [ ] **Step 4: Record the install path**

```bash
# Save the path for the harness and chapters to reference
echo "$PI_PACKAGE/examples/extensions/subagent/index.ts" > .pi/subagent-extension-path.txt
```

- [ ] **Step 5: Commit**

```bash
git add .pi/subagent-extension-path.txt
git commit -m "R0: locate shipped subagent extension, record install path"
```

---

### Task 1: Harness invocation profiles

**Files:**
- Modify: `harness/session.py` — parameterized invocation
- Modify: `harness/telemetry.py` — no-delegation check
- Modify: `harness/runner.py` — pass profile, timeout
- Modify: `tests/conftest.py` — SP2 fixtures
- Modify: `tests/test_session.py` — new signature tests

**Interfaces:**
- Consumes: `_find_pi`, `read_run`, `capture_diff` (existing)
- Produces: `InvocationProfile` dataclass, `run_session` gains `profile` parameter, `run_baseline` gains `profile` parameter
- Consumed by: Tasks 2-6

**Purpose:** Replace `session.py`'s hardcoded `--no-extensions --extension .pi/extensions/hello-world.ts` with a parameterized `InvocationProfile` that can describe SP1 or SP2 sessions. Also add `no-delegation` outcome detection and raise the timeout ceiling.

- [ ] **Step 1: Define the InvocationProfile dataclass**

```python
# In harness/session.py, add before SessionResult:

@dataclass
class InvocationProfile:
    """Describes how to invoke pi for a session."""
    extensions: list[str]     # --extension paths (empty = none beyond built-in)
    append_system_prompt: str | None = None  # --append-system-prompt path
    no_extensions: bool = True  # --no-extensions (strip global config)

    @staticmethod
    def sp1() -> "InvocationProfile":
        """The SP1 profile: hello-world extension only."""
        return InvocationProfile(
            extensions=[".pi/extensions/hello-world.ts"],
        )

    @staticmethod
    def sp2(subagent_path: str) -> "InvocationProfile":
        """The SP2 profile: subagent extension + orchestrator prompt."""
        return InvocationProfile(
            extensions=[subagent_path],
            append_system_prompt="prompts/orchestrator.md",
        )
```

- [ ] **Step 2: Update run_session signature and pi_cmd construction**

Change `run_session` to accept `profile: InvocationProfile` instead of the hardcoded extension logic. The `pi_cmd` list is built from the profile:

```python
def run_session(
    workspace: str | Path,
    phase_prompt: str,
    model: str,
    pristine_hash: str,
    profile: InvocationProfile,
    timeout: int = 300,
    max_startup_attempts: int = 3,
) -> SessionResult:
    ...
    pi_cmd = [pi_exe, "--mode", "json", "-p", "--no-session", "--model", model]

    if profile.no_extensions:
        pi_cmd.append("--no-extensions")
    for ext in profile.extensions:
        pi_cmd.extend(["--extension", ext])
    if profile.append_system_prompt:
        pi_cmd.extend(["--append-system-prompt", profile.append_system_prompt])

    pi_cmd.extend(["--no-skills", "--no-prompt-templates", "--no-themes", "--no-context-files", "--approve"])
    pi_cmd.append(f"@{prompt_file}")
```

- [ ] **Step 3: Add no-delegation detection to telemetry.py**

Add a function to check whether the parent session includes any subagent tool calls:

```python
# In harness/telemetry.py:

def has_subagent_calls(stream_path: str | Path) -> bool:
    """True if the session includes at least one subagent tool call."""
    path = Path(stream_path)
    if not path.exists():
        return False
    for line in path.read_text().splitlines():
        try:
            event = json.loads(line.strip())
            if event.get("type") == "tool_execution_end" and event.get("toolName") == "subagent":
                return True
        except json.JSONDecodeError:
            continue
    return False
```

- [ ] **Step 4: Update run_session to detect no-delegation**

In `run_session`, after `outcome` is determined, check for delegation:

```python
# After outcome/returncode determination, before SessionResult:
if outcome == "exited" and not has_subagent_calls(artifact_path):
    outcome = "no-delegation"
```

- [ ] **Step 5: Update run_baseline to accept and pass a profile**

```python
def run_baseline(
    phase_prompt: str,
    app_source: str | Path,
    model: str,
    profile: InvocationProfile,
    n: int = 8,
    timeout: int = 300,
    phase_name: str | None = None,
) -> BaselineReport:
    ...
    result = run_session(
        ws_path, phase_prompt, model,
        pristine_hash=pristine_hash,
        profile=profile,
        timeout=timeout,
    )
```

- [ ] **Step 6: Add SP2 conftest fixtures**

```python
# In tests/conftest.py, add:

from harness.session import InvocationProfile

@pytest.fixture
def sp1_profile() -> InvocationProfile:
    return InvocationProfile.sp1()

@pytest.fixture
def sp2_profile() -> InvocationProfile:
    subagent_path = Path(__file__).resolve().parent.parent / ".pi" / "subagent-extension-path.txt"
    path = subagent_path.read_text().strip() if subagent_path.exists() else ""
    return InvocationProfile.sp2(path)
```

- [ ] **Step 7: Update existing session/runner tests for new signatures**

Update `test_run_session_signature_exists` to check for `profile` parameter. Update `test_run_baseline_signature` to check for `profile` parameter.

- [ ] **Step 8: Run tests**

```bash
uv run pytest tests/ -v
```
Expected: all existing tests pass with updated signatures.

- [ ] **Step 9: Commit**

```bash
git add harness/session.py harness/telemetry.py harness/runner.py tests/conftest.py tests/test_session.py tests/test_runner.py
git commit -m "feat: invocation profiles — parameterized extensions and system prompt for SP2"
```

---

### Task 2: Implementer specialist

**Files:**
- Create: `.pi/agents/implementer.md`
- Create: `tests/test_sp2_specialists.py` (frontmatter validation)

**Purpose:** Write the implementer specialist. The specialist is a markdown file with YAML frontmatter consumed by the shipped subagent extension's `agents.ts` discovery.

- [ ] **Step 1: Write the failing frontmatter test**

```python
# tests/test_sp2_specialists.py
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parent.parent


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML-like frontmatter from a markdown file.
    The shipped 'agents.ts' parseFrontmatter handles this server-side;
    we validate the frontmatter shape here."""
    if not text.startswith("---"):
        raise ValueError("Missing frontmatter delimiter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Missing closing frontmatter delimiter")
    frontmatter = {}
    for line in parts[1].strip().split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            frontmatter[key.strip()] = value.strip()
    return frontmatter, parts[2].strip()


def test_implementer_md_exists():
    path = REPO_ROOT / ".pi" / "agents" / "implementer.md"
    assert path.exists(), f"{path} not found"


def test_implementer_md_has_valid_frontmatter():
    path = REPO_ROOT / ".pi" / "agents" / "implementer.md"
    text = path.read_text()
    fm, body = _parse_frontmatter(text)
    assert fm.get("name") == "implementer", "frontmatter must have name: implementer"
    assert "description" in fm, "frontmatter must have description"
    assert "tools" in fm, "frontmatter must have tools"
    tools = [t.strip() for t in fm["tools"].split(",")]
    assert "read" in tools
    assert "write" in tools
    assert "bash" in tools
    assert fm.get("model") == "omlx/gemma-4-12B-it-MLX-8bit"


def test_implementer_md_has_system_prompt_body():
    path = REPO_ROOT / ".pi" / "agents" / "implementer.md"
    text = path.read_text()
    fm, body = _parse_frontmatter(text)
    assert len(body) > 100, "system prompt body should be substantial"
    assert "implementer" in body.lower()
    assert "packet" in body.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_sp2_specialists.py -v
```
Expected: FAIL with file not found.

- [ ] **Step 3: Write .pi/agents/implementer.md**

```markdown
---
name: implementer
description: Builds exactly what the packet specifies. No exploration, no redesign.
tools: read, write, bash
model: omlx/gemma-4-12B-it-MLX-8bit
---

You are an implementer. Your job is to build exactly what the packet specifies — nothing more, nothing less.

## Rules

1. **Follow the packet.** The packet tells you what to build, which files you may touch, and what acceptance strings must appear. Do not deviate.
2. **Do not explore.** Do not read files not listed in "Allowed Files." Do not search the codebase, do not examine imports, do not check for existing patterns. The packet is your complete specification.
3. **Do not redesign.** If the packet says "Create app.py with FastAPI," do that. Do not suggest alternatives, improve the architecture, or add "nice to haves."
4. **Acceptance strings must appear verbatim.** If the packet lists an acceptance string like "Scope creep never ends.", that exact text must appear somewhere in your output (usually in a template or the test assertions).
5. **Run validation before reporting.** After writing all files, run the validation command (usually `uv run pytest -q`). If tests fail, fix your code and re-run. If tests pass, report completion.
6. **Report honestly.** After validation, report what you built and whether tests passed. Do not claim success if tests failed.

## Packet Format

You will receive a packet with this structure:

```
## Task
<what to build>

## Allowed Files
- file1.py
- file2.html

## Acceptance Strings
- "exact string that must appear"

## Validation
uv run pytest -q
```

Build the task using only the allowed files. Ensure acceptance strings appear. Run validation. Report result.
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_sp2_specialists.py -v
```
Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add .pi/agents/implementer.md tests/test_sp2_specialists.py
git commit -m "feat: implementer specialist with frontmatter and focused system prompt"
```

---

### Task 3: Orchestrator prompt

**Files:**
- Create: `prompts/orchestrator.md`
- Modify: `tests/test_sp2_specialists.py` (add orchestrator content test)

**Purpose:** Write the parent system prompt that teaches the SLM to extract phases, construct packets, and dispatch via the subagent tool. Lives in `prompts/` (not `.pi/agents/`) to prevent self-delegation.

- [ ] **Step 1: Add orchestrator test to test_sp2_specialists.py**

```python
def test_orchestrator_md_exists():
    path = REPO_ROOT / "prompts" / "orchestrator.md"
    assert path.exists(), f"{path} not found"


def test_orchestrator_md_contains_packet_format():
    path = REPO_ROOT / "prompts" / "orchestrator.md"
    text = path.read_text()
    assert "agentScope" in text, "must mention agentScope: both"
    assert "packet" in text.lower()
    assert "subagent" in text.lower()
    assert "implementer" in text.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_sp2_specialists.py::test_orchestrator_md_exists -v
```
Expected: FAIL.

- [ ] **Step 3: Write prompts/orchestrator.md**

```markdown
You are an orchestrator. Your job is to take a phase from the AgentClinic roadmap
and dispatch it to the implementer specialist via the subagent tool.

## How to work

1. **Read the roadmap.** The `@examples/agentclinic/specs/roadmap.md` file
   contains three phases. Each phase is a checklist of deliverables.

2. **Extract one phase at a time.** When the user says "Build Phase N," find
   that phase in the roadmap. Extract its checklist items verbatim.

3. **Construct a packet.** Build a packet for the implementer using this exact
   format:

   ```
   ## Task
   <extracted phase checklist, copied verbatim>

   ## Allowed Files
   - app.py
   - models.py (Phase 2+)
   - templates/base.html
   - templates/home.html
   - templates/complaints.html (Phase 2+)
   - tests/test_app.py

   ## Acceptance Strings
   - "<verbatim string from phase spec that must appear in output>"

   ## Validation
   uv run pytest -q
   ```

   The task section must be the phase extracted VERBATIM from the roadmap — do
   not paraphrase, rewrite, or summarize. The allowed-files list must match the
   phase (Phase 1 only touches home page files; Phase 2 adds complaints;
   Phase 3 adds the form). Acceptance strings must be the exact user-visible
   strings from the phase spec.

4. **Dispatch via the subagent tool.** Call:
   ```
   subagent({ agent: "implementer", task: "<packet>", agentScope: "both" })
   ```
   The `agentScope: "both"` parameter is REQUIRED — without it, the tool cannot
   find the implementer specialist in `.pi/agents/`.

5. **Verify the result.** After the implementer reports back, check:
   - Did tests pass?
   - Did files change?
   - If not, construct a repair packet (narrower, with the specific failure) and
     dispatch once more. Do not repair more than twice.

6. **Proceed to next phase.** Only after the current phase passes, move to the
   next one.
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_sp2_specialists.py -v
```
Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add prompts/orchestrator.md tests/test_sp2_specialists.py
git commit -m "feat: orchestrator system prompt with packet format and agentScope instruction"
```

---

### Task 4: End-to-end verification — single delegation

**Files:**
- None created (verification run)

**Purpose:** Before writing chapters, verify a single parent+implementer delegation runs end-to-end. This catches the "first contact" failures the spec review warned about. Leave the workspace in place for inspection.

- [ ] **Step 1: Run a single delegation manually**

```bash
PI_PACKAGE=$(dirname $(dirname $(which pi)))/lib/node_modules/@earendil-works/pi-coding-agent
SUBAGENT="$PI_PACKAGE/examples/extensions/subagent/index.ts"

uv run python -c "
from harness.workspace import prepare_workspace
from harness.session import run_session, InvocationProfile
from pathlib import Path
import os

os.environ['PI_EVAL_KEEP_WORKSPACES'] = '1'

# Extract Phase 1 prompt
roadmap = (Path('examples/agentclinic/specs/roadmap.md')).read_text()
lines = roadmap.splitlines()
start = next(i for i,l in enumerate(lines) if l.startswith('## Phase 1 '))
body = [l for l in lines[start+1:] if not l.startswith('## Phase ')]
prompt = '\n'.join(body).strip()

ws, pristine = prepare_workspace('examples/agentclinic')
try:
    profile = InvocationProfile.sp2('$SUBAGENT')
    result = run_session(ws, prompt, 'omlx/gemma-4-12B-it-MLX-8bit', pristine, profile, timeout=900)
    print(f'Outcome: {result.outcome}')
    print(f'Turns: {result.telemetry.turns}')
    print(f'Tests pass: {result.tests_pass}')
    print(f'Changed files: {result.changed_files}')
    print(f'Wall time: {result.wall_time_s:.0f}s')
finally:
    # Keep workspace for inspection
    print(f'Workspace: {ws}')
"
```

Expected: outcome is `exited` or `no-delegation` or `timeout` (not a crash). If outcome is `no-delegation`, the parent never called the subagent tool — check the parent JSONL to understand why.

- [ ] **Step 2: Inspect the parent JSONL**

```bash
# Find the most recent session artifact
ls -t docs/superpowers/research/sessions/*.jsonl | head -1 | xargs python3 -c "
import json, sys
path = sys.argv[1]
has_subagent = False
for line in open(path):
    ev = json.loads(line.strip())
    if ev.get('toolName') == 'subagent':
        has_subagent = True
        print(f'subagent call: {ev.get(\"type\")} args={str(ev.get(\"args\",\"\"))[:200]}')
    if ev.get('type') == 'tool_execution_end' and ev.get('isError') == 'True':
        print(f'ERROR: {ev.get(\"toolName\")} - {str(ev.get(\"result\",\"\"))[:300]}')
if not has_subagent:
    print('NO SUBAGENT CALLS FOUND')
" $(ls -t docs/superpowers/research/sessions/*.jsonl | head -1)
```

- [ ] **Step 3: If subagent was called, check the child result**

The `tool_execution_end` for `subagent` in the parent JSONL carries the child's result in its `result` field. Inspect to confirm the implementer received the packet and attempted work.

- [ ] **Step 4: Do not commit at this step** — this is verification, not deliverable code. If fixes are needed, apply them and re-verify.

---

### Task 5: Chapter 1 — "The Subagent Mechanism"

**Files:**
- Create: `docs/chapters/part3a-subagent-mechanism.md`

**Purpose:** Teach the reader to locate and install the shipped subagent extension, run a trivial delegation, and understand the registered-tool pattern and specialist discovery.

- [ ] **Step 1: Write the chapter**

The chapter follows the MyST/Sphinx format of previous chapters. Content structure:

```markdown
(part3a-subagent-mechanism)=

# The Subagent Mechanism

## What Pi ships

[Explain: Pi has no runtime subagent primitive, but its examples directory
ships a complete subagent extension. Walk through locating it from the pi
binary's install path. Show the file tree: index.ts (900 lines), agents.ts
(discovery), agents/ (sample specialists), prompts/ (workflow templates).]

## Installing the extension

[Two-step recipe:
1. Locate: resolve from `which pi` → package root → examples/extensions/subagent/
2. Load: `pi --extension <path>` per session
Explain that `pi install` installs the extension but NOT the agents/*.md files.
Specialists are data the reader authors, not code that comes with the extension.]

## The first delegation

[Run a trivial delegation: "Call the subagent tool to read README.md and
summarize it." Show the tool call in action, the child process, the result.
Demonstrate the empty-discovery failure first: without an agents/ file, the
tool reports "Available agents: none." Then show the fix: copy a sample agent.]

## How it works

[Dissect index.ts: registerTool, spawn pi --mode json -p --no-session,
stream JSONL, collect results. Dissect agents.ts: discoverAgents, frontmatter
parsing, scope (user/project/both). Explain why agentScope: "both" is needed
for project-local agents.]

## What you built

[A working subagent delegation. In the next chapter you'll author your own
specialists and orchestrate a real build.]
```

Fill in with actual output from Task 0 and Task 4, replacing placeholders.

- [ ] **Step 2: Commit**

```bash
git add docs/chapters/part3a-subagent-mechanism.md
git commit -m "docs: Part III chapter 1 — the subagent mechanism"
```

---

### Task 6: Chapter 2 — "The Implementer + Orchestrator" + baseline

**Files:**
- Create: `docs/chapters/part3b-implementer-orchestrator.md`
- Create: `docs/superpowers/research/YYYY-MM-DD-sp2-baseline-phase-1.md` (after measurement)

**Purpose:** Teach the reader to author the implementer specialist and orchestrator prompt, then run the n=8 baseline. This chapter includes the live measurement producing the dated evidence report.

- [ ] **Step 1: Write the chapter**

```markdown
(part3b-implementer-orchestrator)=

# The Implementer + Orchestrator

## Authoring the implementer

[Walk through .pi/agents/implementer.md: frontmatter fields, system prompt
design, the packet format it expects. Explain each rule and why it maps to
LESSONS #1/#4.]

## Authoring the orchestrator

[Walk through prompts/orchestrator.md: how to extract phases, construct
packets, dispatch with agentScope: "both", verify results. Explain why it
lives in prompts/ not .pi/agents/.]

## Running the parent session

[Show the parent invocation: --extension <subagent> --append-system-prompt
prompts/orchestrator.md. The user prompt is "Build Phase 1 using the
implementer specialist." Walk through what happens end-to-end.]

## The baseline measurement

[Run n=8. Present the report table. Compare to SP1's 0/8. Discuss:
is the implementer doing better, worse, or the same? What failure patterns
are visible? This sets up Chapter 3's tuning.]
```

- [ ] **Step 2: Run the n=8 baseline using the harness**

```bash
PI_PACKAGE=$(dirname $(dirname $(which pi)))/lib/node_modules/@earendil-works/pi-coding-agent
SUBAGENT="$PI_PACKAGE/examples/extensions/subagent/index.ts"

uv run python -c "
from harness.runner import run_baseline, write_report
from harness.session import InvocationProfile
from pathlib import Path
from datetime import date

app_source = Path('examples/agentclinic')
roadmap = (app_source / 'specs' / 'roadmap.md').read_text()

profile = InvocationProfile.sp2('$SUBAGENT')

for phase_num in (1, 2, 3):
    lines = roadmap.splitlines()
    marker = f'## Phase {phase_num} '
    start = next((i for i,l in enumerate(lines) if l.startswith(marker)), None)
    if start is None: continue
    body = [l for l in lines[start+1:] if not l.startswith('## Phase ')]
    prompt = '\n'.join(body).strip()
    phase_name = lines[start][3:].strip()
    print(f'Running baseline: {phase_name}...')
    report = run_baseline(prompt, app_source, 'omlx/gemma-4-12B-it-MLX-8bit',
                          profile=profile, n=8, timeout=900, phase_name=phase_name)
    write_report(report, f'docs/superpowers/research/{date.today().isoformat()}-sp2-baseline-phase-{phase_num}.md')
    print(f'  Success: {report.success_count}/{report.n} ({report.success_rate:.0%})')
    if report.mean_wall_time_s:
        print(f'  Mean wall time: {report.mean_wall_time_s:.0f}s')
    if report.success_rate < 0.5:
        print(f'  => smoking gun found!')
        break
    else:
        print(f'  => passed, escalating...')
"
```

- [ ] **Step 3: Commit chapter + evidence**

```bash
git add docs/chapters/part3b-implementer-orchestrator.md docs/superpowers/research/YYYY-MM-DD-sp2-baseline-phase-*.md docs/superpowers/research/sessions/
git commit -m "docs: Part III chapter 2 — implementer + orchestrator + SP2 baseline"
```

---

### Task 7: Chapter 3 — "Lessons from the Handoff"

**Files:**
- Create: `docs/chapters/part3c-lessons-from-handoff.md`
- Create: updated baseline report after tuning

**Purpose:** Examine Chapter 2's failure patterns, tune the packet/prompt, and re-measure. Demonstrate "structure beats strings" live.

- [ ] **Step 1: Analyze Chapter 2 failures**

Read the session JSONLs from Task 6. Catalog failure patterns:
- Was the subagent called at all?
- Did the parent construct valid packets (acceptance strings present)?
- Did the implementer write code? Run tests?
- Did the implementer's self-report match the harness verdict?

- [ ] **Step 2: Tune based on findings**

Update `prompts/orchestrator.md` and/or `.pi/agents/implementer.md` with targeted fixes. Scope: prompt/packet tuning only (no mechanism-level guardrails). Document each change and which failure it addresses.

- [ ] **Step 3: Re-run n=8 baseline**

Same as Task 6 Step 2, with tuned files. Compare to both SP1 baseline and SP2 pre-tuning baseline.

- [ ] **Step 4: Write the chapter**

```markdown
(part3c-lessons-from-handoff)=

# Lessons from the Handoff

## What the first baseline revealed

[Show the failure patterns from Chapter 2, with evidence.]

## Tuning the packet format

[Show each change, the failure it addresses, the before/after.]

## Tuning the parent prompt

[Show each change, the failure it addresses, the before/after.]

## Re-measuring

[Show the post-tuning baseline. Compare to SP1 and pre-tuning. What improved?
What didn't? What needs a mechanism-level fix (Part IV territory)?]

## What you built

[A parent+implementer setup that the reader authored. The measurement data
that feeds Part IV.]
```

- [ ] **Step 5: Commit**

```bash
git add docs/chapters/part3c-lessons-from-handoff.md docs/superpowers/research/
git commit -m "docs: Part III chapter 3 — lessons from the handoff"
```

---

### Task 8: Final wiring — update chapter index and verify build

**Files:**
- Modify: `docs/chapters/index.md`

- [ ] **Step 1: Add Part III entries to the chapter index**

```markdown
- **Part III — Spec-driven development on Pi.** Roadmap-and-packet, a
  parent-as-orchestrator system prompt, an implementer specialist. *(queued)*
```

Add to toctree:

```markdown
part3a-subagent-mechanism
part3b-implementer-orchestrator
part3c-lessons-from-handoff
```

- [ ] **Step 2: Verify the Sphinx build**

```bash
uv run sphinx-build -b html docs docs/_build -W
```

- [ ] **Step 3: Commit**

```bash
git add docs/chapters/index.md
git commit -m "docs: wire Part III chapters into index"
```

---

## Self-Review

**Spec coverage:**
- Subagent mechanism install/verify → Task 0 ✓
- Harness invocation profiles → Task 1 ✓
- Implementer specialist → Task 2 ✓
- Orchestrator prompt → Task 3 ✓
- End-to-end verification → Task 4 ✓
- Chapter 1 (mechanism) → Task 5 ✓
- Chapter 2 (implementer + orchestrator + baseline) → Task 6 ✓
- Chapter 3 (lessons from handoff) → Task 7 ✓
- Chapter index wiring → Task 8 ✓

**Placeholder scan:**
- Task 4 is verification-only (no code to commit) — intentional, not a placeholder.
- Chapter content (Tasks 5, 6, 7) contains structure, not verbatim prose — the implementer fills in with actual outputs from preceding tasks. This is consistent with the SP1 plan's chapter task approach.
- No "TBD," "TODO," or "implement later" patterns.

**Type consistency:**
- `InvocationProfile` defined in Task 1, consumed in Tasks 2-6 ✓
- `InvocationProfile.sp1()` and `.sp2(path)` factories defined in Task 1 ✓
- `has_subagent_calls(stream_path) -> bool` defined in Task 1, consumed in Task 4 ✓
- `run_session` gains `profile: InvocationProfile` in Task 1 ✓
- `run_baseline` gains `profile: InvocationProfile` in Task 1 ✓
