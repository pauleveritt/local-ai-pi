import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import loopBreaker from "../../.pi/extensions/loop-breaker.ts";

/**
 * The single entry point for the project's installable guard extension.
 *
 * This re-exports the *tracked* loop breaker at `.pi/extensions/` rather
 * than carrying its own copy. There were two copies: identical logic,
 * divergent comments, one tracked and one not — so the replay harness
 * was exercising a file contributors do not install, and a fix to
 * either would silently not reach the other. One artifact, tested where
 * it lives.
 */
export default function guards(pi: ExtensionAPI) {
	loopBreaker(pi);
}
