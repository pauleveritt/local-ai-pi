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

export interface ContractFinding {
	severity: "error" | "warning";
	field: keyof HandoffContract;
	message: string;
}

export interface ContractReadiness {
	status: "BLOCKED" | "READY_WITH_WARNINGS" | "READY";
	findings: ContractFinding[];
}

const PLACEHOLDER_WORDS = /\b(?:todo|tbd|fixme|placeholder|something|whatever|fill (?:this|me) in)\b/i;

/**
 * A fill-in slot such as `<INSERT NAME>` or `<your-app-name>`.
 *
 * This used to be a bare `<[^>]+>`, which is wrong for the workloads this
 * engine is aimed at. A task that says `templates/base.html` needs
 * `<html lang="en">` is being *more* concrete, not less, and the old pattern
 * rejected it as vague filler. Observed live: a chained Phase 1 handoff --
 * correct, file-by-file, naming every route -- was blocked at admission on
 * exactly that substring, and the run wrote nothing at all.
 *
 * Angle brackets are therefore only suspicious when what they contain looks
 * like a slot rather than markup: a shouted `<LIKE_THIS>`, or bracketed text
 * carrying placeholder vocabulary. Case-sensitive, deliberately -- the
 * all-caps form is the signal, and folding case would put `<html lang>` back.
 */
const PLACEHOLDER_SLOT =
	/<(?:[A-Z][A-Z_ -]{2,}|[^>]*\b(?:insert|your|todo|tbd|fixme|placeholder)\b[^>]*)>/;

function hasPlaceholder(text: string): boolean {
	return PLACEHOLDER_WORDS.test(text) || PLACEHOLDER_SLOT.test(text);
}
/**
 * Parse the deliberately small validation-command language.  A handoff
 * carries a command for the parent to execute, not a shell program: quoted
 * arguments are useful (for example a test selector), while composition and
 * expansion are neither necessary nor safe.
 */
