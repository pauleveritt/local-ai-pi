import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  // ── session_start: the session comes to life ──────────────────────
  pi.on("session_start", async (_event, ctx) => {
    ctx.ui.notify("Session started!", "info");
  });

  // ── agent_start: the LLM wakes up ─────────────────────────────────
  pi.on("agent_start", async (_event, ctx) => {
    ctx.ui.notify("Agent started — LLM turn beginning", "info");

    // Write an evidence entry into the session.
    // pi.appendEntry(customType, data?) — first arg is a string type ID.
    //
    // This must happen *after* print mode subscribes to session events.
    // `bindExtensions` awaits the `session_start` emission, and the
    // json-mode subscriber is attached only once it returns — so an
    // entry appended during `session_start` is emitted with no
    // subscriber and dropped. That, not `--no-session`, is why 48
    // recorded runs produced nothing. `agent_start` fires during
    // `session.prompt()`, at least once per run and before any
    // model-dependent behaviour. Not exactly once: Pi retries after
    // some agent errors, and a retry fires it again.
    //
    // No timestamp in the payload: the session entry already carries
    // its own, and a second wall-clock value makes every captured
    // stdout differ from the last for no gain.
    pi.appendEntry("evidence", { event: "agent_start" });
  });

  // ── tool_call: a tool is about to execute (can block here) ────────
  pi.on("tool_call", async (event, ctx) => {
    ctx.ui.notify(`Tool called: ${event.toolName}`, "info");
  });

  // ── tool_execution_start: execution begins ────────────────────────
  pi.on("tool_execution_start", async (event, ctx) => {
    ctx.ui.notify(`Executing: ${event.toolName}`, "info");
  });

  // ── tool_execution_end: execution finished ────────────────────────
  pi.on("tool_execution_end", async (event, ctx) => {
    const status = event.isError ? " (FAILED)" : "";
    ctx.ui.notify(`Done: ${event.toolName}${status}`, "info");
  });

  // ── turn_end: the LLM pauses between tool loops ───────────────────
  pi.on("turn_end", async (event, ctx) => {
    ctx.ui.notify(`Turn ${event.turnIndex + 1} complete`, "info");
  });

  // ── agent_end: the LLM rests ──────────────────────────────────────
  pi.on("agent_end", async (_event, ctx) => {
    ctx.ui.notify("Agent finished", "info");
  });
}
