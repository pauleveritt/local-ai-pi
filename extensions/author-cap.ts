import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

/**
 * Budgets for a contract author, which is not an executor.
 *
 * The author runs with `--tools read`: no shell, no write, no edit. It cannot
 * damage a tree, install anything, or reach a network. The only thing a budget
 * buys here is a bound on cost -- and the wall clock already provides one.
 *
 * `probe-cap.ts` was calibrated for an executor making an edit, and inheriting
 * it cost this project three drafts and then a fourth. Under the old authoring
 * prompt, `async-cm-enter`, `fastapi-get-registry` and `magicmock-factory` all
 * ended at exactly 61 turns with `ctx.abort()` and 28-79 bytes of output. They
 * were recorded as "empty stubs" -- read as authors that produced nothing --
 * when what actually happened is that they were killed mid-sentence while
 * still reading. probe-cap's own docstring names this error: "a run that stops
 * because it ran out of budget must never be read as a run that could not do
 * the work."
 *
 * The locating prompt makes it worse, which is how it was caught. That prompt
 * asks for the exact place in the file, the method to sit beside, and the
 * existing pattern to follow, so the author reads far more. `registry-iter`
 * authored cleanly in 23 turns under the old prompt and hit the 60-turn wall
 * under the new one, aborting on the words "Now I have complete context.
 * Writing the contract:".
 *
 * So the shape here is different, not just the numbers. **The tool budget stops
 * reading instead of killing the run.** Blocking a tool call returns a reason
 * to the model, which can then act on it; aborting a turn returns nothing to
 * anyone. An author that has read enough should be told to write the contract,
 * not shot. That turns the observed failure -- read forever, produce nothing --
 * into a shorter contract written from what it already had, which is a draft a
 * human can judge rather than an absence.
 *
 * The turn cap remains, generously, as a real backstop against a loop the soft
 * stop cannot see. Both exhaustion events are still recorded, because the
 * distinction between "stopped early" and "could not do it" is the entire
 * point.
 */
/**
 * **The soft stop is not enough on its own, measured.** The first version of
 * this file blocked reads at 100 calls and told the model to write. Qwen3.6-27B
 * on `registry-iter` then made 130 read calls, 30 of them blocked, emitting
 * "Now I'll write the contract from what I've already read:" *thirty times* --
 * acknowledging the instruction and then calling `read` again instead of
 * finishing its turn. It burned the full 1800s wall clock for 56 bytes, where
 * the old hard cap had failed in 858s.
 *
 * So the real failure is not reading too much. It is that the model will not
 * terminate a turn with prose, and its response to a blocked tool call is
 * another tool call. A block cannot fix that, because a block is exactly what
 * it is ignoring. What a block can do is bound the damage: after
 * `AUTHOR_STUBBORN_BLOCKS` consecutive refusals the run is aborted, so a model
 * that will not stop costs minutes instead of the whole clock, and the record
 * says which of the two happened.
 */
export const AUTHOR_SOFT_TOOLS = 60;
export const AUTHOR_MAX_TOOLS = 200;
export const AUTHOR_MAX_TURNS = 150;
export const AUTHOR_STUBBORN_BLOCKS = 6;

export default function authorCap(pi: ExtensionAPI) {
	let turns = 0;
	let tools = 0;
	let nudged = false;
	let consecutiveBlocks = 0;

	pi.on("turn_start", async (_event, ctx) => {
		turns += 1;
		if (turns <= AUTHOR_MAX_TURNS) return;
		pi.appendEntry("turn_budget_exhausted", { budget: AUTHOR_MAX_TURNS, attempted: turns });
		ctx.abort();
	});

	pi.on("tool_call", async (_event, ctx) => {
		tools += 1;
		if (tools <= AUTHOR_SOFT_TOOLS) {
			consecutiveBlocks = 0;
			return undefined;
		}
		consecutiveBlocks += 1;
		if (consecutiveBlocks >= AUTHOR_STUBBORN_BLOCKS) {
			// It has been told six times in a row and called a tool anyway.
			// Nothing further will change that, and the wall clock is the
			// only other thing standing between here and 30 wasted minutes.
			pi.appendEntry("author_would_not_stop", {
				blocks: consecutiveBlocks,
				tools,
			});
			ctx.abort();
			return { block: true, reason: "Aborting: tool calls continued after repeated refusals." };
		}
		if (tools > AUTHOR_MAX_TOOLS) {
			pi.appendEntry("tool_budget_exhausted", { budget: AUTHOR_MAX_TOOLS, attempted: tools });
			return {
				block: true,
				reason: `The hard tool budget of ${AUTHOR_MAX_TOOLS} calls is exhausted. Stop calling tools and output the contract now, using only what you have already read.`,
			};
		}
		if (!nudged) {
			nudged = true;
			pi.appendEntry("read_budget_reached", { budget: AUTHOR_SOFT_TOOLS, attempted: tools });
		}
		return {
			block: true,
			reason: `You have used ${AUTHOR_SOFT_TOOLS} tool calls, which is enough reading for a contract. Stop exploring and write the contract now from what you have already read. An incomplete contract is useful; no contract is not.`,
		};
	});
}
