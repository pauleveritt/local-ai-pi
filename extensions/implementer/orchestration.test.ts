import { afterAll, describe, expect, test } from "bun:test";
import { createHash } from "node:crypto";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { normalizeContractPath, type HandoffContract } from "./handoff-contract";
import implementer, { emitPromptTelemetry, promptFromArgv } from "./implementer";
import { ImplementerPolicy } from "./implementer-policy";
import { targetOf } from "./tool-target";
import {
	ABSENT_REVISION,
	captureFileBaselines,
	MAX_PROPOSAL_BYTES,
	MutationEngine,
	MutationRefusal,
	sha256,
} from "./mutation-engine";

// Ported from `phase6-orchestrator-spike`'s `orchestration.test.ts`. Trimmed
// to the describes that cover the files this branch actually ports --
// handoff-contract, implementer-policy, mutation-engine, tool-target, and
// implementer's pure helpers. The controller/repair/orchestrator/
// source-contract/verification describes stayed on phase6; those modules
// were not ported (see the 2026-08-11 re-plan).

const CONTRACT: HandoffContract = {
	task: "Implement deterministic contract checks for the orchestration extension.",
	writableFiles: [{ path: "src/feature.ts" }],
	readableFiles: ["src/types.ts"],
	acceptanceStrings: ["READY"],
	preservedBehavior: ["Existing public exports remain available."],
	knownFacts: ["The project runs TypeScript with Bun."],
	validation: "bun test",
};


describe("child tool telemetry", () => {
	test("captures only path-shaped targets from Pi event arguments", () => {
		expect(targetOf({ path: "src/feature.ts", content: "do not retain this" })).toBe("src/feature.ts");
		expect(targetOf({ filePath: "src/legacy.ts" })).toBe("src/legacy.ts");
		expect(targetOf({ content: "no target" })).toBeNull();
		expect(targetOf(null)).toBeNull();
	});

	test("promptFromArgv reads the last positional argument", () => {
		expect(promptFromArgv(["node", "pi", "--print", "fixture prompt text"])).toBe("fixture prompt text");
		expect(promptFromArgv([])).toBe("");
	});

	test("emitPromptTelemetry appends a satyrn-child-prompt entry hashing the prompt", () => {
		const calls: Array<[string, unknown]> = [];
		const fakePi = { appendEntry: (kind: string, data: unknown) => { calls.push([kind, data]); } };
		const argv = ["node", "pi", "--print", "fixture prompt text"];
		emitPromptTelemetry(fakePi, argv);
		expect(calls).toHaveLength(1);
		expect(calls[0][0]).toBe("satyrn-child-prompt");
		const details = calls[0][1] as { sha256: string; length: number };
		expect(details.sha256).toHaveLength(64); // hex sha256
		expect(details.length).toBe("fixture prompt text".length);
	});

	test("emitPromptTelemetry's hash matches hashing the prompt directly, and does not mutate argv", () => {
		const argv = ["node", "pi", "--print", "fixture prompt text"];
		const argvBefore = [...argv];
		const calls: Array<[string, unknown]> = [];
		const fakePi = { appendEntry: (kind: string, data: unknown) => { calls.push([kind, data]); } };
		emitPromptTelemetry(fakePi, argv);
		const directHash = createHash("sha256").update("fixture prompt text", "utf8").digest("hex");
		const details = calls[0][1] as { sha256: string };
		expect(details.sha256).toBe(directHash);
		// The instrument must not alter what the model sees: confirm argv itself
		// -- the thing the model's own invocation carries -- is untouched by
		// reading it.
		expect(argv).toEqual(argvBefore);
	});
});

