/**
 * Guard behaviour, pinned.
 *
 *     bun test extensions/guards/
 *
 * Ported from `phase6-orchestrator-spike`'s `guards.test.ts`, trimmed to the
 * two guards this branch ports: loop-breaker (the pure-function form used
 * internally by `extensions/orchestration/implementer.ts`; the standalone
 * envelope-arm extension at `.pi/extensions/loop-breaker.ts` is a separate,
 * frozen artifact and is untouched by this file) and preserve-symbols.
 * turn-budget, validation-signal and the guard registry (`index.ts`) were
 * not ported -- implementer-policy.ts already enforces its own tool budget.
 */

import { describe, expect, test } from "bun:test";
import * as fs from "node:fs";
import { callKey, createLoopBreaker, THRESHOLD, WINDOW } from "./loop-breaker";
import { createPreserveSymbols, symbolsIn } from "./preserve-symbols";
import type { ToolCall } from "./types";

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

describe("the two loop-breaker artifacts", () => {
	// There are deliberately two implementations of one policy:
	//
	//   .pi/extensions/loop-breaker.ts   a self-contained Pi extension.
	//       Imports nothing local -- README's install is `cp` of this one
	//       file into ~/.pi/agent/extensions/, so a local import would
	//       break it. This is the standalone artifact.
	//
	//   extensions/guards/loop-breaker.ts  a pure Guard factory, imported
	//       by the bounded implementer and covered by the tests above.
	//
	// `main` added extensions/guards/index.ts to end an earlier duplication,
	// with the rationale "one artifact, tested where it lives". That fix
	// cannot extend to this pair -- collapsing them would cost the
	// copy-one-file install. What it was really protecting against is the
	// two drifting apart, so this pins that directly instead. index.ts
	// itself was deleted when the branches merged: it re-exported the
	// standalone for one caller (tools/replay_guards.mjs), which now
	// imports the standalone itself.
	const standalone = fs.readFileSync(
		new URL("../../.pi/extensions/loop-breaker.ts", import.meta.url), "utf8",
	);

	function constantIn(source: string, name: string): number {
		const match = source.match(new RegExp(`${name}\\s*=\\s*(\\d+)`));
		if (!match) throw new Error(`${name} not found`);
		return Number(match[1]);
	}

	test("the standalone extension and the Guard agree on WINDOW and THRESHOLD", () => {
		// If these diverge, a contributor's installed copy refuses at a
		// different point than the measured one -- and every number this
		// project published about the loop breaker describes the other file.
		expect(constantIn(standalone, "WINDOW")).toBe(WINDOW);
		expect(constantIn(standalone, "THRESHOLD")).toBe(THRESHOLD);
	});

	test("the standalone extension stays free of local imports", () => {
		// The property that makes `cp` a complete install. A relative
		// import here would break the README's two-command instructions
		// without breaking any other test.
		const localImports = standalone
			.split("\n")
			.filter((line) => /^import\s/.test(line) && /["']\.{1,2}\//.test(line));
		expect(localImports).toEqual([]);
	});

	test("the replay harness loads the standalone, not the Guard", () => {
		// Both files export a working loop breaker, so pointing the replay
		// at the wrong one still passes every fixture -- it would just be
		// measuring a file nobody installs. That is exactly the drift
		// index.ts existed to prevent, and this is what survives it.
		const replay = fs.readFileSync(
			new URL("../../tools/replay_guards.mjs", import.meta.url), "utf8",
		);
		expect(replay).toContain('".pi/extensions/loop-breaker.ts"');
		expect(replay).not.toContain("extensions/guards/loop-breaker.ts\"");
	});
});