export function parseValidationCommand(command: string): string[] | null {
	const args: string[] = [];
	let token = "";
	let hasToken = false;
	let quote: "'" | '"' | undefined;
	let escaped = false;
	const push = () => {
		if (hasToken) args.push(token);
		token = "";
		hasToken = false;
	};
	for (const character of command.trim()) {
		if (escaped) {
			token += character;
			hasToken = true;
			escaped = false;
			continue;
		}
		if (character === "\\" && quote !== "'") {
			escaped = true;
			continue;
		}
		if (quote) {
			if (character === quote) quote = undefined;
			else {
				token += character;
				hasToken = true;
			}
			continue;
		}
		if (character === "'" || character === '"') {
			quote = character;
			hasToken = true;
		} else if (/\s/.test(character)) {
			push();
		} else if (/[;&|<>`$(){}\r\n]/.test(character)) {
			return null;
		} else {
			token += character;
			hasToken = true;
		}
	}
	if (escaped || quote) return null;
	push();
	return args.length ? args : null;
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
export function inspectContract(contract: HandoffContract, cwd?: string): ContractReadiness {
	const findings: ContractFinding[] = [];
	if (contract.task.trim().length < 40) {
		findings.push({ severity: "warning", field: "task", message: "task may be too terse to implement without guessing" });
	}
	if (hasPlaceholder(contract.task)) {
		findings.push({ severity: "error", field: "task", message: "task contains placeholder or vague filler" });
	}
	if (contract.writableFiles.length === 0) {
		findings.push({ severity: "error", field: "writableFiles", message: "at least one writable file is required" });
	}

	const seen = new Set<string>();
	for (const file of contract.writableFiles) {
		const normalized = normalizeContractPath(file.path);
		if (!normalized) {
			findings.push({ severity: "error", field: "writableFiles", message: `unsafe or non-exact path: ${file.path}` });
			continue;
		}
		if (normalized !== file.path.replaceAll("\\", "/")) {
			findings.push({ severity: "error", field: "writableFiles", message: `path must already be normalized: ${file.path}` });
		}
		if (seen.has(normalized)) {
			findings.push({ severity: "error", field: "writableFiles", message: `duplicate path: ${normalized}` });
		}
		seen.add(normalized);
		if (cwd && !staysInsideWorkspace(cwd, normalized)) {
			findings.push({ severity: "error", field: "writableFiles", message: `${normalized} escapes the workspace through a symlink` });
		}
	}

	for (const candidate of contract.readableFiles) {
		const normalized = normalizeContractPath(candidate);
		if (!normalized) {
			findings.push({ severity: "error", field: "readableFiles", message: `unsafe or non-exact path: ${candidate}` });
			continue;
		}
		if (normalized !== candidate.replaceAll("\\", "/")) {
			findings.push({ severity: "error", field: "readableFiles", message: `path must already be normalized: ${candidate}` });
		}
		if (seen.has(normalized)) {
			findings.push({ severity: "warning", field: "readableFiles", message: `${normalized} is already writable; listing it twice is unnecessary` });
		}
		seen.add(normalized);
		if (cwd && !staysInsideWorkspace(cwd, normalized)) {
			findings.push({ severity: "error", field: "readableFiles", message: `${normalized} escapes the workspace through a symlink` });
		}
		if (cwd && !pathExists(cwd, normalized)) {
			findings.push({ severity: "error", field: "readableFiles", message: `${normalized} does not exist` });
		}
	}

	if (!contract.validation.trim()) {
		findings.push({ severity: "error", field: "validation", message: "validation command is empty" });
	} else if (!parseValidationCommand(contract.validation)) {
		findings.push({ severity: "error", field: "validation", message: "validation must be one executable command with literal arguments, not shell composition" });
	} else if (!/(?:test|pytest|bun|npm|pnpm|ruff|check|lint|type|build)/i.test(contract.validation)) {
		findings.push({ severity: "warning", field: "validation", message: "command does not look like an executable check" });
	}

	if (contract.acceptanceStrings.some((value) => !value)) {
		findings.push({ severity: "error", field: "acceptanceStrings", message: "acceptance strings must not be empty" });
	}
	for (const fact of contract.knownFacts) {
		if (!fact.trim() || hasPlaceholder(fact)) {
			findings.push({ severity: "error", field: "knownFacts", message: "known facts must be concrete" });
			break;
		}
	}
	for (const requirement of contract.preservedBehavior) {
		if (!requirement.trim() || hasPlaceholder(requirement)) {
			findings.push({ severity: "error", field: "preservedBehavior", message: "preservation requirements must be concrete" });
			break;
		}
	}

	const errors = findings.some((finding) => finding.severity === "error");
	return {
		status: errors ? "BLOCKED" : findings.length ? "READY_WITH_WARNINGS" : "READY",
		findings,
	};
}

export function renderContract(contract: HandoffContract): string {
	const bullets = (items: readonly string[], none = "None") =>
		items.length ? items.map((item) => `- ${item}`).join("\n") : none;
	return `## Task\n\n${contract.task.trim()}\n\n` +
		`## Writable Files\n\n${bullets(contract.writableFiles.map((file) => `\`${file.path}\``))}\n\n` +
		`## Readable Files\n\n${bullets(contract.readableFiles.map((file) => `\`${file}\``))}\n\n` +
		`## Acceptance Strings\n\n${bullets(contract.acceptanceStrings.map((value) => JSON.stringify(value)))}\n\n` +
		`## Preserve\n\n${bullets(contract.preservedBehavior)}\n\n` +
		`## Known Facts\n\n${bullets(contract.knownFacts)}\n\n` +
		`## Validation (run by the parent)\n\n${contract.validation.trim()}`;
}

export function repairContract(contract: HandoffContract, failure: string): HandoffContract {
	return {
		...contract,
		knownFacts: [
			...contract.knownFacts,
			`The previous implementation attempt failed independent verification:\n${failure.slice(-8000)}`,
		],
	};
}
