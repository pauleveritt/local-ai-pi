"""The leak probe's scoring, tested without a model.

The model call is the expensive part and carries no logic; the logic is in
what counts as disclosure. That is what these pin down, using the two real
drafts that motivated the tool -- one that leaked in prose and passed the
fenced-code gate, one that was clean and the gate rejected.

The failure mode to guard hardest is a false zero. A probe that silently
scores nothing reads as "the contract disclosed nothing", which is the
verdict that lets a contaminated arm run.
"""

from pathlib import Path

from harness.reconstruction import (
    Reconstruction,
    added_source_lines,
    signals,
)


def test_the_same_disclosure_written_two_ways_scores_the_same() -> None:
    """Textual comparison would miss this; that is why comparison is semantic.

    `return iter(...)` and `yield from ...` share no distinctive tokens and
    disclose the identical thing: that the work reads `_services.values()`.
    """
    reference = signals("return iter(self._services.values())")
    generator = signals("yield from self._services.values()")
    other_receiver = signals("yield from registry._services.values()")

    assert "_services.values" in reference
    assert "_services.values" in generator
    assert "_services.values" in other_receiver, "receiver name must not matter"


def test_caller_side_setup_discloses_nothing() -> None:
    """The false positives that got the clean draft rejected.

    A caller-side example names a local variable and a public constructor.
    Neither says anything about the body, and the probe must not count them
    or it reproduces the fenced gate's error in a more expensive form.
    """
    target = signals("return iter(self._services.values())")
    caller = signals('reg = svcs.Registry()\nservices = list(reg)')

    assert not (caller & target), f"caller-side code disclosed {caller & target}"


def test_a_bare_return_parses_rather_than_scoring_zero() -> None:
    """A fix body is mostly `return`/`yield`, which is not a valid module.

    If the forgiving parser regressed, every body-only snippet would score
    zero and every contract would look clean.
    """
    assert signals("return iter(self._services.values())")
    assert signals("yield from self._items.values()")
    assert signals("    raise ServiceNotFoundError(svc_type)")


def test_unparseable_input_scores_nothing_without_raising() -> None:
    assert signals("this is not python at all !!!") == set()
    assert signals("") == set()


def test_test_files_are_not_disclosure() -> None:
    """The executor may not write tests, so a test line discloses no work."""
    patch = (
        "--- a/tests/test_core.py\n+++ b/tests/test_core.py\n"
        "+def test_iter():\n+    assert list(reg) == []\n"
        "--- a/src/svcs/_core.py\n+++ b/src/svcs/_core.py\n"
        "+    def __iter__(self):\n+        return iter(self._services.values())\n"
    )
    kept = added_source_lines(patch)
    assert "_services.values" in kept
    assert "test_iter" not in kept


def test_docstrings_in_the_reference_are_not_the_answer() -> None:
    patch = (
        "--- a/src/x.py\n+++ b/src/x.py\n"
        '+    """\n'
        "+    A recipe for creating a service.\n"
        '+    """\n'
        "+    return iter(self._services.values())\n"
    )
    kept = added_source_lines(patch)
    assert "recipe for creating" not in kept
    assert "_services.values" in signals(kept)


def test_leakage_is_the_difference_not_the_absolute() -> None:
    """A brief that gives the answer away must not condemn the contract.

    `flask-extensions`'s brief names the extension key outright. Scored on
    the absolute, every contract for that task fails forever for something
    no author did.
    """
    result = Reconstruction(
        task_id="brief-already-tells",
        target=("extensions.svcs_registry", "iter()"),
        from_brief=("extensions.svcs_registry",),
        from_contract=("extensions.svcs_registry",),
    )
    assert result.leaked == ()
    assert result.floor == 0.5
    assert result.margin == 0.5

    leaking = Reconstruction(
        task_id="contract-adds-the-fix",
        target=("_services.values", "iter()"),
        from_brief=(),
        from_contract=("_services.values",),
    )
    assert leaking.leaked == ("_services.values",)
    assert leaking.margin == 1.0


def test_the_reference_target_is_extracted_from_the_real_patch() -> None:
    """The target side, end to end on the artifact that caused this tool.

    Only the target is checkable offline. Whether the leaking draft causes a
    reconstruction is a claim about a model, and asserting it here without
    one is how a probe comes to be trusted for something it never showed.
    """
    reference = Path("workloads/svcs/reference-patches/registry-iter.patch")
    assert reference.is_file()

    target = signals(added_source_lines(reference.read_text()))
    assert "_services.values" in target, "the reference fix reads _services.values()"
    assert "iter()" in target


def test_signals_cannot_read_prose_which_is_the_reason_for_the_probe() -> None:
    """The limitation, asserted so it cannot be quietly forgotten.

    The v1 draft's leak was an English sentence -- "the implementation is a
    simple generator that yields from `self._services.values()`". Prose does
    not parse, so this module scores it at zero, and any future attempt to
    use `signals()` *directly on a document* as a leak gate will report
    every prose leak as clean. That is exactly the failure the probe exists
    to route around: it scores what a model rebuilds from the document, not
    the document.
    """
    leaking_sentence = (
        "the implementation is a simple generator that yields from "
        "self._services.values()"
    )
    assert signals(leaking_sentence) == set(), (
        "if this ever starts finding signals in prose, the probe's rationale "
        "changes and this test should be revisited deliberately"
    )
