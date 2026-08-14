import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { spawn } from "node:child_process";
import { writeFile, mkdtemp } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

export function buildDeliverCandidateArgv(opts: {
	repo: string;
	task: string;
	promptFile: string;
	validation: string;
	model: string;
}): string[] {
	return [
		"run", "python", "-m", "tools.deliver_candidate",
		"--repo", opts.repo,
		"--task", opts.task,
		"--prompt-file", opts.promptFile,
		"--validation", opts.validation,
		"--model", opts.model,
	];
}

function slugify(text: string): string {
	return text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 40) || "task";
}

export default function (pi: ExtensionAPI) {
	pi.registerCommand("implement", {
		description: "Orchestrate a bounded change: chew a task into a handoff packet and drive the implementer.",
		handler: async (args, ctx) => {
			const prompt = args.trim();
			if (!prompt) {
				ctx.ui.notify("Usage: /implement <task> — the orchestrator chews it into a handoff packet.", "warning");
				return;
			}
			const dir = await mkdtemp(join(tmpdir(), "implement-"));
			const promptFile = join(dir, "prompt.md");
			await writeFile(promptFile, prompt);
			const argv = buildDeliverCandidateArgv({
				repo: ctx.cwd,
				task: slugify(prompt),
				promptFile,
				validation: "pytest -q",
				model: ctx.model
					? `${ctx.model.provider}/${ctx.model.id}`
					: "omlx/gemma-4-12B-it-MLX-8bit",
			});
			ctx.ui.notify(`Orchestrating: ${argv.join(" ")}`, "info");
			const child = spawn("uv", argv, { cwd: ctx.cwd });
			child.stdout.on("data", (d) => ctx.ui.notify(String(d).trim(), "info"));
			child.stderr.on("data", (d) => ctx.ui.notify(String(d).trim(), "warning"));
		},
	});
}
