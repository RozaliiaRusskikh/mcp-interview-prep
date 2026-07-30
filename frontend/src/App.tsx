import { BrowserRouter, Route, Routes } from "react-router-dom";
import Layout from "./Layout";
import ChatPage from "./ChatPage";
import RecommendationsPage from "./RecommendationsPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<ChatPage />} />
          <Route path="recommendations" element={<RecommendationsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
