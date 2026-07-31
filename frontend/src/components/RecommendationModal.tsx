import { useEffect, useRef } from "react";
import type { Recommendation } from "../constants/recommendations";

export default function RecommendationModal({
  r,
  onClose,
}: {
  r: Recommendation;
  onClose: () => void;
}) {
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
          className="absolute top-1 right-3 font-mono text-lg text-stamp cursor-pointer transition-colors hover:text-stamp/70"
        >
          ✕
        </button>
        <p className="font-display italic text-ink/90 leading-relaxed pr-6">
          "{r.quote}"
        </p>
        <p className="font-mono text-xs text-ink/60 mt-4">
          {r.name} — {r.title}
        </p>
        <p className="font-mono text-[11px] text-ink/40 mt-1">
          {r.relationship}
        </p>
      </div>
    </div>
  );
}
