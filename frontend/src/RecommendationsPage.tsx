import { useEffect, useRef, useState } from "react";
import { RECOMMENDATIONS, type Recommendation } from "./recommendations";

function RecommendationCard({ r, onExpand }: { r: Recommendation; onExpand: () => void }) {
  const quoteRef = useRef<HTMLParagraphElement>(null);
  const [truncated, setTruncated] = useState(false);

  useEffect(() => {
    const el = quoteRef.current;
    if (el) setTruncated(el.scrollHeight > el.clientHeight + 1);
  }, []);

  return (
    <div className="relative flex flex-col h-105 bg-card border border-ink/15 px-5 py-4">
      <div className="relative">
        <p ref={quoteRef} className="font-display italic text-ink/90 leading-relaxed pt-1 line-clamp-11">
          "{r.quote}"
        </p>
        {truncated && (
          <div className="absolute bottom-0 inset-x-0 h-6 bg-linear-to-t from-card to-transparent pointer-events-none" />
        )}
      </div>
      {truncated && (
        <button
          onClick={onExpand}
          className="font-mono text-xs text-ledger cursor-pointer hover:underline mt-2 self-start"
        >
          Read more →
        </button>
      )}
      <div className="mt-auto pt-3">
        <p className="font-mono text-xs text-ink/60">
          {r.name} — {r.title}
        </p>
        <p className="font-mono text-[11px] text-ink/40 mt-1">{r.relationship}</p>
      </div>
    </div>
  );
}

function RecommendationModal({ r, onClose }: { r: Recommendation; onClose: () => void }) {
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    closeRef.current?.focus();
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 px-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        className="relative bg-card border border-ink/20 max-w-lg w-full max-h-[80vh] overflow-y-auto px-6 py-6"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          ref={closeRef}
          onClick={onClose}
          aria-label="Close"
          className="absolute top-1 right-3 font-mono text-lg text-stamp cursor-pointer hover:text-stamp/70"
        >
          ✕
        </button>
        <p className="font-display italic text-ink/90 leading-relaxed pr-6">"{r.quote}"</p>
        <p className="font-mono text-xs text-ink/60 mt-4">
          {r.name} — {r.title}
        </p>
        <p className="font-mono text-[11px] text-ink/40 mt-1">{r.relationship}</p>
      </div>
    </div>
  );
}

export default function RecommendationsPage() {
  const [selected, setSelected] = useState<Recommendation | null>(null);

  return (
    <section>
      <h1 className="font-display text-3xl font-medium mb-6">What people say</h1>
      <div className="grid sm:grid-cols-2 gap-4">
        {RECOMMENDATIONS.map((r) => (
          <RecommendationCard key={r.name} r={r} onExpand={() => setSelected(r)} />
        ))}
      </div>
      {selected && <RecommendationModal r={selected} onClose={() => setSelected(null)} />}
    </section>
  );
}
