import { createHash } from "node:crypto";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { createLoopBreaker } from "../guards/loop-breaker";
import type { ToolCall } from "../guards/types";
import type { HandoffContract } from "./handoff-contract";
import { ImplementerPolicy } from "./implementer-policy";
import { MutationEngine, MutationRefusal, type FileBaseline } from "./mutation-engine";
import { targetOf } from "./tool-target";

const CONTRACT_ENV = "SATYRN_HANDOFF_CONTRACT";
const BASELINES_ENV = "SATYRN_FILE_BASELINES";
export const MAX_IMPLEMENTER_TURNS = 16;

// `process.argv` for a Pi child invoked as `pi --print ... <prompt>` carries
// the prompt as the last positional argument.
export function promptFromArgv(argv: readonly string[] = process.argv): string {
	return argv[argv.length - 1] ?? "";
}

export function emitPromptTelemetry(
	pi: Pick<ExtensionAPI, "appendEntry">,
	argv: readonly string[] = process.argv,
): void {
	const prompt = promptFromArgv(argv);
	const sha256 = createHash("sha256").update(prompt, "utf8").digest("hex");
	pi.appendEntry("satyrn-child-prompt", { sha256, length: prompt.length });
}

function isContract(value: unknown): value is HandoffContract {
	if (!value || typeof value !== "object") return false;
	const record = value as Record<string, unknown>;
	return typeof record.task === "string" &&
		Array.isArray(record.writableFiles) && record.writableFiles.every((file) =>
			file && typeof file === "object" && typeof (file as Record<string, unknown>).path === "string",
		) &&
		Array.isArray(record.readableFiles) && record.readableFiles.every((file) => typeof file === "string") &&
		Array.isArray(record.acceptanceStrings) && record.acceptanceStrings.every((value) => typeof value === "string") &&
		Array.isArray(record.preservedBehavior) && record.preservedBehavior.every((value) => typeof value === "string") &&
		Array.isArray(record.knownFacts) && record.knownFacts.every((value) => typeof value === "string") &&
		typeof record.validation === "string" &&
		(record.removableSymbols === undefined ||
			(Array.isArray(record.removableSymbols) &&
				record.removableSymbols.every((value) => typeof value === "string")));
}

function loadContract(): HandoffContract | null {
	const raw = process.env[CONTRACT_ENV];
	if (!raw) return null;
	try {
		const parsed = JSON.parse(raw) as unknown;
		return isContract(parsed) ? parsed : null;
	} catch {
		return null;
	}
}

function loadBaselines(): FileBaseline[] | null {
	const raw = process.env[BASELINES_ENV];
	if (!raw) return null;
	try {
		const baselines = JSON.parse(raw) as unknown;
		return Array.isArray(baselines) ? baselines as FileBaseline[] : null;
	} catch {
		return null;
	}
}

function promptFor(contract: HandoffContract | null): string {
	if (!contract) {
		return "The implementer handoff contract is missing or invalid. Do not call tools; report this configuration failure.";
	}
	return `
You are the bounded writer in a two-agent development workflow. Implement the
typed handoff below; do not redesign it or delegate.

- You have read and write only. The parent owns validation.
- Read only the declared readable and writable files.
- Read a writable file when its current content is useful, then call write
  with complete desired content. The extension carries the parent-captured
  SHA-256 baseline and refuses intervening drift for you.
- If a declared writable file is absent, do not call read on it; submit its
  complete initial content with write.
- Code, not you, chooses create versus reconcile and rejects stale revisions
  or destructive public-symbol removal.
- Preserve the listed behavior and include every acceptance string exactly.
- Stop after the requested edits and report changed files or a concrete blocker.
- Do not claim that validation passed: you cannot run it, and the parent will.

`;
}

const WriteParameters = Type.Object({
	path: Type.String({ description: "Exact writable workspace-relative path" }),
	content: Type.String({ description: "Complete desired UTF-8 file content within the proposal limit" }),
});

