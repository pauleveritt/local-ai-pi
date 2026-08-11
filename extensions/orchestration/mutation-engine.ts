import { createHash, randomUUID } from "node:crypto";
import * as fs from "node:fs";
import * as path from "node:path";
import { symbolsIn, type FoundSymbol } from "../guards/preserve-symbols";
import { normalizeContractPath } from "./handoff-contract";

export const ABSENT_REVISION = "<absent>";
export const MAX_PROPOSAL_BYTES = 32 * 1024;

export interface FileBaseline {
	path: string;
	state: "absent" | "present" | "engine-created";
	sha256?: string;
	mode?: number;
	lineEnding?: "LF" | "CRLF";
}

export interface MutationResult {
	operation: "create" | "reconcile";
	path: string;
	sha256: string;
	changedLines: number;
	patch: string;
}

export class MutationRefusal extends Error {
	constructor(message: string, readonly details: Record<string, unknown>) {
		super(message);
	}
}

export function sha256(content: string | Buffer): string {
	return createHash("sha256").update(content).digest("hex");
}

function lineEnding(content: string): "LF" | "CRLF" {
	return content.includes("\r\n") ? "CRLF" : "LF";
}

function normalizedNewlines(content: string, ending: "LF" | "CRLF"): string {
	const lf = content.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
	return ending === "CRLF" ? lf.replace(/\n/g, "\r\n") : lf;
}

function lostSymbols(before: string, after: string): FoundSymbol[] {
	const remaining = new Set(symbolsIn(after).map((symbol) => `${symbol.kind}:${symbol.name}`));
	return symbolsIn(before).filter((symbol) => !remaining.has(`${symbol.kind}:${symbol.name}`));
}

export function symbolKey(symbol: FoundSymbol): string {
	return `${symbol.kind}:${symbol.name}`;
}

/**
 * Does a declaration cover this symbol?
 *
 * A contract declares bare names (`SiteMenu`, `/about`) rather than
 * `kind:name` keys, because the controller is describing intent, not the
 * guard's internal taxonomy. Matching on either form keeps a precise
 * declaration possible without requiring it.
 */
function declared(removable: ReadonlySet<string>, symbol: FoundSymbol): boolean {
	return removable.has(symbol.name) || removable.has(symbolKey(symbol));
}

function changedLines(before: string, after: string): number {
	const left = before.replace(/\r\n/g, "\n").split("\n");
	const right = after.replace(/\r\n/g, "\n").split("\n");
	const max = Math.max(left.length, right.length);
	let changed = 0;
	for (let index = 0; index < max; index += 1) if (left[index] !== right[index]) changed += 1;
	return changed;
}

/** A compact diagnostic patch; Pi's interactive renderer can show the full diff separately. */
function patch(pathname: string, before: string, after: string): string {
	return `--- a/${pathname}\n+++ b/${pathname}\n@@ changed lines: ${changedLines(before, after)} @@`;
}

function safePath(cwd: string, candidate: string): { relative: string; absolute: string } {
	const relative = normalizeContractPath(candidate);
	if (!relative) throw new MutationRefusal("Mutation path is not a safe workspace-relative file.", { path: candidate });
	const root = fs.realpathSync(cwd);
	const absolute = path.resolve(cwd, relative);
	let existing = absolute;
	while (!fs.existsSync(existing)) {
		const parent = path.dirname(existing);
		if (parent === existing) throw new MutationRefusal("Mutation path has no existing workspace parent.", { path: relative });
		existing = parent;
	}
	const canonical = fs.realpathSync(existing);
	if (canonical !== root && !canonical.startsWith(`${root}${path.sep}`)) {
		throw new MutationRefusal("Mutation path escapes the workspace through a symlink.", { path: relative });
	}
	return { relative, absolute };
}

export function captureFileBaselines(cwd: string, paths: readonly string[]): FileBaseline[] {
	return paths.map((candidate) => {
		const { relative, absolute } = safePath(cwd, candidate);
		if (!fs.existsSync(absolute)) return { path: relative, state: "absent" };
		const stat = fs.statSync(absolute);
		if (!stat.isFile()) throw new MutationRefusal("Declared writable path is not a regular file.", { path: relative });
		const content = fs.readFileSync(absolute, "utf8");
		return { path: relative, state: "present", sha256: sha256(content), mode: stat.mode & 0o777, lineEnding: lineEnding(content) };
	});
}

export function repairFileBaselines(cwd: string, baselines: readonly FileBaseline[]): FileBaseline[] {
	return baselines.map((baseline) => {
		const { absolute } = safePath(cwd, baseline.path);
		if (baseline.state !== "absent" || !fs.existsSync(absolute)) return baseline;
		const stat = fs.statSync(absolute);
		const content = fs.readFileSync(absolute, "utf8");
		return {
			path: baseline.path,
			state: "engine-created",
			sha256: sha256(content),
			mode: stat.mode & 0o777,
			lineEnding: lineEnding(content),
		};
	});
}

