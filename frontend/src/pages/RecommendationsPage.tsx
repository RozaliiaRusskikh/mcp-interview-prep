import { useEffect, useState } from "react";
import RecommendationCard from "../components/RecommendationCard";
import RecommendationModal from "../components/RecommendationModal";
import { type Recommendation } from "../constants/recommendations";
import { BACKEND_URL } from "../config";

export default function RecommendationsPage() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [selected, setSelected] = useState<Recommendation | null>(null);

  useEffect(() => {
    async function loadRecommendations() {
      setLoading(true);
      try {
        const res = await fetch(`${BACKEND_URL}/recommendations`);
        if (!res.ok) throw new Error(`Backend returned ${res.status}`);
        const data = await res.json();
        setRecommendations(data);
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    }
    loadRecommendations();
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
      {!loading && !error && recommendations.length === 0 && (
        <p className="text-ink/70">No recommendations to show yet.</p>
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
