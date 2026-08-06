import React, { useState } from 'react';
import LandingPage from './components/LandingPage';
import Dashboard from './components/Dashboard';

export default function App() {
  const [view, setView] = useState('landing'); // 'landing' | 'dashboard'

  return (
    <div className="min-h-screen bg-[#080c14] text-slate-100 font-['Plus_Jakarta_Sans',sans-serif]">
      {view === 'landing' ? (
        <LandingPage onLaunchDashboard={() => setView('dashboard')} />
      ) : (
        <Dashboard onGoLanding={() => setView('landing')} />
      )}
    </div>
  );
}
