import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

/**
 * Refuse a `write` cleanly when its content can't fit, instead of letting
 * generation truncate mid-file.
 *
 * The real implementer child (`extensions/orchestration/mutation-engine.ts`
 * on `phase6-orchestrator-spike`) checks this before accepting a proposal:
 * `MAX_PROPOSAL_BYTES = 32 * 1024`, thrown as `MutationRefusal("Desired
 * content exceeds the bounded proposal limit.")`. This envelope had no such
 * check. Two attempts under it (`autowire__r3`, `stringified-annotations__r1`)
 * located the right ~30-35KB file, tried to rewrite it whole, and got cut
 * off mid-generation at exactly `output: 8192` -- the model's raw token
 * cap, not a designed boundary, and the failure was only legible by reading
 * raw usage counts out of the transcript.
 *
 * Same limit, same shape of refusal, checked before the call completes
 * rather than reconstructed after the fact.
 */
export const MAX_PROPOSAL_BYTES = 32 * 1024;

export default function proposalLimit(pi: ExtensionAPI) {
	pi.on("tool_call", async (event) => {
		if (event.toolName !== "write") return undefined;
		const input = event.input as Record<string, unknown> | undefined;
		const content = typeof input?.content === "string" ? input.content : "";
		const bytes = Buffer.byteLength(content, "utf8");
		if (bytes <= MAX_PROPOSAL_BYTES) return undefined;
		pi.appendEntry("proposal_limit_exceeded", {
			path: input?.path,
			limitBytes: MAX_PROPOSAL_BYTES,
			actualBytes: bytes,
		});
		return {
			block: true,
			reason:
				`Desired content exceeds the bounded proposal limit ` +
				`(${bytes} bytes > ${MAX_PROPOSAL_BYTES}). A whole-file write this ` +
				`large cannot be expressed in one response. Stop and report this ` +
				`as a blocker rather than attempting a truncated rewrite.`,
		};
	});
}
