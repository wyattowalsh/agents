import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import { ToastProvider } from "./components/Toast";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { Layout } from "./components/Layout";
import { Pipeline } from "./views/Pipeline";
import { Feed } from "./views/Feed";
import { Leaderboard } from "./views/Leaderboard";
import { Detail } from "./views/Detail";
import { Stats } from "./views/Stats";
import { Profile } from "./views/Profile";
import { Sessions } from "./views/Sessions";

export default function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <HashRouter>
          <Routes>
            <Route element={<Layout />}>
              <Route path="/pipeline" element={<Pipeline />} />
              <Route path="/feed" element={<Feed />} />
              <Route path="/leaderboard" element={<Leaderboard />} />
              <Route path="/detail/:id" element={<Detail />} />
              <Route path="/stats" element={<Stats />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/sessions" element={<Sessions />} />
              <Route path="*" element={<Navigate to="/pipeline" replace />} />
            </Route>
          </Routes>
        </HashRouter>
      </ToastProvider>
    </ErrorBoundary>
  );
}
