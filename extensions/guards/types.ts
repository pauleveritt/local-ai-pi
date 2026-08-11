/**
 * The shape every guard has, and the reason it is not Pi's shape.
 *
 * A guard is a **pure decision function over a tool call**. It knows nothing
 * about Pi. `index.ts` adapts it to `pi.on("tool_call")`; `replay.ts` drives
 * the same function over recorded calls.
 *
 * That split exists because of a specific flaw Phase 5 wrote down and could
 * not fix. Cycle 6's replay reimplemented the loop-breaker policy in Python,
 * and its docstring says: "the extension implements the policy in TypeScript
 * and this reimplements it in Python. They can diverge, and no test here
 * would notice." Keeping the decision pure means replay drives the shipped
 * function itself, so there is no second implementation to diverge from.
 *
 * **What this deliberately does not cover.** The adapter in `index.ts` --
 * translating a decision into `{block, reason}` and an `appendEntry` -- is
 * not exercised by replay. That boundary is real and is proven the way cycle
 * 6 proved it: a live smoke with a threshold-0 copy that blocks every call.
 */

/** One tool call, as both Pi and a recorded transcript can describe it. */
export interface ToolCall {
	toolName: string;
	/** Arguments, whatever shape the tool takes. */
	input: unknown;
	/**
	 * The path this call acts on, when it has one. Supplied by the caller
	 * rather than derived here, because the derivation differs between a
	 * live Pi event and a recorded transcript, and a guard should not care.
	 */
	target?: string | null;
}

/** What a guard decides. `undefined` means "no opinion, let it through". */
export interface Block {
	block: true;
	/** Shown to the model as an error tool result. Steers; does not merely refuse. */
	reason: string;
	/** Appended to telemetry as `entry_appended`, so a block is observable. */
	entry: { kind: string; data: Record<string, unknown> };
}

export type Decision = Block | undefined;

export interface Guard {
	readonly name: string;
	/** Called once per tool call, in order. Guards are stateful across a run. */
	inspect(call: ToolCall): Decision;
}
