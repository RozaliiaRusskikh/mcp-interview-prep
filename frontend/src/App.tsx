import { BrowserRouter, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ChatPage from "./pages/ChatPage";
import RecommendationsPage from "./pages/RecommendationsPage";

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
