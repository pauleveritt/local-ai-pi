const TARGET_KEYS = ["path", "filePath", "file_path", "file"];

/** Return the path-shaped argument from a Pi tool event without retaining content. */
export function targetOf(input: unknown): string | null {
	if (!input || typeof input !== "object") return null;
	const record = input as Record<string, unknown>;
	for (const key of TARGET_KEYS) {
		const value = record[key];
		if (typeof value === "string" && value) return value;
	}
	return null;
}
