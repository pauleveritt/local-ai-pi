import type { Decision, Guard, ToolCall } from "./types";

/**
 * Guard #1 — refuse a tool call the model has already made, unchanged,
 * several times in a row.
 *
 * Why this exists, with a number: one recorded run of this project executed
 * 261 tool calls, of which **245 were the identical command `ls -R`**, each
 * returning "(no output)" because the workspace was genuinely empty. It
 * never concluded that it should create files. Pi ships no turn cap, no loop
 * detection and no tool-call budget, and upstream has declined to add one,
 * directing users to extensions (issues #1898, #5248, #6158 -- the last
 * reporting this exact scenario on a small quantized local model).
 *
 * **It trips on repeats regardless of whether the call succeeded.** Every one
 * of those 245 calls succeeded; a breaker that only counts *failing* repeats
 * would never have fired. That is not a subtle design choice here:
 * `tool_call` fires *before* execution, so success is not knowable at this
 * point.
 *
 * **Moved unchanged in phase 6 cycle 1.** The policy, the window, the
 * threshold, the key and the refusal text are byte-identical to the version
 * proven in phase 5 cycle 6. Only the surrounding shape changed: the
 * decision is now a pure function so replay can drive it directly.
 */

/** Calls remembered. Older ones fall out and stop counting. */
export const WINDOW = 20;

/** Identical calls within the window before the next one is refused. */
export const THRESHOLD = 5;

/**
 * Stable key for a call: same tool, same arguments, regardless of key order.
 * `JSON.stringify` alone is order-sensitive, so two identical calls whose
 * arguments serialised differently would not be recognised as repeats.
 */
export function callKey(toolName: string, input: unknown): string {
	const stable = (value: unknown): unknown => {
		if (Array.isArray(value)) return value.map(stable);
		if (value && typeof value === "object") {
			return Object.fromEntries(
				Object.entries(value as Record<string, unknown>)
					.sort(([a], [b]) => a.localeCompare(b))
					.map(([k, v]) => [k, stable(v)]),
			);
		}
		return value;
	};
	return `${toolName}\u0000${JSON.stringify(stable(input))}`;
}

export function createLoopBreaker(
	window: number = WINDOW,
	threshold: number = THRESHOLD,
): Guard {
	// Admitted calls only. A blocked call does not enter the window, so a
	// model that keeps retrying stays blocked rather than sliding the
	// repeats out of view and being let through again.
	const recent: string[] = [];
	const blocked = new Map<string, number>();

	return {
		name: "loop-breaker",
		inspect(call: ToolCall): Decision {
			const key = callKey(call.toolName, call.input);
			const seen = recent.filter((entry) => entry === key).length;

			if (seen >= threshold) {
				const times = (blocked.get(key) ?? 0) + 1;
				blocked.set(key, times);
				return {
					block: true,
					// The reason steers rather than merely refusing. A bare
					// "no" invites a sixth attempt; naming the repetition and
					// stating that the answer will not change gives the model
					// somewhere to go.
					reason:
						`You have already run this exact ${call.toolName} call ${seen} times ` +
						`in a row and the result will not change. Do not repeat it. ` +
						`Use what you already know and take the next concrete action — ` +
						`if you were looking for files and found none, create them.`,
					entry: {
						kind: "loop_broken",
						data: { tool: call.toolName, repeats: seen, blockedSoFar: times },
					},
				};
			}

			recent.push(key);
			if (recent.length > window) recent.shift();
			return undefined;
		},
	};
}