describe("implementer: the mutation engine is the sole gate on edit", () => {
	// The contract-blind preserve-symbols guard used to run ahead of
	// MutationEngine.proposeEdits() in the tool_call handler and had no way
	// to see HandoffContract.removableSymbols, so it refused a
	// contract-authorized rename before the engine -- the only place that
	// check is actually contract-aware -- ever ran (2026-08-11 distribution
	// review). Removed rather than made contract-aware: the guard's own
	// docstring states it must never consult the contract, and the engine
	// already does everything the guard did plus the cases it couldn't see
	// (removableSymbols, cross-file moves).
	const source = fs.readFileSync(new URL("./implementer.ts", import.meta.url), "utf8");

	test("no pre-edit guard is imported or wired ahead of the engine", () => {
		expect(source).not.toContain("preserve-symbols");
		expect(source).not.toContain("createPreserveSymbols");
	});

	test("a contract-authorized rename survives through the real tool_call and registered edit path", async () => {
		const originalCwd = process.cwd();
		const cwd = fs.mkdtempSync(path.join(os.tmpdir(), "satyrn-implementer-"));
		fs.mkdirSync(path.join(cwd, "src"));
		// Python `def` syntax deliberately -- preserve-symbols.ts's SYMBOL_PATTERNS
		// only recognize def/class/route decorators (this cohort's Flask/svcs
		// workloads), so a TS-syntax fixture would never exercise the guard's
		// detection at all and this test would pass for the wrong reason.
		const before = "def old_name():\n    return 1\n";
		fs.writeFileSync(path.join(cwd, "src/feature.py"), before);

		const contract: HandoffContract = {
			...CONTRACT,
			writableFiles: [{ path: "src/feature.py" }],
			removableSymbols: ["old_name"],
		};
		process.env.SATYRN_HANDOFF_CONTRACT = JSON.stringify(contract);
		process.env.SATYRN_FILE_BASELINES = JSON.stringify([
			{ path: "src/feature.py", state: "present", sha256: sha256(before), mode: 0o644, lineEnding: "LF" },
		]);
		process.chdir(cwd);

		try {
			const handlers: Record<string, ((event: unknown) => Promise<unknown>)[]> = {};
			const tools: Record<string, { execute: (id: string, params: unknown) => Promise<{ details?: { operation?: string } }> }> = {};
			const fakePi = {
				on(event: string, handler: (event: unknown) => Promise<unknown>) {
					(handlers[event] ??= []).push(handler);
				},
				registerTool(tool: { name: string; execute: (id: string, params: unknown) => Promise<unknown> }) {
					tools[tool.name] = tool as (typeof tools)[string];
				},
				appendEntry() {},
			};

			implementer(fakePi as unknown as Parameters<typeof implementer>[0]);

			const editInput = {
				path: "src/feature.py",
				edits: [{ oldText: before, newText: "def new_name():\n    return 1\n" }],
			};
			const decision = await handlers["tool_call"][0]({ toolName: "edit", input: editInput });
			// No pre-edit guard left to refuse this ahead of the engine.
			expect(decision).toBeUndefined();

			const result = await tools.edit.execute("call-1", editInput);
			expect(result.details?.operation).toBe("reconcile");
			expect(fs.readFileSync(path.join(cwd, "src/feature.py"), "utf8")).toContain("new_name");
		} finally {
			process.chdir(originalCwd);
			delete process.env.SATYRN_HANDOFF_CONTRACT;
			delete process.env.SATYRN_FILE_BASELINES;
			fs.rmSync(cwd, { recursive: true, force: true });
		}
	});
});

describe("implementer tool policy", () => {
	const cwd = fs.mkdtempSync(path.join(os.tmpdir(), "satyrn-policy-"));
	fs.mkdirSync(path.join(cwd, "src"));
	fs.writeFileSync(path.join(cwd, "src/types.ts"), "export type T = string;\n");
	fs.writeFileSync(path.join(cwd, "src/shared.ts"), "export const old = true;\n");
	const contract: HandoffContract = {
		...CONTRACT,
		writableFiles: [
			{ path: "src/feature.ts" },
			{ path: "src/shared.ts" },
		],
	};
	afterAll(() => fs.rmSync(cwd, { recursive: true, force: true }));

	test("blocks raw mutation tools and paths outside exact packet scope", () => {
		const policy = new ImplementerPolicy(contract, cwd);
		expect(policy.inspect("read", { path: "README.md" })?.kind).toBe("scope_blocked");
		expect(policy.inspect("write", { path: "../escape.ts" })?.kind).toBe("scope_blocked");
		expect(policy.inspect("bash", { command: "pytest" })?.kind).toBe("scope_blocked");
	});

	test("permits a declared write; the engine, not tool order, checks the baseline", () => {
		const policy = new ImplementerPolicy(contract, cwd);
		expect(policy.inspect("write", { path: "src/shared.ts", content: "export const revised = true;\n" })).toBeUndefined();
	});

	test("permits a declared edit and blocks one outside exact packet scope", () => {
		const policy = new ImplementerPolicy(contract, cwd);
		expect(policy.inspect("edit", { path: "src/shared.ts", edits: [{ oldText: "old", newText: "new" }] })).toBeUndefined();
		expect(policy.inspect("edit", { path: "README.md", edits: [{ oldText: "old", newText: "new" }] })?.kind).toBe("scope_blocked");
	});

	test("allows declared absent-file writes and enforces the hard budget", () => {
		const policy = new ImplementerPolicy(contract, cwd, 2);
		expect(policy.inspect("write", { path: "src/feature.ts", content: "answer = 42\n" })).toBeUndefined();
		expect(policy.inspect("read", { path: "src/types.ts" })).toBeUndefined();
		expect(policy.inspect("read", { path: "src/types.ts" })?.kind).toBe("tool_budget_exhausted");
	});
});

