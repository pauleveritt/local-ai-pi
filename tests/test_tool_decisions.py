"""Three decision points in `tools/` that had no coverage.

Each is small, pure, and decides something a published number depends
on -- and each was reachable only through a subprocess before this file
existed, which is why none of them were tested.
"""

import json

import pytest

from tools.author_contract import _parse_transcript
from tools.leak_probe import _majority

# ---- leak_probe._majority: disclosed vs. guessed ----------------------
#
# The threshold that separates "the document discloses this" from "a
# repo-blind model guessed it once". Getting it wrong in either
# direction corrupts the contract-arm gate: too low and a clean contract
# is refused as leaking, too high and a contract carrying the fix is
# admitted.


def test_a_signal_seen_in_every_sample_is_disclosed():
    assert _majority([{"a"}, {"a"}, {"a"}], threshold=2) == ("a",)


def test_a_signal_seen_once_is_a_guess_not_a_leak():
    # The case the docstring names: a repo-blind model guessing once is
    # exactly what a *withholding* document produces, and must not be
    # called a leak.
    assert _majority([{"a"}, set(), set()], threshold=2) == ()


def test_the_threshold_is_inclusive():
    # seen == threshold counts. An exclusive comparison here would make
    # a 3-sample/2-threshold probe silently require unanimity.
    assert _majority([{"a"}, {"a"}, set()], threshold=2) == ("a",)


def test_signals_are_sorted_so_two_runs_are_comparable():
    got = _majority([{"b", "a"}, {"b", "a"}], threshold=2)
    assert got == ("a", "b")


def test_no_samples_discloses_nothing():
    assert _majority([], threshold=2) == ()


# ---- author_contract._parse_transcript --------------------------------
#
# Was three separate walks of the same stream. Consolidated, so these
# pin that the three answers still come out of one pass intact.


def _line(obj: dict) -> str:
    return json.dumps(obj)


def _assistant(text: str, stop: str | None = None) -> str:
    message = {"role": "assistant", "content": [{"type": "text", "text": text}]}
    if stop is not None:
        message["stopReason"] = stop
    return _line({"type": "message_end", "message": message})


def test_the_last_nonempty_assistant_message_wins():
    stdout = "\n".join([_assistant("first"), _assistant("second")])
    text, _, _ = _parse_transcript(stdout)
    assert text == "second"


def test_an_empty_final_message_does_not_erase_the_draft():
    # A trailing whitespace-only message must not blank a real draft --
    # that would turn a good run into a recorded "empty stub".
    stdout = "\n".join([_assistant("the draft"), _assistant("   ")])
    text, _, _ = _parse_transcript(stdout)
    assert text == "the draft"


def test_the_stop_reason_survives_a_later_message_without_one():
    stdout = "\n".join([_assistant("a", stop="max_tokens"), _assistant("b")])
    _, stop_reason, _ = _parse_transcript(stdout)
    assert stop_reason == "max_tokens"


def test_stop_reason_defaults_to_unknown_not_to_success():
    _, stop_reason, _ = _parse_transcript(_assistant("a"))
    assert stop_reason == "unknown"


@pytest.mark.parametrize(
    "custom", ["turn_budget_exhausted", "read_budget_reached", "author_would_not_stop"]
)
def test_budget_markers_are_collected(custom):
    stdout = _line({"type": "entry_appended", "entry": {"customType": custom}})
    _, _, budgets = _parse_transcript(stdout)
    assert budgets == [custom]


def test_an_unrelated_entry_is_not_a_budget():
    stdout = _line({"type": "entry_appended", "entry": {"customType": "satyrn-child-prompt"}})
    _, _, budgets = _parse_transcript(stdout)
    assert budgets == []


def test_malformed_lines_are_skipped_not_fatal():
    # Pi's stdout is not guaranteed to be all-JSON; a truncated final
    # line must cost the parse nothing.
    stdout = "\n".join(["not json at all", _assistant("survived"), "{broken"])
    text, _, _ = _parse_transcript(stdout)
    assert text == "survived"


def test_one_pass_returns_all_three_facts_together():
    # The regression the consolidation exists to prevent: three separate
    # walks could disagree about which run they were describing.
    stdout = "\n".join([
        _line({"type": "entry_appended", "entry": {"customType": "turn_budget_exhausted"}}),
        _assistant("partial draft", stop="aborted"),
    ])
    text, stop_reason, budgets = _parse_transcript(stdout)
    assert (text, stop_reason, budgets) == ("partial draft", "aborted", ["turn_budget_exhausted"])


# ---- report_screen: void attempts leave the denominator ---------------
#
# Roadmap defect 2: `cycle1/summary.json` recorded `attempted: 8` while
# only 7 attempts were real, so every published rate was computed over a
# denominator that included an attempt the model never wrote. The report
# excludes void records from *all* rates. Nothing pinned that.


def _attempt(task_id: str, *, accepted: bool, gap: float, validity: str = "valid") -> dict:
    return {
        "task_id": task_id,
        "validity": validity,
        "validity_evidence": ["read the target implementation"] if validity != "valid" else [],
        "accepted": accepted,
        "gap_closed": gap,
        "oracle_delta": 1 if accepted else 0,
        "out_of_scope": [],
        "model_seconds": 1.0,
        "model_timed_out": False,
        "outcome": "accepted" if accepted else "rejected",
        "rule_version": 8,
    }


def _run_report(tmp_path, records):
    import tools.report_screen as report_screen

    for i, record in enumerate(records):
        (tmp_path / f"{i}.json").write_text(json.dumps(record))
    return report_screen.main(["--dir", str(tmp_path)])


def test_a_void_attempt_leaves_every_denominator(tmp_path, capsys):
    _run_report(tmp_path, [
        _attempt("a", accepted=True, gap=1.0),
        _attempt("b", accepted=False, gap=0.0),
        _attempt("c", accepted=False, gap=0.0, validity="void:read-the-target"),
    ])
    out = capsys.readouterr().out
    # Two real attempts, not three. The defect this pins would print /3.
    assert "accepted         1/2" in out
    assert "gap closed       1/2" in out
    assert "/3" not in out, "a void attempt must not appear in any denominator"


def test_a_void_attempt_is_still_reported_not_hidden(tmp_path, capsys):
    # Excluded from the rates, but never silently dropped -- otherwise
    # the run looks like it had fewer attempts than it was charged for.
    _run_report(tmp_path, [
        _attempt("a", accepted=True, gap=1.0),
        _attempt("voided", accepted=False, gap=0.0, validity="void:read-the-target"),
    ])
    out = capsys.readouterr().out
    assert "VOID" in out and "voided" in out
    assert "read the target implementation" in out, "the evidence must be shown, not just the verdict"


def test_records_without_a_validity_field_count_as_valid(tmp_path, capsys):
    # Older records predate the field. Treating a missing value as void
    # would retroactively empty every banked batch.
    record = _attempt("old", accepted=True, gap=1.0)
    del record["validity"]
    _run_report(tmp_path, [record])
    out = capsys.readouterr().out
    assert "accepted         1/1" in out
