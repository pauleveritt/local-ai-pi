from pathlib import Path

from harness.telemetry import ToolCall, read_telemetry

FIXTURE = Path(__file__).parent / "fixtures" / "pi-run-0.82.0.jsonl"


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
