import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import ErrorBoundary from "./components/common/ErrorBoundary";
import AppLayout from "./components/layout/AppLayout";
import Analytics from "./pages/analytics/Analytics";
import Apps from "./pages/apps/Apps";
import Chat from "./pages/chat/Chat";
// Pages
import Dashboard from "./pages/dashboard/Dashboard";
import MissionControl from "./pages/dashboard/MissionControl";
import Peripherals from "./pages/dashboard/Peripherals";
import Workflows from "./pages/dashboard/Workflows";
import DiagnosticsPage from "./pages/diagnostics/Diagnostics";
import Help from "./pages/help/Help";
import LidarAddonPage from "./pages/lidar/LidarAddon";
import LidarMapPage from "./pages/lidar/LidarMap";
import LLM from "./pages/llm/LLM";
import MapPage from "./pages/map/Map";
import MovementPage from "./pages/movement/Movement";
import Onboarding from "./pages/onboarding/Onboarding";
import SensorsPage from "./pages/sensors/Sensors";
import Settings from "./pages/settings/Settings";
import Tools from "./pages/tools/Tools";
import Voice from "./pages/voice/Voice";
import VoiceUpgrade from "./pages/voice/VoiceUpgrade";
import Viz from "./pages/viz/Viz";

function App() {
  useEffect(() => {
    console.log("[App] Substrate Initialized at", new Date().toISOString());
  }, []);

  return (
    <ErrorBoundary>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/mission-control" element={<MissionControl />} />
          <Route path="/onboarding" element={<Onboarding />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/tools" element={<Tools />} />
          <Route path="/apps" element={<Apps />} />
          <Route path="/llm" element={<LLM />} />
          <Route path="/peripherals" element={<Peripherals />} />
          <Route path="/workflows" element={<Workflows />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/help" element={<Help />} />
          <Route path="/viz" element={<Viz />} />
          <Route path="/map" element={<MapPage />} />
          <Route path="/lidar-map" element={<LidarMapPage />} />
          <Route path="/lidar-addon" element={<LidarAddonPage />} />
          <Route path="/movement" element={<MovementPage />} />
          <Route path="/sensors" element={<SensorsPage />} />
          <Route path="/diagnostics" element={<DiagnosticsPage />} />
          <Route path="/peripherals" element={<Peripherals />} />

          <Route path="/voice" element={<Voice />} />
          <Route path="/voice-upgrade" element={<VoiceUpgrade />} />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AppLayout>
    </ErrorBoundary>
  );
}

export default App;
