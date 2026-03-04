import { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './components/layout/AppLayout';

// Pages
import Dashboard from './pages/dashboard/Dashboard';
import Onboarding from './pages/onboarding/Onboarding';
import Settings from './pages/settings/Settings';
import Help from './pages/help/Help';
import Chat from './pages/chat/Chat';
import Tools from './pages/tools/Tools';
import Apps from './pages/apps/Apps';
import LLM from './pages/llm/LLM';
import Analytics from './pages/analytics/Analytics';

function App() {
    return (
        <AppLayout>
            <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/onboarding" element={<Onboarding />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/chat" element={<Chat />} />
                <Route path="/tools" element={<Tools />} />
                <Route path="/apps" element={<Apps />} />
                <Route path="/llm" element={<LLM />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/help" element={<Help />} />

                {/* Fallback */}
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </AppLayout>
    );
}

export default App;
