import { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './components/layout/AppLayout';

// Pages
import Dashboard from './pages/dashboard/Dashboard';
import MissionControl from './pages/dashboard/MissionControl';
import Onboarding from './pages/onboarding/Onboarding';
import Settings from './pages/settings/Settings';
import Help from './pages/help/Help';
import Chat from './pages/chat/Chat';
import Tools from './pages/tools/Tools';
import Apps from './pages/apps/Apps';
import LLM from './pages/llm/LLM';
import Analytics from './pages/analytics/Analytics';
import Viz from './pages/viz/Viz';
import MapPage from './pages/map/Map';

import ErrorBoundary from './components/common/ErrorBoundary';

function App() {
    useEffect(() => {
        console.log('[App] Substrate Initialized at', new Date().toISOString());
    }, []);

    return (
        <ErrorBoundary>
            <AppLayout>
                <Routes>
                    <Route path="/" element={<Navigate to="/mission-control" replace />} />
                    <Route path="/mission-control" element={<MissionControl />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/onboarding" element={<Onboarding />} />
                    <Route path="/analytics" element={<Analytics />} />
                    <Route path="/chat" element={<Chat />} />
                    <Route path="/tools" element={<Tools />} />
                    <Route path="/apps" element={<Apps />} />
                    <Route path="/llm" element={<LLM />} />
                    <Route path="/settings" element={<Settings />} />
                    <Route path="/help" element={<Help />} />
                    <Route path="/viz" element={<Viz />} />
                    <Route path="/map" element={<MapPage />} />

                    {/* Fallback */}
                    <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Routes>
            </AppLayout>
        </ErrorBoundary>
    );
}

export default App;
