"""Structured measurements derived from one Pi run's captured stdout.

**A turn is one `turn_end` event.** This definition is load-bearing and
must not drift: any change to it invalidates comparison against every
number this instrument has produced. A prior effort counted assistant
messages in one lesson and a session-level field in another, producing 45
turns versus 6 for comparable work, and poisoned the trend it was
measuring.

**When `complete` is `False`, every count here is a lower bound.** A run
killed mid-flight loses the tokens of its unfinished turn entirely, and
leaves tool calls whose outcome is unknown rather than successful.

This is a derived, recomputable view and never load-bearing storage -- but
only because checkpoints retain raw `pi_stdout`. Trimming stdout from
checkpoint records would make every telemetry number ever computed
unreproducible.

**Every field here is the parent's, and `total_*` is the run's.** `turns`
and `context_processed` count the Pi process the harness launched. When that
process delegates, the child's cost arrives second-hand in the parent's
`tool_execution_end` payload and is parsed into `delegations`; `total_turns`,
`total_context_processed` and `total_output_tokens` add it back. The
distinction is not cosmetic: phase 5 cycle 2 published a cost ratio of 1.15x
where the true figure was 8.11x, because the parent is frugal and the child
does the work. The parent-only fields keep their original meanings so that
every number published before that fix stays valid -- `turn` is a pinned
term, and new numbers arrive under new names.

**Custom entries never affect a run's verdict.** `custom_entries` records
what the extension emitted; it has no bearing on `complete`, on
`RunResult.accepted`, or on grading. The extension observes. Letting it
fail a run the model actually completed would make the instrument a
participant in what it measures.
"""

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class ToolCall:
    name: str
    is_error: bool | None  # None = no matching end, or an end with no isError field


@dataclass(frozen=True)
class Delegation:
    """One completed child, as *the parent's stream* reports it.

    Pi's shipped subagent extension aggregates the child's `message_end`
    usage and surfaces it in the parent's `tool_execution_end` result under
    `details.results[]`. So this is the child's own accounting, read
    second-hand -- not a count this project made.

    **`turns` here is therefore not measured the way `RunTelemetry.turns`
    is.** Ours is one per `turn_end` event in a stream we parsed; this is a
    number the extension computed from a stream we never saw. Both are
    called turns. If the two ever need to be strictly comparable, the
    child's raw stream would have to be captured separately -- the
    parent/child attribution work that remains deferred.

    `contextTokens` and `cost` from that payload are deliberately not read:
    the first is a context-window size rather than a workload measure, and
    the second reads 0 against a local server and would invite a cost claim
    this project has never made.
    """

    agent: str
    turns: int
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    exit_code: int | None

    @property
    def context_processed(self) -> int:
        return self.input_tokens + self.cache_read_tokens + self.cache_write_tokens


@dataclass(frozen=True)
class RunTelemetry:
    turns: int
    tool_calls: tuple[ToolCall, ...]
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    complete: bool  # the run finished normally; counts are lower bounds if False
    custom_entries: tuple[str, ...]  # customType of each entry_appended, in order
    delegations: tuple[Delegation, ...]  # one per successful `subagent` call

    @property
    def context_processed(self) -> int:
        return self.input_tokens + self.cache_read_tokens + self.cache_write_tokens

    @property
    def tool_errors(self) -> int:
        """Count of tool calls that finished and reported an error.

        Counts `is_error is True` only. `None` means *unknown*, not a
        failure, and has two sources (see `ToolCall.is_error`): a start
        with no matching end -- where `complete` already declares every
        count a lower bound -- and a matched end carrying no `isError`
        field, which `complete` deliberately still counts as a complete
        run. Neither is counted here.
        """
        return sum(1 for call in self.tool_calls if call.is_error)

    @property
    def child_turns(self) -> int:
        return sum(d.turns for d in self.delegations)

    @property
    def child_output_tokens(self) -> int:
        return sum(d.output_tokens for d in self.delegations)

    @property
    def child_context_processed(self) -> int:
        return sum(d.context_processed for d in self.delegations)

    @property
    def total_turns(self) -> int:
        return self.turns + self.child_turns

    @property
    def total_output_tokens(self) -> int:
        return self.output_tokens + self.child_output_tokens

    @property
    def total_context_processed(self) -> int:
        return self.context_processed + self.child_context_processed