export default function implementer(pi: ExtensionAPI) {
	// Emitted from `agent_start`, never at load time.
	//
	// Calling it directly in this function body -- which is what the first
	// version did -- makes the whole extension fail to load on Pi 0.84.1:
	// "Extension runtime not initialized. Action methods cannot be called
	// during extension loading." Every engine run then dies at its child step
	// with `implement` returning isError, writing nothing at all, and the arm
	// reads as a fast rejection rather than as a broken harness.
	//
	// No unit test caught it because the tests call `emitPromptTelemetry`
	// directly with a stub, which never exercises real extension loading. It
	// took a live run to surface. `.pi/extensions/hello-world.ts` already
	// documents the same constraint and the same resolution.
	//
	// `agent_start` can fire more than once -- Pi retries after some agent
	// errors -- so this emits at most once per child, keeping one prompt
	// hash per run rather than one per retry.
	let promptTelemetryEmitted = false;
	pi.on("agent_start", async () => {
		if (promptTelemetryEmitted) return;
		promptTelemetryEmitted = true;
		emitPromptTelemetry(pi);
	});

	const contract = loadContract();
	const baselines = loadBaselines();
	const policy = contract && baselines ? new ImplementerPolicy(contract, process.cwd()) : null;
	const mutations = baselines
		? new MutationEngine(process.cwd(), baselines, contract?.removableSymbols ?? [])
		: null;
	const revisions = new Map((baselines ?? []).map((baseline) => [
		baseline.path,
		baseline.sha256 ?? "<absent>",
	]));
	const loopBreaker = createLoopBreaker();
	const failedWriteCalls = new Set<string>();

	pi.on("before_agent_start", async (event) => ({
		systemPrompt: `${event.systemPrompt}\n${promptFor(contract)}`,
	}));

	let turns = 0;
	pi.on("turn_start", async (_event, ctx) => {
		turns += 1;
		if (turns <= MAX_IMPLEMENTER_TURNS) return;
		pi.appendEntry("turn_budget_exhausted", { budget: MAX_IMPLEMENTER_TURNS, attempted: turns });
		ctx.abort();
	});

	pi.on("tool_call", async (event) => {
		try {
			if (!policy) {
				return { block: true, reason: "No valid handoff contract was supplied to the implementer extension." };
			}
			const policyBlock = policy.inspect(event.toolName, event.input);
			if (policyBlock) {
				pi.appendEntry(policyBlock.kind, policyBlock.data);
				return { block: true, reason: policyBlock.reason };
			}

			const call: ToolCall = {
				toolName: event.toolName,
				input: event.input,
				target: targetOf(event.input),
			};
			const repeated = loopBreaker.inspect(call);
			if (!repeated) return undefined;
			pi.appendEntry(repeated.entry.kind, repeated.entry.data);
			return { block: true, reason: repeated.reason };
		} catch {
			pi.appendEntry("policy_error", { tool: event.toolName });
			return { block: true, reason: "The implementer policy could not safely inspect this tool call." };
		}
	});

	pi.on("tool_result", async (event) => {
		if (event.toolName === "write") return failedWriteCalls.delete(event.toolCallId) ? { isError: true } : undefined;
		if (event.toolName !== "read" || !policy || !mutations) return undefined;
		const target = targetOf(event.input);
		if (!target) return undefined;
		try {
			const receipt = mutations.readReceipt(target);
			revisions.set(receipt.path, receipt.sha256);
			return {
				// The model receives file content verbatim.  A prose receipt beside
				// source is easy to copy into its next complete-file proposal, which
				// corrupts that source.  Keep the revision receipt in structured
				// details; the extension already owns the revision map.
				content: event.content,
				details: { ...(event.details as Record<string, unknown> ?? {}), satyrnRevision: receipt },
			};
		} catch (error) {
			const text = error instanceof Error ? error.message : String(error);
			return { content: event.content, details: { ...(event.details as Record<string, unknown> ?? {}), satyrnReceiptError: text } };
		}
	});

	pi.registerTool({
		// Pi deliberately permits an extension to replace a built-in by name.
		// Keep the model-facing write contract it already knows, but do not
		// delegate to Pi's filesystem writer: all mutations pass through the
		// revision-checked engine below.
		name: "write",
		label: "Propose deterministic file revision",
		description: "Submit complete desired content for one declared file after reading it. The engine, not the model, chooses create or reconcile and checks the read revision.",
		parameters: WriteParameters,
		async execute(_id, params) {
			if (!mutations) {
				failedWriteCalls.add(_id);
				return { content: [{ type: "text" as const, text: "No valid mutation baseline was supplied." }], details: undefined };
			}
			try {
				const receipt = mutations.readReceipt(params.path);
				const expectedSha256 = revisions.get(receipt.path);
				if (!expectedSha256) {
					failedWriteCalls.add(_id);
					return { content: [{ type: "text" as const, text: `${receipt.path} is outside the declared mutation baseline.` }], details: undefined };
				}
				const result = mutations.propose(params.path, expectedSha256, params.content);
				revisions.set(result.path, result.sha256);
				return {
					content: [{ type: "text" as const, text: `${result.operation} applied to ${result.path}; sha256=${result.sha256}; changed lines=${result.changedLines}\n${result.patch}` }],
					details: result,
				};
			} catch (error) {
				const refusal = error instanceof MutationRefusal ? error : undefined;
				failedWriteCalls.add(_id);
				return {
					content: [{ type: "text" as const, text: refusal?.message ?? (error instanceof Error ? error.message : String(error)) }],
					details: undefined,
				};
			}
		},
	});
}
