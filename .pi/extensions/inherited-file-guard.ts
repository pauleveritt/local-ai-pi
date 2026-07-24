/**
 * Inherited-file guard — experimental mechanism for the write-vs-edit question.
 *
 * lessons.md #12 has two clauses. Clause 1: a whole-file `write` beats
 * anchor-based edits when the phase owns the file. Clause 2: "whole-file
 * writes are unsafe when another phase owns part of the file: they can erase
 * routes, imports, or behavior that must survive."
 *
 * The prior course only ever exercised clause 1 — it built each phase from an
 * empty workspace, so the phase always owned the whole file. The seeded
 * incremental workload makes clause 2 reachable for the first time, and
 * forensics on 8 seeded Phase 2 runs found a perfect split: every run that
 * EXTENDED inherited files passed (6/6); every run that REWROTE one failed
 * (2/2), including the preservation breaker.
 *
 * This guard turns that correlation into a testable intervention: `write` is
 * blocked for files that already existed when the session started, while
 * `write` to NEW files and `edit` everywhere stay allowed. The model keeps the
 * ability to create models.py and templates/complaints.html; it loses only the
 * ability to clobber what it inherited.
 *
 * Mechanism: `tool_call` returning { block, reason }. Categorical, not
 * advisory — the failure becomes structurally impossible rather than
 * discouraged.
 */
import * as fs from "node:fs";
import * as path from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

/** Files the harness owns; never worth guarding or reporting on. */
const IGNORED = new Set(["pyproject.toml", ".gitignore", "uv.lock"]);

function snapshot(root: string): Set<string> {
	const found = new Set<string>();
	const walk = (dir: string) => {
		let entries: fs.Dirent[];
		try {
			entries = fs.readdirSync(dir, { withFileTypes: true });
		} catch {
			return;
		}
		for (const e of entries) {
			if (e.name === ".git" || e.name === ".venv" || e.name === "__pycache__") continue;
			if (e.name === ".pi" || e.name === "node_modules") continue;
			const abs = path.join(dir, e.name);
			if (e.isDirectory()) walk(abs);
			else found.add(path.relative(root, abs));
		}
	};
	walk(root);
	return found;
}

export default function (pi: ExtensionAPI) {
	let inherited = new Set<string>();

	pi.on("session_start", (_event, ctx) => {
		inherited = snapshot(ctx.cwd);
	});

	pi.on("tool_call", (event, ctx) => {
		if (event.toolName !== "write") return;
		const raw = (event.input as Record<string, unknown>);
		const p = String(raw.file_path ?? raw.path ?? "");
		if (!p) return;

		const rel = path.isAbsolute(p) ? path.relative(ctx.cwd, p) : p.replace(/^\.\//, "");
		if (IGNORED.has(rel)) return;
		if (!inherited.has(rel)) return; // new file — writing it is fine

		pi.appendEntry("inherited_write_blocked", { path: rel });
		return {
			block: true,
			reason:
				`Blocked: \`${rel}\` already existed before this task started, and a ` +
				`whole-file write would erase behavior from earlier work that must ` +
				`survive. Use the \`edit\` tool to make a targeted change to this file ` +
				`instead. (Writing NEW files is allowed.)`,
		};
	});
}
