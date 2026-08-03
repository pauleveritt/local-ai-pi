# Teaching extensions

Extensions written to demonstrate one mechanism each. **The harness never
loads these** — `harness/runner.py` loads only `.pi/extensions/hello-world.ts`,
and adding anything here to a run would change its recorded conditions.

Run one by hand:

```bash
pi -e examples/extensions/word-count.ts
```

- `word-count.ts` — registering a tool. One tool, no state, no session
  writes, no child processes. If it grows a second responsibility it has
  stopped being a teaching artifact.
