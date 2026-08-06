import { useLayoutEffect, useRef, useState } from "react";
import type { Recommendation } from "../constants/recommendations";

export default function RecommendationCard({
  r,
  onExpand,
}: {
  r: Recommendation;
  onExpand: () => void;
}) {
  const quoteRef = useRef<HTMLParagraphElement>(null);
  const [truncated, setTruncated] = useState(false);

  useLayoutEffect(() => {
    const el = quoteRef.current;
    if (el) setTruncated(el.scrollHeight > el.clientHeight + 1);
  }, []);

  return (
    <div className="relative flex flex-col h-105 bg-card border border-ink/15 px-5 py-4 rounded-sm">
      <div className="relative">
        <p
          ref={quoteRef}
          className="font-display italic text-ink/90 leading-relaxed pt-1 line-clamp-11"
        >
          "{r.quote}"
        </p>
        {truncated && (
          <div className="absolute bottom-0 inset-x-0 h-6 bg-linear-to-t from-card to-transparent pointer-events-none" />
        )}
      </div>
      {truncated && (
        <button
          onClick={onExpand}
          className="font-mono text-xs text-ledger cursor-pointer border-b border-transparent transition-colors hover:border-ledger mt-2 self-start focus-visible:outline-2 focus-visible:outline-ledger"
        >
          Read more →
        </button>
      )}
      <div className="mt-auto pt-3">
        <p className="font-mono text-xs text-ink/60">
          {r.name} — {r.title}
        </p>
      </div>
    </div>
  );
}
