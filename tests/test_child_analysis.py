"""The recompute script must count events, never substrings.

Phase 5 cycle 13, written because of a live mistake. Cycle 11's first
reported cost figures -- a "4.4x tool-call ratio" and refusal counts of 294
against 65 -- came from counting occurrences of `"toolCallId"` and of the
loop-breaker's refusal text as substrings of the raw `pi_stdout`. Parsed
from events the ratio is 1.33x and the refusals are 12 against 13.

**The reason it was not merely noisy but actively misleading** is that the
inflation factor differs per arm: 10.0x for bare, 6.7x for facts-only, and
21.9x for the orchestrated arm. Pi repeats a single tool call across
`tool_execution_end`, `message_start`, `message_end`, `turn_end` and
`agent_end`; on top of that, the subagent extension's `tool_execution_update`
carries the child's *entire message list so far*, so a child making n calls
has its early calls re-serialized in every later update -- quadratic in
per-run call count, and therefore worst in exactly the arm that delegates.
Two cycle-10 runs made 34 real child calls each and emitted 70 updates
carrying 1,224 serialized `toolCall` blocks.

So a substring count does not over-report every arm alike, which a ratio
would cancel. It manufactures a difference between arms out of how much
they delegate. That is why this is a test and not a comment.

The streams below are synthetic and hold the shape, not the volume, so this
runs without the checkpoints -- which live outside version control in
`~/local-ai-pi-evidence/` and cannot be depended on by a test.
"""

import importlib.util
import json

from harness import runner

SCRIPT = (
    runner.REPO_ROOT
    / "docs"
    / "superpowers"
    / "research"
    / "2026-08-04-phase5-cycle8-child-analysis.py"
)


def _analysis():
    """Import the recompute script, whose date-prefixed name is not a
    module name. It is imported rather than copied so that this pins the
    published figures' actual source and not a lookalike.
    """
    spec = importlib.util.spec_from_file_location("child_analysis", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _refusal_result() -> dict:
    return {
        "content": [
            {
                "type": "text",
                "text": (
                    "You have already run this exact bash call 5 times in a "
                    "row and the result will not change. Do not repeat it."
                ),
            }
        ]
    }


def _stream_with_one_refusal_echoed_everywhere() -> str:
    """One refused call, as Pi actually reports it: once as the execution
    result, and again inside four other events that carry the same text.
    """
    refusal = _refusal_result()
    events = [
        {"type": "message_start", "message": refusal},
        {"type": "tool_execution_end", "toolCallId": "call-1", "result": refusal},
        {"type": "message_end", "message": refusal},
        {"type": "turn_end", "messages": [refusal]},
        {"type": "agent_end", "messages": [refusal]},
    ]
    return "\n".join(json.dumps(event) for event in events)


def test_a_single_refusal_is_counted_once_not_once_per_event():
    stream = _stream_with_one_refusal_echoed_everywhere()
    analysis = _analysis()

    naive = stream.count(analysis.BLOCK_MARKER)
    assert naive == 5, "fixture should reproduce the echo that caused the error"

    assert analysis.parent_blocks(stream) == 1


def _stream_with_cumulative_child_updates() -> str:
    """A child making three calls, reported the way the subagent extension
    reports them: every update repeats the whole transcript so far.
    """
    calls = [
        {"type": "toolCall", "name": "bash", "arguments": {"command": f"echo {n}"}}
        for n in range(3)
    ]
    events = []
    for step in range(1, len(calls) + 1):
        events.append(
            {
                "type": "tool_execution_update",
                "toolName": "subagent",
                "toolCallId": "delegation-1",
                "partialResult": {
                    "details": {
                        "results": [
                            {
                                "stopReason": "stop",
                                # The whole transcript so far, again.
                                "messages": [
                                    {"role": "assistant", "content": [call]}
                                    for call in calls[:step]
                                ],
                            }
                        ]
                    }
                },
            }
        )
    return "\n".join(json.dumps(event) for event in events)


def test_cumulative_updates_do_not_multiply_the_childs_call_count():
    stream = _stream_with_cumulative_child_updates()
    analysis = _analysis()

    naive = stream.count('"toolCallId"')
    assert naive == 3, "fixture should reproduce the re-serialization"

    calls, stop, _steps, _blocks = analysis.child_calls(stream)

    # Three distinct calls were executed. The naive count sees 1+2+3 = 6
    # serialized `toolCall` blocks across the three updates.
    assert stream.count('"toolCall"') == 6
    assert len(calls) == 3
    assert calls == ["bash: echo 0", "bash: echo 1", "bash: echo 2"]
    assert stop == "stop"


def test_every_delegation_is_read_not_only_the_last():
    """Guards a bug this script already had once: keeping only the
    stream-final update dropped every earlier delegation in the run.
    """
    analysis = _analysis()
    stream = "\n".join(
        json.dumps(
            {
                "type": "tool_execution_update",
                "toolName": "subagent",
                "toolCallId": f"delegation-{n}",
                "partialResult": {
                    "details": {
                        "results": [
                            {
                                "stopReason": "stop",
                                "messages": [
                                    {
                                        "role": "assistant",
                                        "content": [
                                            {
                                                "type": "toolCall",
                                                "name": "bash",
                                                "arguments": {"command": f"job {n}"},
                                            }
                                        ],
                                    }
                                ],
                            }
                        ]
                    }
                },
            }
        )
        for n in range(3)
    )

    calls, _stop, _steps, _blocks = analysis.child_calls(stream)

    assert sorted(calls) == ["bash: job 0", "bash: job 1", "bash: job 2"]


def test_the_script_names_the_hazard_where_a_reader_will_meet_it():
    """The counters are correct; the trap is that a substring count *looks*
    correct and is quick to reach for at a terminal. The docstring is the
    only thing standing between the next person and repeating cycle 11's
    mistake, so it is pinned.
    """
    source = SCRIPT.read_text()

    assert "over-reports" in source
    assert "tool_execution_end" in source


def test_the_research_record_publishes_the_retraction():
    """A retracted figure gets a banner, not a silent edit -- the rule this
    project already had, and the one cycle 11 broke.
    """
    record = (
        runner.REPO_ROOT
        / "docs"
        / "superpowers"
        / "research"
        / "2026-08-05-phase5-cycle11-control-arms.md"
    ).read_text()

    assert "Retraction" in record
    assert "4.4" in record and "1.33" in record
