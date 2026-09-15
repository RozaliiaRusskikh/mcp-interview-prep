import { useEffect, useState } from "react";
import RecommendationCard from "../components/RecommendationCard";
import RecommendationModal from "../components/RecommendationModal";
import { type Recommendation } from "../constants/recommendations";
import { BACKEND_URL } from "../config";

export default function RecommendationsPage() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [error, setError] = useState(false);
  const [selected, setSelected] = useState<Recommendation | null>(null);

  useEffect(() => {
    fetch(`${BACKEND_URL}/recommendations`)
      .then((res) => {
        if (!res.ok) throw new Error(`Backend returned ${res.status}`);
        return res.json();
      })
      .then(setRecommendations)
      .catch(() => setError(true));
  }, []);

  return (
    <section>
      <h1 className="font-display text-3xl font-medium mb-8">
        What people say about me
      </h1>
      {error && (
        <p className="text-ink/70">
          Couldn't load recommendations. Confirm the backend is running, then
          reload.
        </p>
      )}
      <div className="grid sm:grid-cols-2 gap-4">
        {recommendations.map((r) => (
          <RecommendationCard
            key={r.id}
            r={r}
            onExpand={() => setSelected(r)}
          />
        ))}
      </div>
      {selected && (
        <RecommendationModal r={selected} onClose={() => setSelected(null)} />
      )}
    </section>
  );
}
