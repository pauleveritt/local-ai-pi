import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

/**
 * Budgets for a headroom probe, which are not the same budgets as an arm.
 *
 * `envelope-cap.ts` caps at 16 turns and 30 tool calls because those mirror
 * `MAX_IMPLEMENTER_TURNS` and the implementer policy's default `maxTools`.
 * That envelope exists to answer one question -- whether constrained latency
 * explains the engine's tight wall-time distribution -- and it is calibrated
 * to an arm with `--tools read,write` and no way to execute anything.
 *
 * A headroom probe asks something else: *is this task solvable by a capable
 * executor at all?* A budget that binds converts that question into "solvable
 * within 16 turns", and the two have different answers. The first screen run
 * under the environment arm measured the difference: on `registry-iter`, the
 * declared floor task, the model closed the whole oracle gap, ran the suite,
 * found a failing doctest it had just written, and hit the turn ceiling with
 * the repository still broken. A budget that truncates work mid-repair
 * manufactures the false floor the probe exists to rule out.
 *
 * So these are deliberately loose. They are not a claim that a product should
 * be this generous -- Cycle 5's pilot imposes a tight envelope on purpose,
 * and the difference between the two is then a measurable arm condition
 * rather than an unexamined inheritance.
 *
 * Exhaustion is still recorded, and that matters more than the numbers. A run
 * that stops because it ran out of budget must never be read as a run that
 * could not do the work, and `screen_task` lifts these entries out of the
 * transcript onto the attempt record so the distinction survives into the
 * result.
 */
export const PROBE_MAX_TURNS = 60;
export const PROBE_MAX_TOOLS = 150;

export default function probeCap(pi: ExtensionAPI) {
	let turns = 0;
	let tools = 0;

	pi.on("turn_start", async (_event, ctx) => {
		turns += 1;
		if (turns <= PROBE_MAX_TURNS) return;
		pi.appendEntry("turn_budget_exhausted", { budget: PROBE_MAX_TURNS, attempted: turns });
		ctx.abort();
	});

	pi.on("tool_call", async () => {
		tools += 1;
		if (tools <= PROBE_MAX_TOOLS) return undefined;
		pi.appendEntry("tool_budget_exhausted", { budget: PROBE_MAX_TOOLS, attempted: tools });
		return {
			block: true,
			reason: `The tool budget of ${PROBE_MAX_TOOLS} calls is exhausted. Stop and report what remains.`,
		};
	});
}
