import React, { useState, useEffect } from 'react';
import {
  Activity,
  GitMerge,
  Search,
  Cpu,
  Eye,
  CheckCircle2,
  Clock,
  Code,
  ArrowRight,
  Database,
  Layers,
  Sparkles,
  RefreshCw,
  HelpCircle,
  FileQuestion
} from 'lucide-react';

export default function TracePage() {
  const [traces, setTraces] = useState([]);
  const [selectedTraceId, setSelectedTraceId] = useState(null);
  const [selectedNode, setSelectedNode] = useState('supervisor');
  const [loading, setLoading] = useState(true);

  const fetchTraces = () => {
    setLoading(true);
    fetch('/api/tracing')
      .then((res) => res.json())
      .then((data) => {
        if (data.traces && data.traces.length > 0) {
          setTraces(data.traces);
          if (!selectedTraceId) {
            setSelectedTraceId(data.traces[data.traces.length - 1].request_id);
          }
        } else {
          setTraces([]);
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    fetchTraces();
  }, []);

  const selectedTrace = traces.find((t) => t.request_id === selectedTraceId) || traces[0] || null;

  const specialistAgents = [
    { id: 'supervisor', name: 'Supervisor Router', icon: Cpu, color: 'text-blue-400 border-blue-500/40 bg-blue-500/10' },
    { id: 'search', name: 'Search Specialist', icon: Search, color: 'text-purple-400 border-purple-500/40 bg-purple-500/10' },
    { id: 'vision', name: 'Vision Specialist', icon: Layers, color: 'text-pink-400 border-pink-500/40 bg-pink-500/10' },
    { id: 'sql', name: 'SQL Specialist', icon: Database, color: 'text-cyan-400 border-cyan-500/40 bg-cyan-500/10' },
    { id: 'reducer', name: 'Master Reducer', icon: GitMerge, color: 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10' },
    { id: 'reflection', name: 'Self-Reflection', icon: Eye, color: 'text-amber-400 border-amber-500/40 bg-amber-500/10' },
  ];

  const activeNodeDetail = selectedTrace?.trace_details?.[selectedNode] || {
    status: selectedTrace ? (selectedTrace.trace_details?.[selectedNode] ? 'EXECUTED' : 'NOT_INVOKED_FOR_QUERY') : 'NOT_AVAILABLE',
    info: `Node '${selectedNode}' was ${selectedTrace?.trace_details?.[selectedNode] ? 'executed' : 'bypassed according to supervisor routing decisions'}.`
  };

  return (
    <div className="h-full w-full overflow-y-auto p-6 md:p-10 space-y-8 bg-[#080c14]">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-100 flex items-center space-x-3">
            <Activity className="w-8 h-8 text-blue-400" />
            <span>Execution Graph Trace Telemetry</span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Real-time LangSmith / LangFuse style state graph inspection. Inspect DAG execution timelines, routing decisions, node payloads, and token consumption.
          </p>
        </div>

        <button
          onClick={fetchTraces}
          className="px-4 py-2 rounded-xl glass-panel hover:bg-white/10 text-xs font-semibold text-slate-300 flex items-center space-x-2 border border-white/10"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Traces</span>
        </button>
      </div>

      {traces.length === 0 ? (
        <div className="glass-panel p-12 rounded-3xl border border-white/10 text-center space-y-4 max-w-2xl mx-auto">
          <div className="w-16 h-16 rounded-2xl bg-blue-500/10 text-blue-400 flex items-center justify-center mx-auto border border-blue-500/20">
            <FileQuestion className="w-8 h-8" />
          </div>
          <h3 className="text-xl font-bold text-slate-100">No Query Traces Recorded Yet</h3>
          <p className="text-sm text-slate-400 leading-relaxed">
            Execute a query in the Chat Assistant tab to generate live execution traces across the Supervisor, Specialist Agents, Reducer, and Self-Reflection nodes.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Query Selector Bar */}
          <div className="glass-panel p-4 rounded-2xl border border-white/10 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-center space-x-3 w-full md:w-auto">
              <span className="text-xs font-semibold text-slate-400 whitespace-nowrap">Select Trace:</span>
              <select
                value={selectedTraceId || ''}
                onChange={(e) => setSelectedTraceId(e.target.value)}
                className="bg-slate-900 border border-blue-500/30 text-blue-300 rounded-xl px-3 py-1.5 text-xs font-medium focus:outline-none focus:border-blue-400 w-full md:w-96 truncate"
              >
                {traces.map((t) => (
                  <option key={t.request_id} value={t.request_id}>
                    [{t.request_id.slice(0, 10)}] {t.question}
                  </option>
                ))}
              </select>
            </div>

            {selectedTrace && (
              <div className="flex items-center space-x-4 text-xs font-mono text-slate-400">
                <span>Latency: <strong className="text-emerald-400">{selectedTrace.execution_time_ms || 0} ms</strong></span>
                <span>•</span>
                <span>Tokens: <strong className="text-purple-400">{selectedTrace.token_analytics?.total_tokens || 0}</strong></span>
              </div>
            )}
          </div>

          {/* Interactive DAG Nodes Flow */}
          {selectedTrace && (
            <div className="space-y-6">
              <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span className="font-semibold uppercase tracking-wider text-blue-400">Pipeline State Nodes</span>
                  <span>Session: <span className="font-mono text-slate-300">{selectedTrace.session_id}</span></span>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                  {specialistAgents.map((node) => {
                    const Icon = node.icon;
                    const isSelected = selectedNode === node.id;
                    const hasExecuted = !!selectedTrace.trace_details?.[node.id];
                    const nodeLatency = selectedTrace.trace_details?.[node.id]?.execution_time_ms || 0;

                    return (
                      <button
                        key={node.id}
                        onClick={() => setSelectedNode(node.id)}
                        className={`p-4 rounded-xl border text-left transition-all duration-200 ${
                          isSelected
                            ? 'bg-blue-600/30 border-blue-400 text-slate-100 shadow-lg shadow-blue-500/20 scale-[1.02]'
                            : hasExecuted
                            ? 'glass-panel border-white/10 text-slate-300 hover:border-blue-500/40'
                            : 'bg-slate-900/30 border-white/5 text-slate-500 opacity-60'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <Icon className={`w-4 h-4 ${hasExecuted ? node.color.split(' ')[0] : 'text-slate-500'}`} />
                          {hasExecuted ? (
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                          ) : (
                            <span className="text-[9px] text-slate-500">Bypassed</span>
                          )}
                        </div>
                        <div className="font-bold text-xs truncate">{node.name}</div>
                        <div className="text-[10px] font-mono text-slate-400 mt-1">
                          {hasExecuted ? `${nodeLatency} ms` : 'N/A'}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Node Inspection & Step Logs Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Node Structured Details */}
                <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
                  <h3 className="text-sm font-bold text-slate-100 flex items-center space-x-2">
                    <Code className="w-4 h-4 text-blue-400" />
                    <span>Selected Node Telemetry: [{selectedNode.toUpperCase()}]</span>
                  </h3>

                  <div className="bg-slate-950 p-4 rounded-xl border border-white/10 text-xs font-mono space-y-2 overflow-x-auto max-h-96">
                    <pre className="text-slate-300 leading-relaxed">
                      {JSON.stringify(activeNodeDetail, null, 2)}
                    </pre>
                  </div>
                </div>

                {/* Step Trace Logs */}
                <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
                  <h3 className="text-sm font-bold text-slate-100 flex items-center space-x-2">
                    <Activity className="w-4 h-4 text-purple-400" />
                    <span>Agent Step Execution Logs</span>
                  </h3>

                  <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                    {selectedTrace.agent_trace && selectedTrace.agent_trace.length > 0 ? (
                      selectedTrace.agent_trace.map((step, idx) => (
                        <div key={idx} className="p-3 rounded-xl bg-slate-900/60 border border-white/5 text-xs text-blue-300 font-mono flex items-start space-x-2">
                          <ArrowRight className="w-3.5 h-3.5 text-blue-400 flex-shrink-0 mt-0.5" />
                          <span>{step}</span>
                        </div>
                      ))
                    ) : (
                      <div className="text-xs text-slate-500 italic p-3">No individual steps recorded.</div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