describe("deterministic mutation engine", () => {
	const cwd = fs.mkdtempSync(path.join(os.tmpdir(), "satyrn-mutate-"));
	afterAll(() => fs.rmSync(cwd, { recursive: true, force: true }));

	test("creates absent files and reconciles present files from a read revision", () => {
		fs.writeFileSync(path.join(cwd, "app.py"), "@app.get(\"/about\")\ndef about():\n    return \"about\"\n");
		const engine = new MutationEngine(cwd, captureFileBaselines(cwd, ["app.py", "new.py"]));
		const receipt = engine.readReceipt("app.py");
		const revised = "@app.get(\"/about\")\ndef about():\n    return \"about\"\n\n@app.get(\"/contact\")\ndef contact():\n    return \"contact\"\n";
		const existing = engine.propose("app.py", receipt.sha256, revised);
		expect(existing.operation).toBe("reconcile");
		expect(existing.sha256).toBe(sha256(revised));
		const created = engine.propose("new.py", ABSENT_REVISION, "answer = 42\n");
		expect(created.operation).toBe("create");
		expect(fs.readFileSync(path.join(cwd, "new.py"), "utf8")).toBe("answer = 42\n");
	});

	test("refuses stale revisions and public-symbol deletion without changing the file", () => {
		const engine = new MutationEngine(cwd, captureFileBaselines(cwd, ["app.py"]));
		const before = fs.readFileSync(path.join(cwd, "app.py"), "utf8");
		expect(() => engine.propose("app.py", "stale", before)).toThrow(MutationRefusal);
		const receipt = engine.readReceipt("app.py");
		expect(() => engine.propose("app.py", receipt.sha256, "def contact():\n    return \"contact\"\n")).toThrow(MutationRefusal);
		expect(fs.readFileSync(path.join(cwd, "app.py"), "utf8")).toBe(before);
	});
});

