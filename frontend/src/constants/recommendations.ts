// Shape of the data served by GET /recommendations (backend/mcp_server/data/recommendations.json
// is the single source of truth — see RecommendationsPage.tsx for the fetch).
export type Recommendation = {
  id: number;
  name: string;
  title: string;
  relationship: string;
  date: string;
  quote: string;
};
