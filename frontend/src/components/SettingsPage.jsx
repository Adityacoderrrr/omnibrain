import React, { useState } from 'react';
import { Settings, Cpu, Database, Sliders, Key, Save, Check } from 'lucide-react';

export default function SettingsPage() {
  const [model, setModel] = useState('gemini-3.6-flash');
  const [chunkSize, setChunkSize] = useState(1000);
  const [topK, setTopK] = useState(5);
  const [bm25Weight, setBm25Weight] = useState(0.5);
  const [vectorWeight, setVectorWeight] = useState(0.5);
  const [openaiKey, setOpenaiKey] = useState('');
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="h-full w-full overflow-y-auto p-6 md:p-10 space-y-8 bg-[#080c14]">
      <div>
        <h1 className="text-3xl font-extrabold text-slate-100 flex items-center space-x-3">
          <Settings className="w-8 h-8 text-blue-400" />
          <span>Platform Settings & Configurations</span>
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Customize LLM foundation models, hybrid retriever weights, chunking parameters, and API keys.
        </p>
      </div>

      <div className="max-w-3xl space-y-6">
        {/* Model Selection */}
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
          <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-blue-400" />
            <span>LLM Foundation Model</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <button
              onClick={() => setModel('gemini-3.6-flash')}
              className={`p-4 rounded-xl border text-left transition-all ${
                model === 'gemini-3.6-flash'
                  ? 'bg-blue-600/30 border-blue-400 text-slate-100'
                  : 'bg-slate-900/60 border-white/10 text-slate-400 hover:text-slate-200'
              }`}
            >
              <div className="font-bold text-sm">Gemini 3.6 Flash (High)</div>
              <div className="text-xs text-slate-500 mt-1">Ultra-fast multi-modal reasoning</div>
            </button>

            <button
              onClick={() => setModel('gpt-4o')}
              className={`p-4 rounded-xl border text-left transition-all ${
                model === 'gpt-4o'
                  ? 'bg-blue-600/30 border-blue-400 text-slate-100'
                  : 'bg-slate-900/60 border-white/10 text-slate-400 hover:text-slate-200'
              }`}
            >
              <div className="font-bold text-sm">OpenAI GPT-4o</div>
              <div className="text-xs text-slate-500 mt-1">Complex agentic synthesis</div>
            </button>
          </div>
        </div>

        {/* RAG & Retriever Parameters */}
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
          <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
            <Sliders className="w-4 h-4 text-purple-400" />
            <span>Hybrid Retriever & Chunking Settings</span>
          </h3>

          <div className="space-y-4 text-sm">
            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Vector Top-K Chunks: {topK}</span>
              </div>
              <input
                type="range"
                min="1"
                max="20"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="w-full accent-blue-500"
              />
            </div>

            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Max Chunk Character Length: {chunkSize}</span>
              </div>
              <input
                type="range"
                min="500"
                max="3000"
                step="100"
                value={chunkSize}
                onChange={(e) => setChunkSize(Number(e.target.value))}
                className="w-full accent-purple-500"
              />
            </div>
          </div>
        </div>

        {/* API Key Management */}
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
          <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
            <Key className="w-4 h-4 text-emerald-400" />
            <span>API Keys & Credentials</span>
          </h3>

          <div>
            <label className="text-xs text-slate-400 block mb-1">OpenAI API Key</label>
            <input
              type="password"
              value={openaiKey}
              onChange={(e) => setOpenaiKey(e.target.value)}
              placeholder="sk-proj-..."
              className="w-full bg-slate-900 border border-white/10 rounded-xl px-4 py-2 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-blue-400 font-mono"
            />
          </div>
        </div>

        <button
          onClick={handleSave}
          className="px-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 font-bold text-sm shadow-lg shadow-blue-500/25 flex items-center space-x-2"
        >
          {saved ? <Check className="w-4 h-4 text-emerald-300" /> : <Save className="w-4 h-4" />}
          <span>{saved ? 'Settings Saved!' : 'Save Settings'}</span>
        </button>
      </div>
    </div>
  );
}
