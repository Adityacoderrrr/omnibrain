import React, { useState } from 'react';
import {
  MessageSquare,
  Database,
  BarChart3,
  Activity,
  Settings,
  Brain,
  ChevronRight,
  FolderKanban,
  Cpu,
  Layers,
  Sparkles,
  Home,
  LogOut,
  ShieldCheck
} from 'lucide-react';
import ChatPage from './ChatPage';
import KnowledgeBasePage from './KnowledgeBasePage';
import AnalyticsPage from './AnalyticsPage';
import TracePage from './TracePage';
import SettingsPage from './SettingsPage';

export default function Dashboard({ onGoLanding }) {
  const [activeTab, setActiveTab] = useState('chat');
  const [selectedDocId, setSelectedDocId] = useState(null);

  const navItems = [
    { id: 'chat', label: 'Chat Assistant', icon: MessageSquare, badge: 'SSE Stream' },
    { id: 'kb', label: 'Knowledge Base', icon: Database, badge: '6 Formats' },
    { id: 'analytics', label: 'Analytics', icon: BarChart3, badge: 'Live Metrics' },
    { id: 'tracing', label: 'Trace Telemetry', icon: Activity, badge: 'LangSmith' },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="flex h-screen bg-[#080c14] text-slate-100 overflow-hidden font-['Plus_Jakarta_Sans',sans-serif]">
      {/* Sidebar */}
      <aside className="w-64 glass-panel border-r border-white/10 flex flex-col justify-between p-4 z-20">
        <div className="space-y-6">
          {/* Brand Header */}
          <div
            onClick={onGoLanding}
            className="flex items-center space-x-3 px-3 py-2 cursor-pointer hover:bg-white/5 rounded-xl transition-all"
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-purple-600 p-0.5 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <div className="w-full h-full bg-[#080c14] rounded-[10px] flex items-center justify-center">
                <Brain className="w-5 h-5 text-blue-400" />
              </div>
            </div>
            <div>
              <div className="font-bold text-sm text-slate-100 tracking-wide">OmniBrain AI</div>
              <div className="text-[10px] font-mono text-blue-400 flex items-center space-x-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                <span>System Ready</span>
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-gradient-to-r from-blue-600/30 to-purple-600/30 text-blue-300 border border-blue-500/40 shadow-lg shadow-blue-500/10'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-white/10 text-slate-300">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Footer info & Home button */}
        <div className="space-y-3 pt-4 border-t border-white/10">
          <button
            onClick={onGoLanding}
            className="w-full flex items-center space-x-3 px-3.5 py-2 rounded-xl text-xs text-slate-400 hover:text-slate-200 hover:bg-white/5 transition-all"
          >
            <Home className="w-4 h-4 text-slate-400" />
            <span>Back to Landing Page</span>
          </button>

          <div className="glass-panel p-3 rounded-xl border border-white/10 space-y-1">
            <div className="flex items-center justify-between text-xs text-slate-300 font-semibold">
              <span>Model Active</span>
              <span className="text-emerald-400 text-[10px] font-mono">Gemini 3.6 Flash</span>
            </div>
            <div className="text-[10px] text-slate-500">Vector Collection: omnibrain_text</div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative z-10">
        {activeTab === 'chat' && <ChatPage activeDocId={selectedDocId} />}
        {activeTab === 'kb' && <KnowledgeBasePage onSelectDoc={(id) => { setSelectedDocId(id); setActiveTab('chat'); }} />}
        {activeTab === 'analytics' && <AnalyticsPage />}
        {activeTab === 'tracing' && <TracePage />}
        {activeTab === 'settings' && <SettingsPage />}
      </main>
    </div>
  );
}
