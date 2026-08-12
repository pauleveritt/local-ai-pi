import json
from pathlib import Path

from harness.telemetry import ToolCall, read_telemetry

FIXTURE = Path(__file__).parent / "fixtures" / "pi-run-0.82.0.jsonl"
DELEGATION_FIXTURE = (
    Path(__file__).parent / "fixtures" / "pi-run-0.83.0-delegation.jsonl"
)


def _real_run() -> str:
    return FIXTURE.read_text()


def test_counts_one_turn_per_turn_end_event():
    assert read_telemetry(_real_run()).turns == 6


def test_sums_token_usage_across_turn_end_events():
    # Also the double-count guard: `message_end` carries `message.usage`
    # too, on 6 of this stream's 12 message_end events. A reader that
    # summed both event types would report exactly twice these numbers.
    telemetry = read_telemetry(_real_run())
    assert telemetry.input_tokens == 7068
    assert telemetry.output_tokens == 933
    assert telemetry.cache_read_tokens == 6144
    assert telemetry.cache_write_tokens == 0


def test_context_processed_sums_input_and_both_cache_fields():
    assert read_telemetry(_real_run()).context_processed == 13212


def test_pairs_tool_starts_with_their_ends_in_start_order():
    assert read_telemetry(_real_run()).tool_calls == (
        ToolCall(name="bash", is_error=False),
        ToolCall(name="write", is_error=False),
        ToolCall(name="write", is_error=False),
        ToolCall(name="write", is_error=False),
        ToolCall(name="write", is_error=False),
    )


def test_a_healthy_run_is_complete():
    assert read_telemetry(_real_run()).complete is True


def test_a_malformed_final_line_is_skipped_not_raised():
    # A process killed mid-write leaves a partial final line, exactly as
    # harness/checkpoint.py already tolerates.
    stream = (
        '{"type": "turn_end", "message": {"usage": '
        '{"input": 10, "output": 2, "cacheRead": 0, "cacheWrite": 0, "reasoning": 0}}}\n'
        '{"type": "agent_end"}\n'
        '{"type": "turn_en'
    )
    telemetry = read_telemetry(stream)
    assert telemetry.turns == 1
    assert telemetry.input_tokens == 10


def test_a_tool_start_with_no_end_is_unknown_not_successful():
    # agent_end IS present here, so `complete is False` is driven purely
    # by the unmatched start -- not by a missing end-of-agent marker.
    stream = (
        '{"type": "tool_execution_start", "toolCallId": "call_1", "toolName": "bash"}\n'
        '{"type": "tool_execution_end", "toolCallId": "call_1", '
        '"toolName": "bash", "isError": false}\n'
        '{"type": "tool_execution_start", "toolCallId": "call_2", "toolName": "write"}\n'
        '{"type": "agent_end"}\n'
    )
    telemetry = read_telemetry(stream)
    assert telemetry.tool_calls == (
        ToolCall(name="bash", is_error=False),
        ToolCall(name="write", is_error=None),
    )
    assert telemetry.tool_calls[1].is_error is None
    assert telemetry.complete is False


def test_a_stream_truncated_before_any_turn_end_reports_zero_not_an_error():
    stream = (
        '{"type": "session", "version": "0.82.0"}\n'
        '{"type": "agent_start"}\n'
        '{"type": "turn_start"}\n'
        '{"type": "message_start", "message": {"role": "assistant"}}\n'
    )
    telemetry = read_telemetry(stream)
    assert telemetry.turns == 0
    assert telemetry.tool_calls == ()
    assert telemetry.input_tokens == 0
    assert telemetry.output_tokens == 0
    assert telemetry.cache_read_tokens == 0
    assert telemetry.cache_write_tokens == 0
    assert telemetry.context_processed == 0
    assert telemetry.complete is False


