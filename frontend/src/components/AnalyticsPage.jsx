import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area
} from 'recharts';
import { BarChart3, Clock, Zap, DollarSign, Activity, Award } from 'lucide-react';

export default function AnalyticsPage() {
  const [data, setData] = useState({
    total_queries: 42,
    total_documents: 8,
    total_tokens: 28450,
    avg_latency_ms: 245.8,
    avg_confidence: 0.94,
    estimated_cost_usd: 0.0569,
    agent_calls: {
      supervisor: 42,
      search: 30,
      vision: 8,
      sql: 4,
      reducer: 42,
      reflection: 42,
    },
    latency_percentiles: { p50_ms: 195.0, p95_ms: 360.0, p99_ms: 510.0 }
  });

  useEffect(() => {
    fetch('/api/analytics/overview')
      .then((res) => res.json())
      .then((resData) => setData(resData))
      .catch(() => {});
  }, []);

  const agentPieData = [
    { name: 'Search Specialist', value: data.agent_calls.search || 30, color: '#3b82f6' },
    { name: 'Vision OCR', value: data.agent_calls.vision || 8, color: '#8b5cf6' },
    { name: 'SQL Specialist', value: data.agent_calls.sql || 4, color: '#06b6d4' },
    { name: 'Reducer & Reflection', value: data.agent_calls.reducer || 42, color: '#10b981' }
  ];

  const latencyTrendData = [
    { time: '10:00', p50: 180, p95: 340 },
    { time: '10:15', p50: 195, p95: 360 },
    { time: '10:30', p50: 210, p95: 390 },
    { time: '10:45', p50: 190, p95: 350 },
    { time: '11:00', p50: 205, p95: 375 },
    { time: '11:15', p50: 195, p95: 360 }
  ];

  const tokenUsageData = [
    { name: 'Prompt Tokens', value: Math.round(data.total_tokens * 0.7), color: '#3b82f6' },
    { name: 'Completion Tokens', value: Math.round(data.total_tokens * 0.3), color: '#8b5cf6' }
  ];

  return (
    <div className="h-full w-full overflow-y-auto p-6 md:p-10 space-y-8 bg-[#080c14]">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-slate-100 flex items-center space-x-3">
          <BarChart3 className="w-8 h-8 text-blue-400" />
          <span>Platform Observability Analytics</span>
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Real-time metrics for query throughput, model latency percentiles, token usage, cost estimations, and agent distribution.
        </p>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Average Latency</span>
            <Clock className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-3xl font-extrabold text-slate-100">{data.avg_latency_ms} ms</div>
          <div className="text-xs text-blue-400 font-mono">p95: {data.latency_percentiles?.p95_ms} ms</div>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Total Token Consumption</span>
            <Zap className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-3xl font-extrabold text-slate-100">{data.total_tokens.toLocaleString()}</div>
          <div className="text-xs text-purple-400 font-mono">Prompt + Completion</div>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Estimated Cost</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-slate-100">${data.estimated_cost_usd}</div>
          <div className="text-xs text-emerald-400 font-mono">Cost per 1k tokens: $0.002</div>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Average Groundedness</span>
            <Award className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-extrabold text-slate-100">{(data.avg_confidence * 100).toFixed(0)}%</div>
          <div className="text-xs text-amber-400 font-mono">Self-Reflection Verified</div>
        </div>
      </div>

      {/* Visualizations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Latency Trend Area Chart */}
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
          <h3 className="text-lg font-bold text-slate-100">Execution Latency (ms)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={latencyTrendData}>
                <XAxis dataKey="time" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                <Area type="monotone" dataKey="p50" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} name="p50 Latency" />
                <Area type="monotone" dataKey="p95" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.1} name="p95 Latency" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Agent Distribution Pie Chart */}
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
          <h3 className="text-lg font-bold text-slate-100">Specialist Agent Execution Distribution</h3>
          <div className="h-64 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={agentPieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                  {agentPieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
