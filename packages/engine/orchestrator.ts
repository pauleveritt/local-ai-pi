import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { spawn } from "node:child_process";

export function buildDeliverCandidateArgv(opts: {
	repo: string;
	task: string;
	contractPath: string;
	model: string;
}): string[] {
	return [
		"run", "python", "-m", "tools.deliver_candidate",
		"--repo", opts.repo,
		"--task", opts.task,
		"--contract", opts.contractPath,
		"--model", opts.model,
	];
}

function slugify(text: string): string {
	return text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 40) || "task";
}

const USAGE =
	"Usage: /implement <contract-file> — a handoff contract, not a prompt. " +
	"Ask me to write one first (see the write-handoff-contract skill).";

export default function (pi: ExtensionAPI) {
	pi.registerCommand("implement", {
		description: "Drive the bounded implementer with a handoff contract file.",
		handler: async (args, ctx) => {
			const contractPath = args.trim();
			if (!contractPath) {
				ctx.ui.notify(USAGE, "warning");
				return;
			}
			const argv = buildDeliverCandidateArgv({
				repo: ctx.cwd,
				task: slugify(contractPath.split("/").pop() ?? "task"),
				contractPath,
				model: ctx.model
					? `${ctx.model.provider}/${ctx.model.id}`
					: "omlx/gemma-4-12B-it-MLX-8bit",
			});
			ctx.ui.notify(`Orchestrating: ${argv.join(" ")}`, "info");
			// Awaited, not fire-and-forget: in --print (non-interactive) mode
			// the session tears down as soon as the handler's promise settles,
			// and a stdout/stderr callback that fires after that touches a
			// stale ctx and crashes the process. Verified against a live
			// smoke run (2026-08-16) -- see the contract-file smoke doc.
			await new Promise<void>((resolve) => {
				const child = spawn("uv", argv, { cwd: ctx.cwd });
				child.stdout.on("data", (d) => ctx.ui.notify(String(d).trim(), "info"));
				child.stderr.on("data", (d) => ctx.ui.notify(String(d).trim(), "warning"));
				child.on("error", (e) => {
					ctx.ui.notify(`Could not start uv: ${e.message}`, "warning");
					resolve();
				});
				child.on("close", () => resolve());
			});
		},
	});
}
