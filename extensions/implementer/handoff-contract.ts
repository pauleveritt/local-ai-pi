import * as fs from "node:fs";
import * as path from "node:path";

export interface WritableFile {
	path: string;
}

export interface HandoffContract {
	task: string;
	writableFiles: WritableFile[];
	readableFiles: string[];
	acceptanceStrings: string[];
	preservedBehavior: string[];
	knownFacts: string[];
	validation: string;
	/**
	 * Public symbols the writer is permitted to remove outright.
	 *
	 * A move needs no declaration -- the mutation engine sees the symbol
	 * arrive in its destination. A **rename** has no compensating file, so
	 * declaring it is the only way to distinguish it from the destructive
	 * edit this engine was built to refuse. Optional, and empty for every
	 * additive task.
	 */
	removableSymbols?: string[];
}

export function normalizeContractPath(candidate: string): string | null {
	if (!candidate || path.isAbsolute(candidate) || candidate.includes("\0")) return null;
	const normalized = path.posix.normalize(candidate.replaceAll("\\", "/"));
	if (normalized === "." || normalized === ".." || normalized.startsWith("../")) return null;
	if (normalized.includes("*") || normalized.endsWith("/")) return null;
	return normalized;
}

function staysInsideWorkspace(cwd: string, relative: string): boolean {
	const root = fs.realpathSync(cwd);
	let existing = path.resolve(cwd, relative);
	while (!fs.existsSync(existing)) {
		const parent = path.dirname(existing);
		if (parent === existing) return false;
		existing = parent;
	}
	try {
		const real = fs.realpathSync(existing);
		return real === root || real.startsWith(`${root}${path.sep}`);
	} catch {
		return false;
	}
}

function pathExists(cwd: string, relative: string): boolean {
	try {
		return fs.statSync(path.resolve(cwd, relative)).isFile();
	} catch {
		return false;
	}
}

/** Structural and workspace-aware checks; no model call is involved. */
