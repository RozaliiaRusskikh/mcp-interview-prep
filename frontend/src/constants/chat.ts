export type Source = "deterministic" | "llm" | "rate_capped";

export const STAMP: Record<Source, { label: string; className: string }> = {
  deterministic: {
    label: "Filed — resume data",
    className: "text-stamp border-stamp",
  },
  llm: {
    label: "In Roza's words",
    className: "text-ledger border-ledger",
  },
  rate_capped: {
    label: "Filed — daily limit reached",
    className: "text-ink/50 border-ink/30",
  },
};
