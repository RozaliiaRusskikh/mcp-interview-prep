import { useState, type FormEvent } from "react";
import AssistantIcon from "../components/AssistantIcon";
import { PROMPTS } from "../constants/prompts";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000";

type Exchange = {
  id: number;
  question: string;
  answer?: string;
  error?: string;
};

export default function ChatPage() {
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function ask(question: string) {
    if (!question.trim() || loading) return;
    const id = exchanges.length + 1;
    setExchanges((prev) => [...prev, { id, question }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!res.ok) throw new Error(`Backend returned ${res.status}`);
      const data: { answer: string } = await res.json();
      setExchanges((prev) =>
        prev.map((e) => (e.id === id ? { ...e, answer: data.answer } : e))
      );
    } catch {
      setExchanges((prev) =>
        prev.map((e) =>
          e.id === id
            ? { ...e, error: "Couldn't reach the backend. Confirm it's running, then ask again." }
            : e
        )
      );
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    ask(input);
  }

  return (
    <>
      <div>
        <h1 className="font-display text-4xl sm:text-5xl font-medium mb-4">
          Ask my assistant anything about my work.
        </h1>
        <p className="text-ink/70">
          It's trained on my professional experience, so it answers using my resume,
          real engineering stories, projects I've delivered, and recommendations from
          colleagues — all in my voice.
        </p>
      </div>

      {exchanges.length === 0 && (
        <div className="flex flex-wrap justify-center gap-2">
          {PROMPTS.map((p) => (
            <button
              key={p}
              onClick={() => ask(p)}
              className="font-mono text-xs uppercase tracking-wide border border-ink text-ink px-3 py-2
                         cursor-pointer transition-colors hover:bg-ink hover:text-paper
                         focus-visible:outline-2 focus-visible:outline-ledger"
            >
              {p}
            </button>
          ))}
        </div>
      )}

      {exchanges.map((ex) => (
        <article key={ex.id} className="flex flex-col gap-3">
          <div className="flex flex-wrap items-baseline justify-center gap-x-3 gap-y-1">
            <span className="font-mono text-xs text-ink/40 whitespace-nowrap">Question {ex.id}</span>
            <p className="font-display italic text-lg text-ink/90 text-center max-w-full sm:max-w-[80%] border border-ink/15 bg-card px-4 py-2">
              {ex.question}
            </p>
          </div>

          {ex.error && (
            <div className="flex items-start gap-3 bg-card border border-ink/15 px-5 py-4">
              <AssistantIcon />
              <p className="text-sm text-stamp pt-1">{ex.error}</p>
            </div>
          )}

          {ex.answer && (
            <div className="flex items-start gap-3 bg-card border border-ink/15 px-5 py-4 motion-safe:animate-[cardIn_0.35s_ease-out]">
              <AssistantIcon />
              <p className="text-ink leading-relaxed pt-1">{ex.answer}</p>
            </div>
          )}

          {!ex.answer && !ex.error && (
            <div className="flex items-center gap-3 bg-card border border-ink/15 px-5 py-4 text-sm text-ink/50 font-mono">
              <AssistantIcon />
              Filing…
            </div>
          )}
        </article>
      ))}

      <form
        onSubmit={handleSubmit}
        className="fixed bottom-0 inset-x-0 bg-paper border-t border-ink/15"
      >
        <div className="max-w-175 mx-auto flex items-end gap-3 px-4 py-4">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question…"
            className="flex-1 bg-transparent border-b border-ink/30 py-2 outline-none
                       focus:border-ledger placeholder:text-ink/40"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="font-mono text-xs uppercase tracking-wide bg-ledger text-paper px-4 py-2
                       transition-colors cursor-pointer disabled:cursor-not-allowed disabled:opacity-40
                       hover:bg-ledger/85 focus-visible:outline-2 focus-visible:outline-ledger"
          >
            {loading ? "Filing…" : "Ask →"}
          </button>
        </div>
      </form>
    </>
  );
}
