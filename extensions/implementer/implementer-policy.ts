import * as fs from "node:fs";
import * as path from "node:path";
import type { HandoffContract } from "./handoff-contract";
import { normalizeContractPath } from "./handoff-contract";
import { targetOf } from "./tool-target";

export interface PolicyBlock {
	reason: string;
	kind: "scope_blocked" | "tool_budget_exhausted" | "revision_blocked";
	data: Record<string, unknown>;
}

function nearestExisting(candidate: string): string {
	let current = candidate;
	while (!fs.existsSync(current)) {
		const parent = path.dirname(current);
		if (parent === current) return current;
		current = parent;
	}
	return current;
}

export class ImplementerPolicy {
	readonly #cwd: string;
	readonly #root: string;
	readonly #writable = new Set<string>();
	readonly #readable: Set<string>;
	readonly #maxTools: number;
	#tools = 0;

	constructor(contract: HandoffContract, cwd: string, maxTools = 30) {
		this.#cwd = path.resolve(cwd);
		this.#root = fs.realpathSync(this.#cwd);
		this.#maxTools = maxTools;
		for (const file of contract.writableFiles) {
			const normalized = normalizeContractPath(file.path);
			if (!normalized) continue;
			this.#writable.add(normalized);
		}
		this.#readable = new Set(
			contract.readableFiles.map(normalizeContractPath).filter((value): value is string => value !== null),
		);
	}

	#canonical(candidate: string): string | null {
		const normalized = normalizeContractPath(candidate);
		if (!normalized) return null;
		const absolute = path.resolve(this.#cwd, normalized);
		const existing = nearestExisting(absolute);
		let real: string;
		try {
			real = fs.realpathSync(existing);
		} catch {
			return null;
		}
		if (real !== this.#root && !real.startsWith(`${this.#root}${path.sep}`)) return null;
		return normalized;
	}

	inspect(toolName: string, input: unknown): PolicyBlock | undefined {
		this.#tools += 1;
		if (this.#tools > this.#maxTools) {
			return {
				kind: "tool_budget_exhausted",
				reason: `The implementer tool budget of ${this.#maxTools} calls is exhausted. Stop and report what remains.`,
				data: { budget: this.#maxTools, attempted: this.#tools },
			};
		}

		if (!new Set(["read", "write", "edit"]).has(toolName)) {
			return {
				kind: "scope_blocked",
				reason: `The implementer may use only read, write and edit; ${toolName} is not available for this handoff.`,
				data: { tool: toolName },
			};
		}
		const rawTarget = targetOf(input);
		const target = rawTarget ? this.#canonical(rawTarget) : null;
		if (!target) {
			return {
				kind: "scope_blocked",
				reason: "This tool call has no safe, workspace-relative exact path from the handoff contract.",
				data: { tool: toolName, target: rawTarget },
			};
		}

		const writable = this.#writable.has(target);
		if (toolName === "read") {
			if (!writable && !this.#readable.has(target)) {
				return {
					kind: "scope_blocked",
					reason: `Reading ${target} is outside the handoff contract. Use only the exact readable or writable paths supplied by the orchestrator.`,
					data: { tool: toolName, target },
				};
			}
			const record = input as Record<string, unknown>;
			if (record.offset !== undefined || record.limit !== undefined) {
				return {
					kind: "revision_blocked",
				reason: `Read ${target} without offset or limit before writing, so its revision receipt covers the complete file.`,
					data: { tool: toolName, target },
				};
			}
			return undefined;
		}

		if (!writable) {
			return {
				kind: "scope_blocked",
				reason: `Writing ${target} is outside the handoff contract.`,
				data: { tool: toolName, target },
			};
		}
		return undefined;
	}
}