describe("refactoring through the mutation engine", () => {
	const cwd = fs.mkdtempSync(path.join(os.tmpdir(), "satyrn-refactor-"));
	afterAll(() => fs.rmSync(cwd, { recursive: true, force: true }));

	const APP = 'def home():\n    return "home"\n\ndef about():\n    return "about"\n';

	function freshApp(name: string): { dir: string; engine: (removable?: string[]) => MutationEngine } {
		const dir = path.join(cwd, name);
		fs.mkdirSync(dir, { recursive: true });
		fs.writeFileSync(path.join(dir, "app.py"), APP);
		return {
			dir,
			engine: (removable = []) =>
				new MutationEngine(dir, captureFileBaselines(dir, ["app.py", "views.py"]), removable),
		};
	}

	test("a move survives when the destination is written first", () => {
		// The failure this whole change exists for: `lostSymbols` compared one
		// file against itself, so moving `about` out of app.py was refused even
		// though it reappeared next door. The engine never saw the other file.
		const { dir, engine } = freshApp("move-ok");
		const mutations = engine();
		mutations.propose("views.py", ABSENT_REVISION, 'def about():\n    return "about"\n');
		const receipt = mutations.readReceipt("app.py");
		const result = mutations.propose("app.py", receipt.sha256, 'def home():\n    return "home"\n');
		expect(result.operation).toBe("reconcile");
		expect(fs.readFileSync(path.join(dir, "app.py"), "utf8")).not.toContain("def about");
	});

	test("a move is refused when the source is emptied first, and says so", () => {
		const { engine } = freshApp("move-early");
		const mutations = engine();
		const receipt = mutations.readReceipt("app.py");
		expect(() => mutations.propose("app.py", receipt.sha256, 'def home():\n    return "home"\n'))
			.toThrow(/write the destination file first/);
	});

	test("a rename needs a declaration, and is allowed with one", () => {
		const { engine } = freshApp("rename-undeclared");
		const undeclared = engine();
		const first = undeclared.readReceipt("app.py");
		expect(() => undeclared.propose("app.py", first.sha256, 'def home():\n    return "home"\n\ndef summary():\n    return "about"\n'))
			.toThrow(/removableSymbols/);

		const { engine: declaredEngine } = freshApp("rename-declared");
		const mutations = declaredEngine(["about"]);
		const receipt = mutations.readReceipt("app.py");
		const result = mutations.propose("app.py", receipt.sha256, 'def home():\n    return "home"\n\ndef summary():\n    return "about"\n');
		expect(result.operation).toBe("reconcile");
	});

	test("the original guarantee survives: undeclared, uncompensated loss is still refused", () => {
		const { dir, engine } = freshApp("destructive");
		const mutations = engine();
		const before = fs.readFileSync(path.join(dir, "app.py"), "utf8");
		const receipt = mutations.readReceipt("app.py");
		expect(() => mutations.propose("app.py", receipt.sha256, 'def home():\n    return "home"\n'))
			.toThrow(MutationRefusal);
		expect(fs.readFileSync(path.join(dir, "app.py"), "utf8")).toBe(before);
	});

	test("a declaration does not license unrelated destruction", () => {
		const { engine } = freshApp("narrow-declaration");
		const mutations = engine(["about"]);
		const receipt = mutations.readReceipt("app.py");
		// `home` was never declared, so removing it stays refused even though
		// this invocation is permitted to drop `about`.
		expect(() => mutations.propose("app.py", receipt.sha256, 'def summary():\n    return "x"\n'))
			.toThrow(/function:home/);
	});
});

