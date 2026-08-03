import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

export default function (pi: ExtensionAPI) {
  pi.registerTool({
    name: "word_count",
    label: "Word count",
    description: "Count the words in a piece of text.",
    parameters: Type.Object({
      text: Type.String({ description: "Text to count the words in" }),
    }),
    async execute(_toolCallId, params) {
      const words = params.text.trim().split(/\s+/).filter(Boolean).length;
      return {
        content: [{ type: "text", text: String(words) }],
        details: { words },
      };
    },
  });
}
