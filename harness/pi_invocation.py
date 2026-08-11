"""The Pi invocation primitives every harness entry point shares.

Extracted from the legacy `harness/runner.py` (2026-08-11 distribution
brief, step 4): `tools/screen_workload.py`, `tools/deliver_candidate.py`,
`tools/leak_probe.py`, `tools/author_contract.py`, and `harness/screen.py`
all reached into a 32 KiB module built around `Suite`/`Improvement` and the
phase 4/5 duration-suite harness just to get `pi_command`, `pi_env`, and
`DEFAULT_MODEL` -- none of which have anything to do with that machinery.
`harness/runner.py` still owns the suite/checkpoint/batch concepts and
imports these back from here rather than redefining them.
"""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = REPO_ROOT / "pi-agent-dir"
DEFAULT_MODEL = "omlx/gemma-4-12B-it-MLX-8bit"


def pi_env(
    inherit_venv: bool = False, agent_dir: Path | None = AGENT_DIR
) -> dict[str, str]:
    """The environment every Pi process the harness starts runs under.

    `agent_dir=None` leaves `PI_CODING_AGENT_DIR` unset, so Pi reads the
    operator's own `~/.pi/agent`. **Measurement must never do this** --
    everything below is the reason. It exists for `deliver_candidate`,
    which is not measurement: it runs on a contributor's repository with
    a contributor's model, and pinning it to this repo's agent directory
    means their `--model` does not resolve unless they have replicated
    this laptop. The trade is explicit -- their own extensions then load
    in delegated children -- and it is theirs to make, not ours.

    `PI_CODING_AGENT_DIR` points Pi at `pi-agent-dir/` instead of
    `~/.pi/agent`. The parent does not need this -- it already passes
    `--no-extensions --no-skills --no-prompt-templates --no-themes
    --no-context-files` and is hermetic. **The child does.**

    The delegated child is spawned by Pi's shipped subagent extension as
    `pi --mode json -p --no-session [...]`, carrying none of those flags,
    and user-scope resources load unconditionally -- so before phase 5
    cycle 9 the child loaded the operator's own `~/.pi/agent/extensions/`
    and packages. That was not a theory: recorded child transcripts show
    `ls -R` returning the output of `rtk ls -R`, because the operator's
    `rtk.ts` rewrites bash commands on `tool_call`.

    An environment variable is the only seam that reaches the child. The
    shipped extension calls `spawn` without an `env` argument, so the child
    inherits ours; its *arguments* are fixed and its project-local resources
    are trust-gated away in a headless run.

    **The harness's own virtualenv is stripped.** Passing `os.environ`
    through put `.venv/bin` first on the child's `PATH` and set
    `VIRTUAL_ENV`, so an executor with a shell had the *grader's*
    interpreter as its `python3`. That was harmless while the envelope was
    `read,write`; the first screen run with `bash` in the tool set spent
    eight turns trying to make `import svcs` work, ran `ensurepip`, and
    then `pip install`ed attrs, pytest and pytest-asyncio into the
    harness venv -- replacing the pinned pytest 8.3.4 with 9.1.1. An
    executor that can change the tooling that grades it is not being
    measured, and a workspace it can reach outside of is not hermetic.

    `SSH_AUTH_SOCK` goes for the same reason: a live agent socket is
    push access to every remote the operator can reach, and nothing in a
    replay task needs the network.

    The frozen cohort environment was never exposed and was verified
    unaffected -- it lives under `.workloads/env` and is passed to
    `run_suite` explicitly, not through `PATH`.

    `inherit_venv=True` restores the old behaviour, and exists for one
    reason: phase 5's suites are built on it. Their stack prompts assert
    that FastAPI, Jinja2, pytest and httpx are installed and forbid
    installing anything, and that claim is true *because* the workspace
    is bare and the harness venv is inherited. A false claim there is
    worse than none -- a model told not to install a missing package
    cannot recover -- so a closed phase keeps the environment its
    recorded results were measured under. Phase 7 does not use it:
    `screen_task` provisions a real per-workspace environment instead,
    which is what the old arrangement was a poor substitute for.
    """
    env = dict(os.environ)
    if agent_dir is not None:
        env["PI_CODING_AGENT_DIR"] = str(agent_dir)
    else:
        env.pop("PI_CODING_AGENT_DIR", None)
    if inherit_venv:
        return env
    venv = env.pop("VIRTUAL_ENV", None)
    env.pop("SSH_AUTH_SOCK", None)
    if venv:
        # Filtered by prefix rather than exact match: `.venv/bin` is what
        # lands on PATH, and a future layout could add more than one entry
        # under the same root.
        env["PATH"] = os.pathsep.join(
            entry
            for entry in env.get("PATH", "").split(os.pathsep)
            if entry and not Path(entry).is_relative_to(venv)
        )
    return env


def pi_command(
    model: str,
    prompt: str,
    extensions: tuple[Path, ...] = (),
    system_prompt: Path | None = None,
) -> list[str]:
    """Build one hermetic `pi --print` invocation.

    `extensions` defaults to empty here, unlike the legacy `runner.py`
    version this was extracted from (which defaulted to the phase 4/5
    duration-suite's `hello-world.ts`). Every caller of this function,
    inside and outside `runner.py`, already passes `extensions` explicitly
    -- confirmed by reading every call site before this default changed --
    so an empty default is the honest one for a module that has no
    suite-specific extension of its own.
    """
    command = [
        "pi",
        "--print",
        "--mode",
        "json",
        "--no-session",
        "--model",
        model,
        "--no-extensions",
    ]
    for extension in extensions:
        command += ["--extension", str(extension)]
    # `--approve` is not an isolation flag: Pi's help defines it as "Trust
    # project-local files for this run" (cli/args.js:263). It widens trust.
    # Project-local extensions are excluded by `--no-extensions` above, not
    # by anything here -- so removing that flag would make a model-written
    # `.pi/extensions/*.ts` in the workspace loadable.
    command += [
        "--no-skills",
        "--no-prompt-templates",
        "--no-themes",
        "--no-context-files",
        "--approve",
    ]
    # Before the prompt, never after: callers that hash the command's last
    # element as "<task-spec>" (see `runner._conditions`) would hash a
    # trailing flag as the prompt and record the real prompt nowhere.
    if system_prompt is not None:
        command += ["--append-system-prompt", str(system_prompt)]
    command.append(prompt)
    return command
