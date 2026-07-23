import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  // ── session_start: the session comes to life ──────────────────────
  pi.on("session_start", async (_event, ctx) => {
    ctx.ui.notify("Session started!", "info");

    // Write an evidence entry into the session JSONL.
    // Part II's telemetry reader will surface this.
    pi.appendEntry({
      type: "evidence",
      data: { event: "session_start", timestamp: Date.now() },
    });
  });

  // ── agent_start: the LLM wakes up ─────────────────────────────────
  pi.on("agent_start", async (_event, ctx) => {
    ctx.ui.notify("Agent started — LLM turn beginning", "info");
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
