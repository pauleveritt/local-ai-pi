# The harness-owned Pi agent directory

`PI_CODING_AGENT_DIR` points every Pi process the harness starts at this
directory instead of `~/.pi/agent`. It exists for one reason: **the delegated
child.**

The parent is launched with `--no-extensions --no-skills --no-prompt-templates
--no-themes --no-context-files`, so it is hermetic. The child is not launched by
us — Pi's shipped subagent extension spawns it as `pi --mode json -p
--no-session [...]`, carrying **none** of those flags, and user-scope resources
load unconditionally. Before phase 5 cycle 9, that meant the child loaded the
operator's personal `~/.pi/agent/extensions/` and packages. In this project's
case that included `rtk.ts`, which rewrites bash commands: recorded child
transcripts show `ls -R` returning `rtk ls -R`'s output.

Because the shipped extension passes no `env` to `spawn`, the child inherits
ours — so overriding the agent dir reaches the child, which is the only seam
that does.

That inheritance also makes this the delivery route for `extensions/`:
user-scope extensions load in the child unconditionally, so a guard placed here
reaches it. Project-local `.pi/extensions/` does not — it is trust-gated, and a
headless child has no stored trust decision.

## Contents

- `settings.json` — deliberately names no `packages` and no `skills`. Test
  `test_the_agent_dir_names_no_packages_or_skills` holds that line.
- `models.json` — the one provider and one model this project runs, transcribed
  from the operator's file so the provider definition is a recorded condition
  rather than a machine fact.
- `extensions/` — loaded by the child, and by any process not passing
  `--no-extensions`.

## What is deliberately absent

The operator's `auth.json` is **not** copied here. The `omlx` provider carries
`"apiKey": "not-needed"`, so no credential is required, and a directory the
harness points processes at should never hold one. Adding a provider that needs
a key means solving that separately, not copying that file in.

Pi writes its own empty `auth.json` here on startup, along with sessions and
caches. None of it is committed — `.gitignore` allowlists only the four files
above, and a test asserts that `git ls-files pi-agent-dir` returns exactly
those four.
