import React, { useState, useEffect } from 'react';
import { Activity, GitMerge, Search, Cpu, Eye, CheckCircle2, Clock, Code, ArrowRight } from 'lucide-react';

export default function TracePage() {
  const [traces, setTraces] = useState([]);
  const [selectedTrace, setSelectedTrace] = useState(null);
  const [selectedNode, setSelectedNode] = useState('supervisor');

  useEffect(() => {
    fetch('/api/tracing')
      .then((res) => res.json())
      .then((data) => {
        if (data.traces && data.traces.length > 0) {
          setTraces(data.traces);
          setSelectedTrace(data.traces[0]);
        } else {
          // Synthetic trace demo fallback
          const demoTrace = {
            request_id: 'req_8f1a23e',
            session_id: 'sess_financial_2026',
            timestamp: new Date().toISOString(),
            question: 'What is the YoY revenue growth in the annual report?',
            answer: 'According to the annual report, YoY revenue growth was 15% with cloud subscription revenue driving the highest margins.',
            agent_trace: [
              'Supervisor: Classified query intent as TEXT_SEARCH',
              'Search Agent: Retrieved 5 text chunks from Qdrant with hybrid RRF fusion',
              'Reducer: Consolidated final response and deduplicated citations',
              'Self-Reflection: Verified answer groundedness (Score: 0.94)',
            ],
            trace_details: {
              supervisor: {
                selected_agent: 'search',
                selected_agents: ['search'],
                routing_reasoning: 'Query requires narrative document text retrieval.',
                confidence: 0.96,
                execution_time_ms: 14.2,
              },
              search: {
                collection: 'omnibrain_text_chunks',
                hybrid_rrf_k: 60,
                chunks_searched: 352,
                top_similarity: 0.96,
                retrieved_count: 5,
                execution_time_ms: 135.8,
              },
              reducer: {
                inputs: ['search'],
                conflict_detection: 'None',
                final_response: 'YoY revenue growth was 15%.',
                confidence: 0.94,
                execution_time_ms: 62.4,
              },
              reflection: {
                groundedness_score: 0.94,
                verification_status: 'PASSED',
                citation_count: 2,
                critique: 'Answer is factually grounded in retrieved source context.',
                execution_time_ms: 18.5,
              },
            },
            token_analytics: { prompt_tokens: 420, completion_tokens: 180, total_tokens: 600 },
            execution_time_ms: 230.9,
          };
          setTraces([demoTrace]);
          setSelectedTrace(demoTrace);
        }
      })
      .catch(() => {});
  }, []);

  const nodes = [
    { id: 'supervisor', name: 'Supervisor Node', icon: Cpu, color: 'text-blue-400 border-blue-500/40 bg-blue-500/10' },
    { id: 'search', name: 'Search Specialist', icon: Search, color: 'text-purple-400 border-purple-500/40 bg-purple-500/10' },
    { id: 'reducer', name: 'Master Reducer', icon: GitMerge, color: 'text-cyan-400 border-cyan-500/40 bg-cyan-500/10' },
    { id: 'reflection', name: 'Self-Reflection', icon: Eye, color: 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10' },
  ];

  const activeNodeDetail = selectedTrace?.trace_details?.[selectedNode] || {};

  return (
    <div className="h-full w-full overflow-y-auto p-6 md:p-10 space-y-8 bg-[#080c14]">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-slate-100 flex items-center space-x-3">
          <Activity className="w-8 h-8 text-blue-400" />
          <span>Execution Graph Trace Telemetry</span>
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          LangSmith / LangFuse style state graph inspection. Click any node in the execution pipeline to view state snapshots, tokens, and node reasoning.
        </p>
      </div>

      {/* Main Content Layout */}
      {selectedTrace && (
        <div className="space-y-6">
          {/* Interactive DAG Pipeline Flow */}
          <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>Request ID: <span className="font-mono text-blue-300">{selectedTrace.request_id}</span></span>
              <span>Total Latency: <span className="font-mono text-emerald-400">{selectedTrace.execution_time_ms} ms</span></span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {nodes.map((node) => {
                const Icon = node.icon;
                const isSelected = selectedNode === node.id;
                return (
                  <button
                    key={node.id}
                    onClick={() => setSelectedNode(node.id)}
                    className={`p-5 rounded-2xl border text-left transition-all duration-200 ${
                      isSelected
                        ? 'bg-blue-600/30 border-blue-400 text-slate-100 shadow-lg shadow-blue-500/20 scale-[1.02]'
                        : 'glass-panel border-white/10 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <Icon className={`w-5 h-5 ${node.color.split(' ')[0]}`} />
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    </div>
                    <div className="font-bold text-sm">{node.name}</div>
                    <div className="text-[10px] font-mono text-slate-500 mt-1">
                      {selectedTrace.trace_details?.[node.id]?.execution_time_ms || 25} ms
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Node Execution Inspection Panel */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
              <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
                <Code className="w-4 h-4 text-blue-400" />
                <span>Selected Node Details: [{selectedNode.toUpperCase()}]</span>
              </h3>

              <div className="bg-slate-950 p-4 rounded-xl border border-white/10 text-xs font-mono space-y-2 overflow-x-auto">
                <pre className="text-slate-300">
                  {JSON.stringify(activeNodeDetail, null, 2)}
                </pre>
              </div>
            </div>

            <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
              <h3 className="text-base font-bold text-slate-100">Step Trace Logs</h3>
              <div className="space-y-2">
                {selectedTrace.agent_trace.map((step, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-slate-900/60 border border-white/5 text-xs text-blue-300 font-mono flex items-center space-x-2">
                    <ArrowRight className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                    <span>{step}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
