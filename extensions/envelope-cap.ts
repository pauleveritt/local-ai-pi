import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

/**
 * The engine child's budgets, and nothing else.
 *
 * The factorial showed the engine posting a far tighter wall-time
 * distribution than an unrestricted baseline at comparable acceptance. That
 * has two competing explanations and the two-arm design cannot separate them:
 * deterministic mutation and orchestration might be doing it, or the child's
 * *topology* might be -- one attempt, no shell, no test loop, hard budgets.
 * Independent review named this as the reason the tighter envelope stays
 * unattributed.
 *
 * This extension is the discriminator. Paired with `--tools read,write` it
 * gives a plain agent the same envelope the child runs inside, with none of
 * the orchestration: no controller, no typed handoff, no deterministic
 * mutation engine, no verification.
 *
 * - If that arm also runs tight, the envelope comes from the constraints and
 *   the honest name for the effect is **constrained latency**.
 * - If only the full engine runs tight, the constraints alone do not explain
 *   it and the directness claim survives its sharpest objection.
 *
 * Deliberately *not* included: the loop breaker and the mutation engine's
 * revision checks. Those are mechanism, not envelope, and folding them in
 * would blur the very line this arm exists to draw. The budgets below mirror
 * `MAX_IMPLEMENTER_TURNS` in `implementer.ts` and the default `maxTools` in
 * `implementer-policy.ts`; if either moves, this must move with it or the arm
 * silently stops matching.
 */
export const ENVELOPE_MAX_TURNS = 16;
export const ENVELOPE_MAX_TOOLS = 30;

export default function envelopeCap(pi: ExtensionAPI) {
	let turns = 0;
	let tools = 0;

	pi.on("turn_start", async (_event, ctx) => {
		turns += 1;
		if (turns <= ENVELOPE_MAX_TURNS) return;
		pi.appendEntry("turn_budget_exhausted", { budget: ENVELOPE_MAX_TURNS, attempted: turns });
		ctx.abort();
	});

	pi.on("tool_call", async () => {
		tools += 1;
		if (tools <= ENVELOPE_MAX_TOOLS) return undefined;
		pi.appendEntry("tool_budget_exhausted", { budget: ENVELOPE_MAX_TOOLS, attempted: tools });
		return {
			block: true,
			reason: `The tool budget of ${ENVELOPE_MAX_TOOLS} calls is exhausted. Stop and report what remains.`,
		};
	});
}
