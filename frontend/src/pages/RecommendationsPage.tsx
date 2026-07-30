import { useState } from "react";
import RecommendationCard from "../components/RecommendationCard";
import RecommendationModal from "../components/RecommendationModal";
import { RECOMMENDATIONS, type Recommendation } from "../constants/recommendations";

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