def test_reasoning_tokens_are_folded_into_output_tokens():
    # gemma-4-12B emits 0 reasoning tokens, so the real fixture cannot
    # prove this. The fold exists so a future reasoning-capable model's
    # generated tokens cannot vanish silently.
    stream = (
        '{"type": "turn_end", "message": {"usage": '
        '{"input": 10, "output": 5, "cacheRead": 0, "cacheWrite": 0, "reasoning": 7}}}\n'
        '{"type": "agent_end"}\n'
    )
    assert read_telemetry(stream).output_tokens == 12


def test_a_line_separator_inside_message_text_does_not_fracture_the_line():
    # U+2028/U+2029 are legal unescaped inside a JSON string, and pi is a
    # Node tool -- Node's JSON.stringify emits them raw rather than
    # \u-escaped. str.splitlines() treats U+2028 as a line break, so a
    # naive split fractures one valid JSON line into two invalid halves,
    # silently dropping the turn's tokens while agent_end still parses.
    # ensure_ascii=False is required to reproduce that: the default
    # ascii-escapes U+2028 away, which would make this test vacuous.
    content = json.dumps("line one line two", ensure_ascii=False)
    stream = (
        '{"type": "turn_end", "message": {"content": ' + content + ", "
        '"usage": {"input": 500, "output": 50, "cacheRead": 0, "cacheWrite": 0, "reasoning": 0}}}\n'
        '{"type": "agent_end"}\n'
    )
    telemetry = read_telemetry(stream)
    assert telemetry.turns == 1
    assert telemetry.input_tokens == 500
    assert telemetry.complete is True


def test_a_tool_update_with_no_end_is_unknown_not_successful():
    # tool_execution_update (a streaming progress event) must not be
    # mistaken for tool_execution_end. A tool killed after emitting an
    # update but before finishing is exactly the case complete=False
    # exists to catch.
    stream = (
        '{"type": "tool_execution_start", "toolCallId": "call_1", "toolName": "bash"}\n'
        '{"type": "tool_execution_update", "toolCallId": "call_1", '
        '"toolName": "bash", "partialResult": {}}\n'
        '{"type": "agent_end"}\n'
    )
    telemetry = read_telemetry(stream)
    assert telemetry.tool_calls == (ToolCall(name="bash", is_error=None),)
    assert telemetry.complete is False


def test_tool_errors_counts_only_calls_that_reported_an_error():
    # Non-vacuity pin. `None` means *unknown*, not failure, and has two
    # distinct sources -- an unmatched start (c3) and a matched end
    # carrying no isError field (c4). Counting either would be the
    # plausible wrong implementation, so this asserts they are excluded
    # specifically rather than only asserting the total.
    stream = (
        '{"type": "tool_execution_start", "toolCallId": "c1", "toolName": "bash"}\n'
        '{"type": "tool_execution_end", "toolCallId": "c1", "isError": true}\n'
        '{"type": "tool_execution_start", "toolCallId": "c2", "toolName": "bash"}\n'
        '{"type": "tool_execution_end", "toolCallId": "c2", "isError": false}\n'
        '{"type": "tool_execution_start", "toolCallId": "c3", "toolName": "write"}\n'
        '{"type": "tool_execution_start", "toolCallId": "c4", "toolName": "write"}\n'
        '{"type": "tool_execution_end", "toolCallId": "c4"}\n'
        '{"type": "agent_end"}\n'
    )
    telemetry = read_telemetry(stream)
    assert [call.is_error for call in telemetry.tool_calls] == [
        True,
        False,
        None,
        None,
    ]
    assert telemetry.tool_errors == 1


def test_a_clean_real_run_reports_zero_tool_errors():
    # A weak pin on its own -- zero -- which is why the synthetic
    # mixed-outcome test above carries the non-vacuity weight. It is the
    # only real-data pin available: tests/fixtures/phase1-n48-telemetry-summary.json
    # holds only turns and context_processed, and extending it would
    # change a checksum already recorded in tests/fixtures/README.md.
    assert read_telemetry(_real_run()).tool_errors == 0