export class MutationEngine {
	readonly #baselines: Map<string, FileBaseline>;
	readonly #created = new Set<string>();
	/**
	 * Symbols this invocation has *added* anywhere, so a symbol leaving one
	 * file can be recognised as having arrived in another.
	 *
	 * Refactoring was impossible before this existed. `lostSymbols` compared
	 * one file against itself, so "move the two views into views.py" was
	 * refused on `app.py` even though the functions reappeared next door --
	 * the check could not see the other file. Extraction survived only because
	 * the source file kept its own `def`; move and rename could not.
	 *
	 * The ordering consequence is deliberate and stated in the refusal:
	 * write the destination before emptying the source. The alternative --
	 * deferring the check to the end of the invocation -- would mean the
	 * destructive write has already happened by the time anything objects,
	 * which is the guarantee this engine exists to provide.
	 */
	readonly #gained = new Set<string>();
	readonly #removable: ReadonlySet<string>;

	constructor(
		private readonly cwd: string,
		baselines: readonly FileBaseline[],
		/**
		 * Symbols the typed handoff declares may disappear outright -- a
		 * rename has no compensating file, so it can only be sanctioned by
		 * being declared. Undeclared, uncompensated loss is still refused,
		 * which is the whole of the original guarantee.
		 */
		removableSymbols: readonly string[] = [],
	) {
		this.#baselines = new Map(baselines.map((baseline) => [baseline.path, baseline]));
		this.#removable = new Set(removableSymbols);
	}

	/** Put every symbol in a written revision on the invocation's ledger. */
	#recordGains(content: string): void {
		for (const symbol of symbolsIn(content)) this.#gained.add(symbolKey(symbol));
	}

	readReceipt(candidate: string): { path: string; sha256: string } {
		const { relative, absolute } = safePath(this.cwd, candidate);
		if (!this.#baselines.has(relative)) throw new MutationRefusal("Read path is outside the writable mutation scope.", { path: relative });
		if (!fs.existsSync(absolute)) return { path: relative, sha256: ABSENT_REVISION };
		return { path: relative, sha256: sha256(fs.readFileSync(absolute)) };
	}

	propose(candidate: string, expectedSha256: string, desiredContent: string): MutationResult {
		const { relative, absolute } = safePath(this.cwd, candidate);
		const baseline = this.#baselines.get(relative);
		if (!baseline) throw new MutationRefusal("Mutation path is outside the declared writable scope.", { path: relative });
		if (Buffer.byteLength(desiredContent, "utf8") > MAX_PROPOSAL_BYTES) {
			throw new MutationRefusal("Desired content exceeds the bounded proposal limit.", {
				path: relative, limitBytes: MAX_PROPOSAL_BYTES, actualBytes: Buffer.byteLength(desiredContent, "utf8"),
			});
		}

		const exists = fs.existsSync(absolute);
		if (!exists) {
			if (baseline.state !== "absent" || expectedSha256 !== ABSENT_REVISION) {
				throw new MutationRefusal("Expected an existing revision, but the file is absent.", { path: relative, expectedSha256, state: baseline.state });
			}
			fs.mkdirSync(path.dirname(absolute), { recursive: true });
			this.#atomicWrite(absolute, desiredContent, undefined);
			this.#created.add(relative);
			// A created file is the usual destination of a move, so its symbols
			// must be on the ledger before the source is emptied.
			this.#recordGains(desiredContent);
			return { operation: "create", path: relative, sha256: sha256(desiredContent), changedLines: desiredContent.split("\n").length, patch: patch(relative, "", desiredContent) };
		}

		const stat = fs.statSync(absolute);
		if (!stat.isFile()) throw new MutationRefusal("Mutation target is not a regular file.", { path: relative });
		const before = fs.readFileSync(absolute, "utf8");
		const actualSha256 = sha256(before);
		if (expectedSha256 !== actualSha256) {
			throw new MutationRefusal("File changed after the revision that was read; read it again before proposing a mutation.", {
				path: relative, expectedSha256, actualSha256,
			});
		}
		if (baseline.state === "absent" && !this.#created.has(relative)) {
			throw new MutationRefusal("A file declared absent appeared outside this engine invocation.", { path: relative });
		}
		const next = normalizedNewlines(desiredContent, baseline.lineEnding ?? lineEnding(before));
		const removed = lostSymbols(before, next).filter(
			(symbol) => !this.#gained.has(symbolKey(symbol)) && !declared(this.#removable, symbol),
		);
		if (removed.length) {
			const named = removed.map(symbolKey);
			throw new MutationRefusal(
				`Proposal removes ${named.join(", ")} from ${relative} without replacing them. ` +
					"If you are moving them, write the destination file first, so this engine can see they survive. " +
					"If you mean to remove them outright, the handoff must declare them in removableSymbols.",
				{ path: relative, removed: named },
			);
		}
		this.#recordGains(next);
		this.#atomicWrite(absolute, next, baseline.mode ?? (stat.mode & 0o777));
		return { operation: "reconcile", path: relative, sha256: sha256(next), changedLines: changedLines(before, next), patch: patch(relative, before, next) };
	}

	#atomicWrite(absolute: string, content: string, mode: number | undefined) {
		const temporary = path.join(path.dirname(absolute), `.${path.basename(absolute)}.satyrn-${randomUUID()}.tmp`);
		try {
			fs.writeFileSync(temporary, content, "utf8");
			if (mode !== undefined) fs.chmodSync(temporary, mode);
			fs.renameSync(temporary, absolute);
		} finally {
			try { fs.unlinkSync(temporary); } catch {}
		}
	}
}
