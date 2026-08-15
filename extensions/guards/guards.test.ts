/**
 * Guard behaviour, pinned.
 *
 *     bun test extensions/guards/
 *
 * Ported from `phase6-orchestrator-spike`'s `guards.test.ts`, trimmed to the
 * two guards this branch ports: loop-breaker (the pure-function form used
 * internally by `extensions/orchestration/implementer.ts`) and
 * preserve-symbols. turn-budget, validation-signal and that spike's guard
 * registry were not ported -- implementer-policy.ts already enforces its
 * own tool budget.
 *
 * The standalone extension at `.pi/extensions/loop-breaker.ts` is a
 * separate artifact with its own reasons; the behaviour tests below do not
 * exercise it, but the last describe block reads it and pins it against
 * this one. Do not confuse the spike's registry above with
 * `extensions/guards/index.ts`, a different, also-deleted file that block
 * discusses.
 */

import { describe, expect, test } from "bun:test";
import * as fs from "node:fs";
import { readFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import { callKey, createLoopBreaker, THRESHOLD, WINDOW } from "./loop-breaker";
import { createPreserveSymbols, symbolsIn } from "./preserve-symbols";
import type { ToolCall } from "./types";

// The shipped engine bundle (packages/engine/), the artifact a checkout
// loads and a pi install delivers. The "engine bundle artifact" block
// below pins it against the guard sources.
const ENGINE = new URL("../../packages/engine/engine.ts", import.meta.url);
const ENGINE_SOURCE = await readFile(ENGINE, "utf8");
const engineModule = await import(ENGINE.href);

const loopFixture: ToolCall = { toolName: "bash", input: { command: "ls -R" } };

const bash = (command: string): ToolCall => ({
	toolName: "bash",
	input: { command },
});

describe("loop-breaker", () => {
	test("admits the first THRESHOLD identical calls and refuses the next", () => {
		const guard = createLoopBreaker(20, 5);
		const call = bash("ls -R");

		for (let i = 0; i < 5; i++) expect(guard.inspect(call)).toBeUndefined();
		expect(guard.inspect(call)?.block).toBe(true);
	});

	test("a blocked call does not enter the window, so it stays blocked", () => {
		// The property that makes it a breaker rather than a rate limiter: a
		// model that keeps retrying must not slide its own repeats out of
		// view and be let through again.
		const guard = createLoopBreaker(20, 5);
		const call = bash("ls -R");
		for (let i = 0; i < 5; i++) guard.inspect(call);

		for (let i = 0; i < 30; i++) expect(guard.inspect(call)?.block).toBe(true);
	});

	test("differing calls never trip it", () => {
		const guard = createLoopBreaker(20, 5);
		for (let i = 0; i < 50; i++) {
			expect(guard.inspect(bash(`echo ${i}`))).toBeUndefined();
		}
	});

	test("argument order does not change a call's identity", () => {
		expect(callKey("bash", { a: 1, b: 2 })).toBe(callKey("bash", { b: 2, a: 1 }));
	});
});

describe("preserve-symbols", () => {
	// The exact payload the model sent in the three failing preservation
	// runs, reduced to its edits array. Pi 0.83.0's shape is
	// {path, edits:[{oldText,newText}]} -- an earlier draft of this guard
	// assumed oldString/newString and would have matched nothing.
	const destructive = {
		toolName: "edit",
		input: {
			path: "app.py",
			edits: [
				{
					oldText:
						'@app.get("/about", response_class=HTMLResponse)\ndef about(request: Request):\n    return templates.TemplateResponse(\n        "about.html", {"request": request, "title": "About"}\n    )',
					newText:
						'@app.get("/contact", response_class=HTMLResponse)\ndef contact(request: Request):\n    return templates.TemplateResponse(\n        "contact.html", {"request": request, "title": "Contact"}\n    )',
				},
			],
		},
	};

	// The nav edit every run made, including the one that passed. Adds a
	// link and keeps both existing ones. Nothing is deleted.
	const additive = {
		toolName: "edit",
		input: {
			path: "templates/base.html",
			edits: [
				{
					oldText: '    <a href="/">Home</a>\n    <a href="/about">About</a>',
					newText:
						'    <a href="/">Home</a>\n    <a href="/about">About</a>\n    <a href="/contact">Contact</a>',
				},
			],
		},
	};

	test("fires on the recorded destructive edit", () => {
		const decision = createPreserveSymbols().inspect(destructive);
		expect(decision?.block).toBe(true);
		expect(decision?.entry.data.deleted).toEqual(["function:about", "route:/about"]);
	});

	test("stays silent on the additive edit every run made", () => {
		expect(createPreserveSymbols().inspect(additive)).toBeUndefined();
	});

	test("a symbol moved between entries of one call is not a deletion", () => {
		// Refactoring: deleted in one entry, re-added in another. Comparing
		// entry-by-entry instead of against the union would refuse this.
		const moved = {
			toolName: "edit",
			input: {
				path: "app.py",
				edits: [
					{ oldText: "def helper():\n    pass", newText: "" },
					{ oldText: "# tail", newText: "def helper():\n    pass\n# tail" },
				],
			},
		};
		expect(createPreserveSymbols().inspect(moved)).toBeUndefined();
	});

	test("ignores every tool that is not an edit", () => {
		expect(
			createPreserveSymbols().inspect({
				toolName: "write",
				input: { path: "app.py", content: "" },
			}),
		).toBeUndefined();
	});

	test("finds functions, classes and route decorators", () => {
		const found = symbolsIn(
			'@app.get("/x")\ndef a():\n    pass\n\nclass B:\n    pass\n',
		).map((s) => `${s.kind}:${s.name}`);
		expect(found).toContain("function:a");
		expect(found).toContain("class:B");
		expect(found).toContain("route:/x");
	});

	test("the global patterns do not leak lastIndex between calls", () => {
		// Module-level global regexes reused without resetting lastIndex
		// silently return different results on the second call.
		const text = "def a():\n    pass\n";
		expect(symbolsIn(text)).toEqual(symbolsIn(text));
	});
});

function fakePi() {
	const handlers = new Map<string, (event: any) => unknown>();
	const entries: Array<[string, unknown]> = [];
	const pi = {
		on: (event: string, handler: (event: any) => unknown) => {
			handlers.set(event, handler);
		},
		appendEntry: (kind: string, data: unknown) => {
			entries.push([kind, data]);
		},
	} as any;
	return { pi, handlers, entries };
}

describe("the engine bundle artifact", () => {
	// The exact payload the model sent in the three failing preservation
	// runs, reduced to its edits array (copied verbatim from the
	// "preserve-symbols" block above, which scopes its copy to itself).
	const destructive = {
		toolName: "edit",
		input: {
			path: "app.py",
			edits: [
				{
					oldText:
						'@app.get("/about", response_class=HTMLResponse)\ndef about(request: Request):\n    return templates.TemplateResponse(\n        "about.html", {"request": request, "title": "About"}\n    )',
					newText:
						'@app.get("/contact", response_class=HTMLResponse)\ndef contact(request: Request):\n    return templates.TemplateResponse(\n        "contact.html", {"request": request, "title": "Contact"}\n    )',
				},
			],
		},
	};

	// The nav edit every run made, including the one that passed. Adds a
	// link and keeps both existing ones. Nothing is deleted.
	const additive = {
		toolName: "edit",
		input: {
			path: "templates/base.html",
			edits: [
				{
					oldText: '    <a href="/">Home</a>\n    <a href="/about">About</a>',
					newText:
						'    <a href="/">Home</a>\n    <a href="/about">About</a>\n    <a href="/contact">Contact</a>',
				},
			],
		},
	};

	test("the artifact stays free of local imports", () => {
		// The property that makes `cp` a complete install. A relative
		// import here would break the one-file install without breaking
		// any other test.
		const localImports = ENGINE_SOURCE
			.split("\n")
			.filter((line) => /^import\s/.test(line) && /["']\.{1,2}\//.test(line));
		expect(localImports).toEqual([]);
	});

	test("the artifact's constants agree with the Guard sources", () => {
		// If these diverge, an installed copy refuses at a different point
		// than the measured Guard.
		expect(engineModule.WINDOW).toBe(WINDOW);
		expect(engineModule.THRESHOLD).toBe(THRESHOLD);
	});

	test("the artifact's loop breaker fires on the repeated call and reasons like the Guard", () => {
		const source = createLoopBreaker();
		const artifact = engineModule.createLoopBreaker();
		for (let i = 0; i < 5; i++) {
			expect(source.inspect(loopFixture)).toBeUndefined();
			expect(artifact.inspect(loopFixture)).toBeUndefined();
		}
		const sourceDecision = source.inspect(loopFixture);
		const artifactDecision = artifact.inspect(loopFixture);
		expect(sourceDecision?.block).toBe(true);
		expect(artifactDecision?.block).toBe(true);
		expect(artifactDecision?.reason).toBe(sourceDecision?.reason);
	});

	test("the artifact's preserve-symbols fires on the recorded destructive edit and stays silent on the additive edit", () => {
		const source = createPreserveSymbols();
		const artifact = engineModule.createPreserveSymbols();
		const sourceDecision = source.inspect(destructive);
		const artifactDecision = artifact.inspect(destructive);
		expect(sourceDecision?.block).toBe(true);
		expect(artifactDecision?.block).toBe(true);
		expect(artifactDecision?.entry.data.deleted).toEqual(["function:about", "route:/about"]);
		expect(artifactDecision?.reason).toBe(sourceDecision?.reason);
		expect(artifact.inspect(additive)).toBeUndefined();
	});

	test("the default export registers both guards on tool_call", async () => {
		const first = fakePi();
		engineModule.default(first.pi);
		expect(first.handlers.has("tool_call")).toBe(true);

		// loop-breaker: five admitted calls, then the sixth is refused.
		const loopRun = fakePi();
		engineModule.default(loopRun.pi);
		const loopHandler = loopRun.handlers.get("tool_call")!;
		for (let i = 0; i < 5; i++) {
			expect(await loopHandler(loopFixture)).toBeUndefined();
		}
		const blocked: any = await loopHandler(loopFixture);
		expect(blocked?.block).toBe(true);
		expect(blocked?.reason).toContain("You have already run this exact bash call");
		expect(loopRun.entries.length).toBe(1);
		expect(loopRun.entries[0][0]).toBe("loop_broken");

		// preserve-symbols: the destructive edit is refused.
		const symbolRun = fakePi();
		engineModule.default(symbolRun.pi);
		const symbolHandler = symbolRun.handlers.get("tool_call")!;
		const refused: any = await symbolHandler(destructive);
		expect(refused?.block).toBe(true);
		expect(symbolRun.entries.length).toBe(1);
		expect(symbolRun.entries[0][0]).toBe("symbol_preserved");
	});
});