// proposeEdits: the 2026-08-11 re-plan's step 2. A model that reliably
// speaks diffs was, under `write` alone, emitting the changed fragment as
// if it were the complete file; `write` then overwrote everything else.
// These tests are this task's rule-7 obligation: the mutation engine's
// checks do not get cited as validated until they clear a false-rejection
// test, same as any other admitted component.
describe("proposeEdits: diff-shaped mutation", () => {
	const cwd = fs.mkdtempSync(path.join(os.tmpdir(), "satyrn-edit-"));
	afterAll(() => fs.rmSync(cwd, { recursive: true, force: true }));

	test("applies a unique anchor and reconciles like a whole-file write", () => {
		fs.writeFileSync(path.join(cwd, "app.py"), 'def home():\n    return "home"\n');
		const engine = new MutationEngine(cwd, captureFileBaselines(cwd, ["app.py"]));
		const receipt = engine.readReceipt("app.py");
		const result = engine.proposeEdits("app.py", receipt.sha256, [
			{ oldText: 'return "home"', newText: 'return "home page"' },
		]);
		expect(result.operation).toBe("reconcile");
		expect(fs.readFileSync(path.join(cwd, "app.py"), "utf8")).toBe('def home():\n    return "home page"\n');
	});

	test("applies edits in order, each against the previous edit's result", () => {
		fs.writeFileSync(path.join(cwd, "seq.py"), "a = 1\nb = 2\n");
		const engine = new MutationEngine(cwd, captureFileBaselines(cwd, ["seq.py"]));
		const receipt = engine.readReceipt("seq.py");
		engine.proposeEdits("seq.py", receipt.sha256, [
			{ oldText: "a = 1", newText: "a = 10" },
			{ oldText: "a = 10\nb = 2", newText: "a = 10\nb = 20" },
		]);
		expect(fs.readFileSync(path.join(cwd, "seq.py"), "utf8")).toBe("a = 10\nb = 20\n");
	});

	test("refuses an oldText that is not present", () => {
		fs.writeFileSync(path.join(cwd, "missing.py"), "a = 1\n");
		const engine = new MutationEngine(cwd, captureFileBaselines(cwd, ["missing.py"]));
		const receipt = engine.readReceipt("missing.py");
		expect(() => engine.proposeEdits("missing.py", receipt.sha256, [{ oldText: "b = 2", newText: "b = 3" }]))
			.toThrow(MutationRefusal);
		expect(fs.readFileSync(path.join(cwd, "missing.py"), "utf8")).toBe("a = 1\n");
	});

	test("refuses an ambiguous oldText that matches more than once", () => {
		fs.writeFileSync(path.join(cwd, "dup.py"), "x = 1\nx = 1\n");
		const engine = new MutationEngine(cwd, captureFileBaselines(cwd, ["dup.py"]));
		const receipt = engine.readReceipt("dup.py");
		expect(() => engine.proposeEdits("dup.py", receipt.sha256, [{ oldText: "x = 1", newText: "x = 2" }]))
			.toThrow(/unique/);
	});

	test("refuses editing an absent file; write is required to create one", () => {
		const engine = new MutationEngine(cwd, captureFileBaselines(cwd, ["new.py"]));
		expect(() => engine.proposeEdits("new.py", ABSENT_REVISION, [{ oldText: "x", newText: "y" }]))
			.toThrow(/write/);
	});

	test("refuses a stale revision without changing the file", () => {
		fs.writeFileSync(path.join(cwd, "stale.py"), "a = 1\n");
		const engine = new MutationEngine(cwd, captureFileBaselines(cwd, ["stale.py"]));
		expect(() => engine.proposeEdits("stale.py", "not-the-real-sha", [{ oldText: "a = 1", newText: "a = 2" }]))
			.toThrow(MutationRefusal);
		expect(fs.readFileSync(path.join(cwd, "stale.py"), "utf8")).toBe("a = 1\n");
	});

	test("refuses undeclared, uncompensated symbol loss the same as propose()", () => {
		fs.writeFileSync(path.join(cwd, "guarded.py"), 'def home():\n    return "home"\n\ndef about():\n    return "about"\n');
		const engine = new MutationEngine(cwd, captureFileBaselines(cwd, ["guarded.py"]));
		const receipt = engine.readReceipt("guarded.py");
		expect(() => engine.proposeEdits("guarded.py", receipt.sha256, [
			{ oldText: 'def about():\n    return "about"\n', newText: "" },
		])).toThrow(/removableSymbols/);
	});

	test("a declared rename survives through the edit path", () => {
		fs.writeFileSync(path.join(cwd, "rename.py"), 'def home():\n    return "home"\n\ndef about():\n    return "about"\n');
		const engine = new MutationEngine(cwd, captureFileBaselines(cwd, ["rename.py"]), ["about"]);
		const receipt = engine.readReceipt("rename.py");
		const result = engine.proposeEdits("rename.py", receipt.sha256, [
			{ oldText: "def about():", newText: "def summary():" },
		]);
		expect(result.operation).toBe("reconcile");
		expect(fs.readFileSync(path.join(cwd, "rename.py"), "utf8")).toContain("def summary():");
	});

	test("a move survives through the edit path when the destination is written first", () => {
		const dir = path.join(cwd, "move");
		fs.mkdirSync(dir);
		fs.writeFileSync(path.join(dir, "app.py"), 'def home():\n    return "home"\n\ndef about():\n    return "about"\n');
		const engine = new MutationEngine(dir, captureFileBaselines(dir, ["app.py", "views.py"]));
		engine.propose("views.py", ABSENT_REVISION, 'def about():\n    return "about"\n');
		const receipt = engine.readReceipt("app.py");
		const result = engine.proposeEdits("app.py", receipt.sha256, [
			{ oldText: '\n\ndef about():\n    return "about"\n', newText: "\n" },
		]);
		expect(result.operation).toBe("reconcile");
		expect(fs.readFileSync(path.join(dir, "app.py"), "utf8")).not.toContain("def about");
	});

	// The load-bearing property this whole path exists for: `propose()`'s
	// MAX_PROPOSAL_BYTES check is on the reconstructed whole file, which
	// forecloses any edit to a file already near or over the limit. The
	// edit path must check the payload the model actually emits instead, so
	// a one-line change to a large file stays cheap regardless of the
	// file's own size.
	test("the size check is on the edit payload, not the file it produces", () => {
		const big = `x = 1\n${"# padding line\n".repeat(3000)}`;
		expect(Buffer.byteLength(big, "utf8")).toBeGreaterThan(MAX_PROPOSAL_BYTES);
		fs.writeFileSync(path.join(cwd, "big.py"), big);
		const engine = new MutationEngine(cwd, captureFileBaselines(cwd, ["big.py"]));
		const receipt = engine.readReceipt("big.py");
		const result = engine.proposeEdits("big.py", receipt.sha256, [{ oldText: "x = 1", newText: "x = 2" }]);
		expect(result.operation).toBe("reconcile");
		expect(fs.readFileSync(path.join(cwd, "big.py"), "utf8").startsWith("x = 2\n")).toBe(true);
	});

	test("refuses an edit payload that itself exceeds the proposal limit", () => {
		fs.writeFileSync(path.join(cwd, "hugepayload.py"), "x = 1\n");
		const engine = new MutationEngine(cwd, captureFileBaselines(cwd, ["hugepayload.py"]));
		const receipt = engine.readReceipt("hugepayload.py");
		const huge = "y".repeat(MAX_PROPOSAL_BYTES + 1);
		expect(() => engine.proposeEdits("hugepayload.py", receipt.sha256, [{ oldText: "x = 1", newText: huge }]))
			.toThrow(/proposal limit/);
	});

	test("a newText containing a dollar substitution pattern is written literally", () => {
		// String.prototype.replace treats $&, $1, $`, $' in its *replacement*
		// argument as substitution patterns, not literal text. A naive
		// `content.replace(oldText, newText)` would silently mangle any
		// newText containing an ordinary `$` sequence -- an f-string, a
		// shell variable, a regex literal, a price in a docstring.
		fs.writeFileSync(path.join(cwd, "dollar.py"), 'x = 1\n');
		const engine = new MutationEngine(cwd, captureFileBaselines(cwd, ["dollar.py"]));
		const receipt = engine.readReceipt("dollar.py");
		engine.proposeEdits("dollar.py", receipt.sha256, [
			{ oldText: "x = 1", newText: 'x = f"{cost}$"  # regex: $&, $1, $`, $\'' },
		]);
		expect(fs.readFileSync(path.join(cwd, "dollar.py"), "utf8"))
			.toBe('x = f"{cost}$"  # regex: $&, $1, $`, $\'\n');
	});

	test("a harmless successful edit does not disarm the destructive-overwrite check for symbols already in the file", () => {
		// The bug this guards against: #recordGains used to record every
		// symbol in the *post-edit file*, not just symbols the edit added.
		// One successful edit that never touches `home`/`contact` would
		// still mark them "gained" (present in `next`), and a later
		// fragment write dropping them would be excused as if this
		// invocation had put them there -- exactly the failure this engine
		// exists to refuse, and exactly the sequence a model that speaks
		// diffs (a small edit, then a fragment write) produces naturally.
		fs.writeFileSync(
			path.join(cwd, "guard.py"),
			'def home():\n    return "home"\n\ndef about():\n    return "about"\n\ndef contact():\n    return "contact"\n',
		);
		const engine = new MutationEngine(cwd, captureFileBaselines(cwd, ["guard.py"]));

		// A harmless edit: touches only `about`'s body, adds no symbol.
		const first = engine.readReceipt("guard.py");
		engine.proposeEdits("guard.py", first.sha256, [
			{ oldText: 'return "about"', newText: 'return "about page"' },
		]);

		// A fragment write dropping `home` and `contact`, neither declared
		// removable, must still be refused -- the earlier edit must not
		// have put them on the gained ledger.
		const second = engine.readReceipt("guard.py");
		expect(() => engine.propose("guard.py", second.sha256, 'def about():\n    return "about page"\n'))
			.toThrow(MutationRefusal);
		expect(fs.readFileSync(path.join(cwd, "guard.py"), "utf8")).toContain("def home");
		expect(fs.readFileSync(path.join(cwd, "guard.py"), "utf8")).toContain("def contact");
	});

	test("an LF newText into a CRLF file does not leave mixed line endings", () => {
		fs.writeFileSync(path.join(cwd, "crlf.py"), "x = 1\r\ny = 2\r\n");
		const engine = new MutationEngine(cwd, captureFileBaselines(cwd, ["crlf.py"]));
		const receipt = engine.readReceipt("crlf.py");
		// A newText with a bare \n, as any ordinary edit call supplies.
		engine.proposeEdits("crlf.py", receipt.sha256, [{ oldText: "x = 1", newText: "x = 10\ny = 20" }]);
		const written = fs.readFileSync(path.join(cwd, "crlf.py"), "utf8");
		expect(written).toBe("x = 10\r\ny = 20\r\ny = 2\r\n");
	});
});
