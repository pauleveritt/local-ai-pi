import { expect, test } from "bun:test";
import { buildDeliverCandidateArgv } from "./orchestrator";

test("passes the contract path through and no longer hardcodes validation", () => {
	const argv = buildDeliverCandidateArgv({
		repo: "/repo",
		task: "enter-async-cms",
		contractPath: "/tmp/contract.md",
		model: "omlx/gemma-4-12B-it-MLX-8bit",
	});
	expect(argv).toEqual([
		"run", "python", "-m", "tools.deliver_candidate",
		"--repo", "/repo",
		"--task", "enter-async-cms",
		"--contract", "/tmp/contract.md",
		"--model", "omlx/gemma-4-12B-it-MLX-8bit",
	]);
	expect(argv).not.toContain("--prompt-file");
	expect(argv).not.toContain("--validation");
});