def read_telemetry(pi_stdout: str) -> RunTelemetry:
    turns = 0
    input_tokens = 0
    output_tokens = 0
    cache_read_tokens = 0
    cache_write_tokens = 0
    started: dict[str, str] = {}  # toolCallId -> toolName, in start order
    ended: dict[str, bool | None] = {}  # toolCallId -> isError
    agent_ended = False
    custom_entries: list[str] = []
    delegations: list[Delegation] = []

    # Split on "\n" only, not str.splitlines()'s full line-break set.
    # pi is a Node tool; Node's JSON.stringify emits U+2028/U+2029 raw
    # rather than \u-escaped, and both are legal unescaped inside a JSON
    # string. splitlines() treats them as breaks too, fracturing one
    # valid JSON line into two invalid halves -- silently dropping a
    # turn's tokens while agent_end still parses, misreporting complete.
    for line in pi_stdout.split("\n"):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            # A process killed mid-write leaves a partial final line.
            # Tolerated, as harness/checkpoint.py already tolerates one.
            continue
        match event.get("type"):
            case "turn_end":
                turns += 1
                # Usage is per-turn, not cumulative -- verified across all
                # 16 runs of the real batch, where per-turn input is
                # non-monotonic. Reading only the final event would
                # undercount badly.
                usage = event.get("message", {}).get("usage", {})
                input_tokens += usage.get("input", 0)
                # Reasoning tokens are generated output. Folding them in
                # rather than giving them their own field means a future
                # reasoning-capable model's tokens cannot vanish
                # silently, and no assertion has to fire to prevent it.
                output_tokens += usage.get("output", 0) + usage.get("reasoning", 0)
                cache_read_tokens += usage.get("cacheRead", 0)
                cache_write_tokens += usage.get("cacheWrite", 0)
            case "tool_execution_start":
                started[event["toolCallId"]] = event["toolName"]
            case "tool_execution_end":
                ended[event["toolCallId"]] = event.get("isError")
                if event.get("toolName") == "subagent" and not event.get("isError"):
                    details = event.get("result", {}).get("details") or {}
                    for result in details.get("results") or []:
                        usage = result.get("usage")
                        if not isinstance(usage, dict):
                            continue
                        delegations.append(
                            Delegation(
                                agent=result.get("agent", "<unknown>"),
                                turns=usage.get("turns", 0),
                                input_tokens=usage.get("input", 0),
                                output_tokens=usage.get("output", 0)
                                + usage.get("reasoning", 0),
                                cache_read_tokens=usage.get("cacheRead", 0),
                                cache_write_tokens=usage.get("cacheWrite", 0),
                                exit_code=result.get("exitCode"),
                            )
                        )
            case "agent_end":
                agent_ended = True
            case "entry_appended":
                entry = event.get("entry")
                if not isinstance(entry, dict) or entry.get("type") != "custom":
                    continue
                custom_type = entry.get("customType")
                if isinstance(custom_type, str):
                    custom_entries.append(custom_type)

    tool_calls = tuple(
        ToolCall(name=name, is_error=ended.get(call_id))
        for call_id, name in started.items()
    )

    return RunTelemetry(
        turns=turns,
        tool_calls=tool_calls,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=cache_read_tokens,
        cache_write_tokens=cache_write_tokens,
        # Checked against `ended`'s keys rather than its values so that a
        # matched call carrying no `isError` field still counts as
        # complete, while an unmatched one never does.
        complete=agent_ended and started.keys() <= ended.keys(),
        custom_entries=tuple(custom_entries),
        delegations=tuple(delegations),
    )
