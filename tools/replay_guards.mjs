#!/usr/bin/env node

/**
 * Replay recorded tool calls through the shipped TypeScript guard.
 *
 * This deliberately uses a tiny ExtensionAPI double rather than copying the
 * loop-breaker algorithm into Python. The replay therefore tests the artifact
 * that contributors install, with no model or network involved.
 */

import { readFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, resolve } from "node:path";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const extensionPath = resolve(root, "extensions/guards/index.ts");
const { default: guards } = await import(pathToFileURL(extensionPath));

function loadFixture(path) {
	return JSON.parse(path);
}

async function replay(fixture) {
	const handlers = new Map();
	const entries = [];
	guards({
		on(event, handler) {
			handlers.set(event, handler);
		},
		appendEntry(customType, data) {
			entries.push({ customType, data });
		},
	});

	const handler = handlers.get("tool_call");
	if (!handler) throw new Error("guards did not register tool_call");

	let blocked = 0;
	// 1-based index of the first refusal. A blocked count alone cannot
	// tell a guard that fires early from one that fires after the model
	// has already wasted most of its budget, and "how soon" is the whole
	// value of a loop breaker.
	let firstBlock = null;
	let index = 0;
	for (const call of fixture.calls) {
		index += 1;
		if (await handler(call)) {
			blocked += 1;
			if (firstBlock === null) firstBlock = index;
		}
	}
	return { calls: fixture.calls.length, blocked, firstBlock, entries };
}

const fixturePaths = process.argv.slice(2);
if (fixturePaths.length === 0) {
	console.error("usage: node --experimental-strip-types tools/replay_guards.mjs <fixture.json>");
	process.exit(2);
}

for (const fixturePath of fixturePaths) {
	const fixture = loadFixture(await readFile(resolve(fixturePath), "utf8"));
	const result = await replay(fixture);
	const expected = fixture.expected;
	const mismatches = [];
	if (result.blocked !== expected.blocked)
		mismatches.push(`blocked ${result.blocked} != ${expected.blocked}`);
	if (result.entries.length !== expected.entries)
		mismatches.push(`entries ${result.entries.length} != ${expected.entries}`);
	if ("firstBlock" in expected && result.firstBlock !== expected.firstBlock)
		mismatches.push(`firstBlock ${result.firstBlock} != ${expected.firstBlock}`);
	if (mismatches.length > 0) {
		throw new Error(`${fixture.name}: ${mismatches.join("; ")}`);
	}
	console.log(
		JSON.stringify({
			name: fixture.name,
			calls: result.calls,
			blocked: result.blocked,
			firstBlock: result.firstBlock,
			entries: result.entries.length,
		}),
	);
}
