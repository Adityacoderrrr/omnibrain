import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Brain,
  Zap,
  Shield,
  Database,
  GitMerge,
  Activity,
  ArrowRight,
  Layers,
  Sparkles,
  FileText,
  Search,
  CheckCircle2,
  Terminal,
  Cpu,
  Eye,
  Code
} from 'lucide-react';
import BrainCanvas from './BrainCanvas';

export default function LandingPage({ onLaunchDashboard }) {
  const [typedText, setTypedText] = useState('');
  const fullText = 'Enterprise Multi-Agent Intelligence Platform';

  useEffect(() => {
    let index = 0;
    const interval = setInterval(() => {
      if (index <= fullText.length) {
        setTypedText(fullText.slice(0, index));
        index++;
      } else {
        clearInterval(interval);
      }
    }, 60);
    return () => clearInterval(interval);
  }, []);

  const features = [
    {
      icon: GitMerge,
      title: 'Multi-Agent Orchestration',
      description: 'LangGraph-powered supervisor dynamic routing across Search, Vision OCR, and SQL specialists in parallel.',
      color: 'from-blue-500 to-indigo-600',
    },
    {
      icon: Search,
      title: 'Advanced Hybrid RAG',
      description: 'Vector Cosine + BM25 Sparse search with Reciprocal Rank Fusion (RRF), parent chunk retrieval, and context compression.',
      color: 'from-indigo-500 to-purple-600',
    },
    {
      icon: Database,
      title: 'Universal Knowledge Base',
      description: 'Native parsing and indexing for PDF, DOCX, PPTX, Markdown, TXT, and Images with metadata tagging.',
      color: 'from-purple-500 to-pink-600',
    },
    {
      icon: Activity,
      title: 'LangSmith Observability',
      description: 'Node execution timelines, state diffs, prompt/completion token breakdown, latency tracking, and cost analytics.',
      color: 'from-cyan-500 to-blue-600',
    },
    {
      icon: Shield,
      title: 'Enterprise Security',
      description: 'Role-based access control, SQL AST safety validation, encrypted session persistence, and full audit logs.',
      color: 'from-emerald-500 to-teal-600',
    },
    {
      icon: Sparkles,
      title: 'Self-Reflection & Citations',
      description: 'Automated groundedness verification, exact page/snippet citations, and follow-up question generation.',
      color: 'from-amber-500 to-orange-600',
    },
  ];

  const techStack = [
    { name: 'FastAPI', category: 'Backend Engine' },
    { name: 'LangGraph', category: 'Agentic Graph' },
    { name: 'Qdrant Vector DB', category: 'Embedding Store' },
    { name: 'BM25 Engine', category: 'Sparse Search' },
    { name: 'React + Vite', category: 'Frontend SPA' },
    { name: 'Tailwind CSS', category: 'Styling Framework' },
    { name: 'Framer Motion', category: 'Micro-Animations' },
    { name: 'Docker', category: 'Containerization' },
  ];

  return (
    <div className="relative min-h-screen bg-[#080c14] text-slate-100 overflow-x-hidden">
      <BrainCanvas />

      {/* Navigation Header */}
      <header className="sticky top-0 z-50 glass-panel border-b border-white/10 px-6 py-4 backdrop-blur-md">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3 cursor-pointer">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-purple-600 p-0.5 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <div className="w-full h-full bg-[#080c14] rounded-[10px] flex items-center justify-center">
                <Brain className="w-6 h-6 text-blue-400 animate-pulse" />
              </div>
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-blue-400">
                OmniBrain
              </span>
              <span className="ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30">
                v1.0 Enterprise
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <button
              onClick={onLaunchDashboard}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 font-semibold text-sm shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all duration-300 flex items-center space-x-2"
            >
              <span>Launch Platform</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 pt-20 pb-16 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="space-y-6"
        >
          <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full glass-panel border border-blue-500/30 text-blue-300 text-xs font-semibold tracking-wide uppercase">
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            <span>Next-Gen Enterprise AI Architecture</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight max-w-4xl mx-auto leading-tight">
            The Autonomous{' '}
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 text-glow">
              OmniBrain
            </span>
          </h1>

          <p className="text-xl md:text-2xl text-slate-300 font-mono h-12 max-w-3xl mx-auto">
            {typedText}
            <span className="animate-pulse text-blue-400">|</span>
          </p>

          <p className="text-slate-400 max-w-2xl mx-auto text-base md:text-lg">
            Orchestrate specialized Search, Vision OCR, and SQL agents over multi-format documents with hybrid vector-BM25 retrieval, real-time token streaming, and full execution observability.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <button
              onClick={onLaunchDashboard}
              className="w-full sm:w-auto px-8 py-4 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 font-bold text-base shadow-xl shadow-blue-500/30 hover:shadow-blue-500/50 transition-all duration-300 flex items-center justify-center space-x-3 group"
            >
              <span>Explore Workspace</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </motion.div>
      </section>

      {/* Feature Grid */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 py-16">
        <div className="text-center space-y-4 mb-16">
          <h2 className="text-3xl md:text-4xl font-bold">Production-Grade AI Capabilities</h2>
          <p className="text-slate-400 max-w-xl mx-auto">
            Designed for high-throughput enterprise RAG, multi-agent collaboration, and complete state explainability.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: idx * 0.1 }}
              className="glass-panel-interactive p-8 rounded-2xl border border-white/10 space-y-4"
            >
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-tr ${feature.color} p-3 text-white shadow-lg`}>
                <feature.icon className="w-full h-full" />
              </div>
              <h3 className="text-xl font-bold text-slate-100">{feature.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Architecture Interactive Flow */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 py-16">
        <div className="glass-panel rounded-3xl p-8 md:p-12 border border-white/10 space-y-8">
          <div className="text-center space-y-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-blue-400">Agentic DAG Pipeline</span>
            <h3 className="text-3xl font-bold">StateGraph Workflow Architecture</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
            <div className="glass-panel p-6 rounded-2xl border-blue-500/30 space-y-2">
              <Cpu className="w-8 h-8 text-blue-400 mx-auto" />
              <div className="font-bold text-slate-200">1. Supervisor</div>
              <div className="text-xs text-slate-400">Intent classification & parallel routing</div>
            </div>
            <div className="glass-panel p-6 rounded-2xl border-purple-500/30 space-y-2">
              <Search className="w-8 h-8 text-purple-400 mx-auto" />
              <div className="font-bold text-slate-200">2. Specialists</div>
              <div className="text-xs text-slate-400">Hybrid Search, Vision OCR, SQL execution</div>
            </div>
            <div className="glass-panel p-6 rounded-2xl border-cyan-500/30 space-y-2">
              <GitMerge className="w-8 h-8 text-cyan-400 mx-auto" />
              <div className="font-bold text-slate-200">3. Reducer</div>
              <div className="text-xs text-slate-400">Synthesis, fact dedup, confidence blend</div>
            </div>
            <div className="glass-panel p-6 rounded-2xl border-emerald-500/30 space-y-2">
              <Eye className="w-8 h-8 text-emerald-400 mx-auto" />
              <div className="font-bold text-slate-200">4. Reflection</div>
              <div className="text-xs text-slate-400">Groundedness verification & citations</div>
            </div>
          </div>
        </div>
      </section>

      {/* Tech Stack Footer */}
      <footer className="relative z-10 border-t border-white/10 glass-panel py-12 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center space-x-3">
            <Brain className="w-6 h-6 text-blue-400" />
            <span className="font-bold text-slate-200">OmniBrain Enterprise</span>
            <span className="text-xs text-slate-500">© 2026 OmniBrain AI</span>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3">
            {techStack.map((tech, i) => (
              <span key={i} className="text-xs px-3 py-1 rounded-full glass-panel border border-white/10 text-slate-400">
                {tech.name}
              </span>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