ENTRY_FIXTURE = (
    Path(__file__).parent / "fixtures" / "pi-run-0.82.0-entry-appended.jsonl"
)


def test_reads_custom_entry_types_from_a_real_run():
    assert "evidence" in read_telemetry(ENTRY_FIXTURE.read_text()).custom_entries


def test_the_pre_cycle1_fixture_has_no_custom_entries():
    # Regression guard on the inert behaviour: 80 runs produced none,
    # because the entry was appended before print mode subscribed.
    assert read_telemetry(_real_run()).custom_entries == ()


def test_reads_custom_entry_types_in_stdout_order():
    stream = "\n".join(
        json.dumps(
            {"type": "entry_appended", "entry": {"type": "custom", "customType": name}}
        )
        for name in ("first", "second")
    )

    assert read_telemetry(stream).custom_entries == ("first", "second")


def test_skips_an_appended_entry_that_is_not_a_custom_entry():
    # appendEntry is not the only thing that appends an entry. A label
    # change is not evidence.
    stream = json.dumps(
        {"type": "entry_appended", "entry": {"type": "label_change", "label": "x"}}
    )

    assert read_telemetry(stream).custom_entries == ()


def test_skips_a_custom_entry_whose_type_is_not_a_string():
    stream = json.dumps(
        {"type": "entry_appended", "entry": {"type": "custom", "customType": 7}}
    )

    assert read_telemetry(stream).custom_entries == ()


def test_a_missing_custom_entry_does_not_make_a_run_incomplete():
    # The extension observes. It must never fail a run the model
    # actually completed.
    assert read_telemetry(_real_run()).complete is True


def _delegation_end(call_id: str, **usage) -> str:
    """One successful `subagent` end event carrying the given child usage."""
    return json.dumps(
        {
            "type": "tool_execution_end",
            "toolCallId": call_id,
            "toolName": "subagent",
            "result": {
                "details": {
                    "results": [{"agent": "implementer", "exitCode": 0, "usage": usage}]
                }
            },
        }
    )


def test_a_delegated_run_reports_the_childs_cost():
    """The regression this cycle exists for. Phase 5 cycle 2 published a
    1.15x cost ratio when the true figure was 8.11x, because telemetry
    counted the parent and the child did most of the work. Asserted
    against a real trimmed payload, not a synthetic one."""
    telemetry = read_telemetry(DELEGATION_FIXTURE.read_text())

    assert len(telemetry.delegations) == 1
    assert telemetry.delegations[0].agent == "implementer"
    assert telemetry.child_turns > telemetry.turns
    assert telemetry.total_context_processed > 3 * telemetry.context_processed


def test_totals_are_parent_plus_child():
    telemetry = read_telemetry(DELEGATION_FIXTURE.read_text())

    assert telemetry.total_turns == telemetry.turns + telemetry.child_turns
    assert telemetry.total_context_processed == (
        telemetry.context_processed + telemetry.child_context_processed
    )
    assert telemetry.total_output_tokens == (
        telemetry.output_tokens + telemetry.child_output_tokens
    )


def test_a_run_with_no_delegation_totals_to_its_parent():
    """A bare run's totals must equal its parent figures exactly, or every
    number published before this cycle silently changes meaning. `turn` is
    a pinned term; this is what pins it."""
    telemetry = read_telemetry(_real_run())

    assert telemetry.delegations == ()
    assert telemetry.total_turns == telemetry.turns
    assert telemetry.total_context_processed == telemetry.context_processed
    assert telemetry.total_output_tokens == telemetry.output_tokens


