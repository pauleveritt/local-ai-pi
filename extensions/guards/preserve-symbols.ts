import type { Decision, Guard, ToolCall } from "./types";

/**
 * Candidate guard — refuse an `edit` that deletes a public symbol.
 *
 * **This is the first Phase 6 guard with a live failure behind it rather
 * than a historical one.** In a recorded 4-run batch on the preservation
 * suite, three runs failed the same way: asked to *add* a `/contact` route to
 * a working site, the model issued an edit that **replaced the existing
 * `/about` route** with it —
 *
 * ```diff
 * -@app.get("/about", response_class=HTMLResponse)
 * -def about(request: Request):
 * +@app.get("/contact", response_class=HTMLResponse)
 * +def contact(request: Request):
 * ```
 *
 * It treated "add a route" as "transform the nearest similar route". Three
 * acceptance tests failed from that one deletion.
 *
 * **This is not the stale-anchor failure `LESSONS.md` §12 documents.** The
 * anchor matched perfectly — Pi 0.83.0 even fuzzy-matches whitespace and
 * smart quotes now, so that whole class of mismatch is largely absorbed
 * upstream. The failure has moved from mechanics to *intent*: the model
 * chose live code that had to survive as its anchor.
 *
 * **What it does not need.** No acceptance file, no task description, no
 * knowledge of what the run is for. It compares an edit against *itself*:
 * a symbol named on the way in that is not named on the way out is being
 * deleted. That keeps it clear of this project's rule that a guard must
 * never consult the harness's contract.
 *
 * **What it cannot see.** `write` and bash heredocs bypass it entirely, and
 * that is not academic — the one run that *passed* did so by rewriting
 * `app.py` wholesale through a `cat <<EOF` heredoc, as a repair. Blocking
 * that escape hatch would have converted the only success into a failure, so
 * this guard deliberately governs `edit` alone.
 */

/** Tools whose payload this guard understands. */
const EDIT_TOOLS = new Set(["edit"]);

/**
 * What counts as a public symbol. Deliberately shallow: these are text
 * patterns, not a parse. A parser would be more precise and would also make
 * the guard language-specific and far larger than the loop-breaker's shape.
 */
const SYMBOL_PATTERNS: { kind: string; pattern: RegExp }[] = [
	{ kind: "function", pattern: /^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)/gm },
	{ kind: "class", pattern: /^\s*class\s+([A-Za-z_]\w*)/gm },
	// A route decorator names a URL rather than an identifier, and losing one
	// is exactly the observed failure. Matches @app.get("/x"), @router.post('/y').
	{ kind: "route", pattern: /^\s*@\w+\.(?:get|post|put|patch|delete)\(\s*["']([^"']+)["']/gm },
];

export interface FoundSymbol {
	kind: string;
	name: string;
}

export function symbolsIn(text: string): FoundSymbol[] {
	const found: FoundSymbol[] = [];
	for (const { kind, pattern } of SYMBOL_PATTERNS) {
		// `matchAll` needs a fresh lastIndex; the patterns are module-level
		// and global, so reusing them across calls without this leaks state.
		pattern.lastIndex = 0;
		for (const match of text.matchAll(pattern)) {
			found.push({ kind, name: match[1] });
		}
	}
	return found;
}

interface EditPayload {
	path?: unknown;
	edits?: unknown;
}

/**
 * Symbols present in the `oldText`s of a call but absent from *every*
 * `newText` of the same call.
 *
 * The union across `newText`s is load-bearing. Pi 0.83.0's edit input is
 * `{path, edits: [{oldText, newText}]}` — a **multi-edit array**, not the
 * `oldString`/`newString` pair an earlier draft of this guard assumed and
 * which would have matched nothing. A model that moves a function by
 * deleting it in one entry and re-adding it in another is refactoring, not
 * destroying, and comparing entry-by-entry would refuse it.
 */
export function deletedSymbols(input: unknown): FoundSymbol[] {
	const payload = (input ?? {}) as EditPayload;
	if (!Array.isArray(payload.edits)) return [];

	const olds: string[] = [];
	const news: string[] = [];
	for (const entry of payload.edits) {
		const { oldText, newText } = (entry ?? {}) as Record<string, unknown>;
		if (typeof oldText === "string") olds.push(oldText);
		if (typeof newText === "string") news.push(newText);
	}

	const surviving = new Set(
		news.flatMap((text) => symbolsIn(text)).map((s) => `${s.kind}:${s.name}`),
	);

	const deleted: FoundSymbol[] = [];
	const seen = new Set<string>();
	for (const symbol of olds.flatMap(symbolsIn)) {
		const key = `${symbol.kind}:${symbol.name}`;
		if (surviving.has(key) || seen.has(key)) continue;
		seen.add(key);
		deleted.push(symbol);
	}
	return deleted;
}

function describe(symbol: FoundSymbol): string {
	return symbol.kind === "route" ? `the route \`${symbol.name}\`` : `\`${symbol.name}\``;
}

export function createPreserveSymbols(): Guard {
	let refused = 0;

	return {
		name: "preserve-symbols",
		inspect(call: ToolCall): Decision {
			if (!EDIT_TOOLS.has(call.toolName)) return undefined;

			const deleted = deletedSymbols(call.input);
			if (deleted.length === 0) return undefined;

			refused += 1;
			const named = deleted.map(describe).join(", ");
			return {
				block: true,
				reason:
					`This edit removes ${named}, which exists in the file already and ` +
					`is not replaced by anything in the new text. ` +
					`If you meant to ADD something, do not use existing code as the ` +
					`anchor — anchor on a line you are keeping and include it unchanged ` +
					`in the new text, so the new code is inserted alongside rather than ` +
					`on top of it. ` +
					`If you genuinely meant to delete ${named}, say so and do it in a ` +
					`separate edit.`,
				entry: {
					kind: "symbol_preserved",
					data: {
						path: typeof (call.input as EditPayload)?.path === "string"
							? (call.input as EditPayload).path
							: null,
						deleted: deleted.map((s) => `${s.kind}:${s.name}`),
						refusedSoFar: refused,
					},
				},
			};
		},
	};
}
