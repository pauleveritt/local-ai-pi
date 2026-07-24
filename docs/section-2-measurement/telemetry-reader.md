(part2a-telemetry-reader)=

# The Telemetry Reader

In Part I you wrote your first Pi extension and learned the shape of the
event lifecycle. Now you need to *measure* what the agent does. A small
local model driving real Python development will go off the rails — but
you cannot claim it went off the rails unless you have the data to prove it.

This chapter builds the first piece of the measurement harness: a telemetry
reader that parses Pi's `--mode json` event stream into structured records
you can inspect, count, and reason about.

## Running pi in `--mode json`

Pi's `--mode json` flag writes every lifecycle event as a JSON line to stdout.
Run it once and capture the output:

```bash
pi --mode json -p --no-session \
   --model omlx/gemma-4-12B-it-MLX-8bit \
   --no-extensions --extension .pi/extensions/hello-world.ts \
   --no-skills --no-prompt-templates --no-themes --no-context-files \
   --approve \
   "Write a hello world script in Python" \
   < /dev/null > session.jsonl
```

The `--no-*` flags strip everything except the hello-world extension you wrote
in Part I. This isolation is important: a headless eval run must not pick up
your RTK proxy, your Superpowers skills, or any other global configuration.
Only what you intentionally place should be present.

```{note}
The prompt is passed as a positional argument, not after `--`. Pi's CLI
parser rejects the `--` separator in this mode.
```

You now have a `session.jsonl` file. Each line is a JSON object with a `type`
field. Let's see what Pi emitted:

```bash
python3 -c "
import json
types = set()
for line in open('session.jsonl'):
    try:
        ev = json.loads(line)
        types.add(ev.get('type', '?'))
    except: pass
print(sorted(types))
"
```

You'll see something like:

```
['agent_end', 'agent_settled', 'agent_start', 'message_end', 'message_start',
 'message_update', 'session', 'tool_execution_end', 'tool_execution_start',
 'tool_execution_update', 'turn_end', 'turn_start']
```

Twelve event types. Four groups: session lifecycle, agent lifecycle, message
streaming, and tool execution.

## The event schema

Here is the actual schema captured from Pi 0.81.1 running against Gemma 4 12B
via oMLX:

### Session lifecycle

| Event | Fields | When |
|-------|--------|------|
| `session` | `cwd`, `id`, `timestamp`, `version` | Once, at start |

### Agent lifecycle

| Event | Fields | When |
|-------|--------|------|
| `agent_start` | (none) | LLM wakes up |
| `agent_end` | `messages`, `willRetry` | LLM finishes |
| `agent_settled` | (none) | Optional, after agent_end |

### Turn lifecycle

| Event | Fields | When |
|-------|--------|------|
| `turn_start` | (none) | Each turn begins |
| `turn_end` | `message`, `toolResults` | Each turn ends |

### Message streaming

| Event | Fields | What |
|-------|--------|------|
| `message_start` | `message` (role + content) | Message begins streaming |
| `message_update` | `assistantMessageEvent`, `message` | Incremental content |
| `message_end` | `message` (role + content) | Message complete |

### Tool execution

| Event | Fields | What |
|-------|--------|------|
| `tool_execution_start` | `toolCallId`, `toolName`, `args` (JSON string) | Tool begins |
| `tool_execution_update` | `toolCallId`, `toolName`, `args`, `partialResult` | Optional progress |
| `tool_execution_end` | `toolCallId`, `toolName`, `result` (JSON string), `isError` (string: "True"/"False") | Tool done |

```{warning}
Two surprising things from this capture:

1. **No token counts in json mode.** Pi 0.81.1's `--mode json` stream does not
   include input/output token usage in any event. We will track turns and tool
   calls but not token cost from the JSONL alone. Token data IS available via
   `--mode rpc` and the `get_session_stats` command — that path is deferred to
   a later chapter.

2. **`isError` is a string.** The `isError` field on `tool_execution_end` is
   `"True"` or `"False"` (a JSON string), not a boolean. Your parser must
   convert it.

3. **Args live on `tool_execution_start`.** The `args` field (what the tool was
   called with) is on the start event, not the end event. Correlate by
   `toolCallId`.
```

## Building the telemetry reader

We need three things from each run:

1. **What prompt was given.** Extract from `message_end` events where
   `message.role == "user"`.
2. **What tools were called.** Collect from `tool_execution_end` events.
3. **How many turns occurred.** Count `turn_end` events.

### The dataclass

```python
from dataclasses import dataclass, field

@dataclass
class ToolCall:
    name: str
    args: dict
    result: str | None = None
    is_error: bool = False

@dataclass
class RunTelemetry:
    prompts: list[str] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)
    turns: int = 0
```

No token fields because the JSONL doesn't carry that data.

### The parser

The `read_run()` function walks a JSONL file line-by-line, skipping malformed
lines so partial captures don't crash:

```python
def read_run(stream_path):
    for line in path.read_text().splitlines():
        event = json.loads(line)
        etype = event.get("type", "")

        if etype == "message_end":
            message = event.get("message", {})
            if message.get("role") == "user":
                # Extract text from content blocks
                for block in message.get("content", []):
                    if block.get("type") == "text":
                        prompts.append(block["text"])

        elif etype == "tool_execution_end":
            tool_calls.append(ToolCall(
                name=event.get("toolName", "unknown"),
                args=_parse_args(event.get("args", "{}")),
                result=event.get("result"),
                is_error=event.get("isError", "False") == "True",
            ))

        elif etype == "turn_end":
            turns += 1
```

### Testing against the captured fixture

The project includes `tests/fixtures/sample-session.jsonl` — a real Pi session
captured against the AgentClinic app. Your tests run against this fixture and
assert:

- At least one prompt is extracted
- Tool calls are collected
- Turns are counted
- Empty and malformed streams are handled gracefully

```bash
uv run pytest tests/test_telemetry.py -v
```

```{note}
The fixture is the **ground truth**. Event type strings and field names in
`telemetry.py` came from examining the fixture, not from documentation.
If Pi's event schema changes in a later version, re-capture the fixture
and update the parser.
```

## What you built

By the end of this chapter you have `harness/telemetry.py` — a module that
reads a `pi --mode json` stream and returns structured telemetry: prompts,
tool calls, and turns. In the next chapter you will provision a disposable
workspace and run pi inside it.