def test_child_context_processed_includes_both_cache_fields():
    """Same definition as the parent's: input + cacheRead + cacheWrite.
    cacheRead dominates a delegated run -- cycle 2's first child read
    173,056 cached tokens against 23,955 fresh input -- so dropping it
    would understate the cost by most of it."""
    telemetry = read_telemetry(
        _delegation_end(
            "c1", input=100, output=10, cacheRead=1000, cacheWrite=7, turns=3
        )
    )

    assert telemetry.child_context_processed == 1107
    assert telemetry.child_output_tokens == 10
    assert telemetry.child_turns == 3


def test_child_reasoning_tokens_are_folded_into_output():
    """Mirrors the parent's rule, so a future reasoning-capable child's
    tokens cannot vanish silently."""
    telemetry = read_telemetry(
        _delegation_end("c1", input=1, output=10, reasoning=5, turns=1)
    )

    assert telemetry.child_output_tokens == 15


def test_a_failed_delegation_is_not_counted_as_a_free_success():
    """Cycle 1 found a delegation whose result was the string 'Tool
    subagent not found'. It carries no usage, and counting it as a
    zero-cost delegation would make a broken arm look efficient -- which
    is exactly how a silently unorchestrated batch would read."""
    line = json.dumps(
        {
            "type": "tool_execution_end",
            "toolCallId": "c1",
            "toolName": "subagent",
            "isError": True,
            "result": {
                "content": [{"type": "text", "text": "Tool subagent not found"}],
                "details": {},
            },
        }
    )

    telemetry = read_telemetry(line)

    assert telemetry.delegations == ()
    assert telemetry.child_context_processed == 0


def test_two_delegations_in_one_run_are_both_counted():
    """Cycle 2's runs 4 and 10 each made three delegations; run 4's
    children totalled 128 turns."""
    stream = "\n".join(
        [
            _delegation_end("c1", input=5, output=1, turns=4),
            _delegation_end("c2", input=5, output=1, turns=6),
        ]
    )

    telemetry = read_telemetry(stream)

    assert len(telemetry.delegations) == 2
    assert telemetry.child_turns == 10


def test_a_delegation_with_no_usage_payload_is_skipped_not_crashed():
    """Pi's payload shape is not ours and may change with an upgrade. An
    end event carrying a results list but no usage must not raise."""
    line = json.dumps(
        {
            "type": "tool_execution_end",
            "toolCallId": "c1",
            "toolName": "subagent",
            "result": {"details": {"results": [{"agent": "implementer"}]}},
        }
    )

    telemetry = read_telemetry(line)

    assert telemetry.delegations == ()
    assert telemetry.child_context_processed == 0


def test_a_non_subagent_tool_is_never_read_as_a_delegation():
    """`bash` results carry no usage, but a future tool might. Only
    `subagent` ends are delegations."""
    line = json.dumps(
        {
            "type": "tool_execution_end",
            "toolCallId": "c1",
            "toolName": "bash",
            "result": {
                "details": {
                    "results": [{"agent": "x", "usage": {"input": 9, "turns": 9}}]
                }
            },
        }
    )

    assert read_telemetry(line).delegations == ()


def test_a_failed_delegation_carrying_usage_is_still_not_counted():
    """The `isError` guard, exercised directly.

    Cycle 1's real failure carried an empty `details`, so a test built
    from it passes with or without the guard -- the mutation check caught
    that. A child that errors *after* doing work is plausible and would
    carry usage; its cost belongs in a failure analysis, not in a
    delegation total that a cost ratio is computed from.
    """
    line = json.dumps(
        {
            "type": "tool_execution_end",
            "toolCallId": "c1",
            "toolName": "subagent",
            "isError": True,
            "result": {
                "details": {
                    "results": [
                        {
                            "agent": "implementer",
                            "exitCode": 1,
                            "usage": {"input": 500, "output": 40, "turns": 7},
                        }
                    ]
                }
            },
        }
    )

    telemetry = read_telemetry(line)

    assert telemetry.delegations == ()
    assert telemetry.child_context_processed == 0
    assert telemetry.child_turns == 0
