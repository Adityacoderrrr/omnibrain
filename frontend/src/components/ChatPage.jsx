import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  Bot,
  User,
  Sparkles,
  FileText,
  Copy,
  Check,
  RefreshCw,
  Trash2,
  ChevronRight,
  Zap,
  Activity,
  Layers,
  Search,
  BookOpen,
  Cpu,
  AlertCircle,
  CheckCircle2,
  GitMerge,
  Eye,
  Database
} from 'lucide-react';

export default function ChatPage({ activeDocId }) {
  const [input, setInput] = useState('');
  const [documentId, setDocumentId] = useState(activeDocId || '');
  const [documentsList, setDocumentsList] = useState([]);
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      text: "Hello! I'm OmniBrain Enterprise AI. Select an uploaded document from your Knowledge Base or query our enterprise SQL database. I orchestrate specialized Search, Vision, and SQL agents with LangGraph to deliver verified, citation-backed answers.",
      confidence: 0.98,
      agentTrace: ['Supervisor: Initialized multi-agent StateGraph pipeline'],
      citations: [],
      followUps: [
        'What are the key conclusions in the uploaded document?',
        'Show me total revenue records from the database.',
        'Summarize the primary sections on page 1.'
      ]
    }
  ]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [copiedId, setCopiedId] = useState(null);
  const [showCitationDrawer, setShowCitationDrawer] = useState(false);
  const [activeCitations, setActiveCitations] = useState([]);
  const messagesEndRef = useRef(null);

  const fetchDocuments = () => {
    fetch('/api/documents')
      .then((res) => res.json())
      .then((data) => {
        if (data.documents && data.documents.length > 0) {
          setDocumentsList(data.documents);
          if (!documentId) {
            setDocumentId(data.documents[0].document_id);
          }
        }
      })
      .catch(() => {});
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  useEffect(() => {
    if (activeDocId) {
      setDocumentId(activeDocId);
    }
  }, [activeDocId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  const handleClearChat = () => {
    setMessages([
      {
        id: 'welcome_reset',
        sender: 'assistant',
        text: "Conversation reset. Ready for your next query.",
        confidence: 1.0,
        agentTrace: ['Supervisor: Ready'],
        citations: [],
        followUps: [
          'What are the key conclusions in the uploaded document?',
          'Show me total revenue records from the database.'
        ]
      }
    ]);
  };

  const handleSend = async (textToSend) => {
    const query = textToSend || input;
    if (!query.trim() || isStreaming) return;

    const targetDocId = documentId || (documentsList[0] ? documentsList[0].document_id : '');

    const userMsgId = `user_${Date.now()}`;
    const assistantMsgId = `asst_${Date.now()}`;

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, sender: 'user', text: query },
      {
        id: assistantMsgId,
        sender: 'assistant',
        text: '',
        isStreaming: true,
        agentTrace: ['Supervisor: Analyzing query intent and selecting agents...'],
        confidence: 0.0,
        citations: [],
        followUps: []
      }
    ]);

    setInput('');
    setIsStreaming(true);

    try {
      // If targetDocId is empty and no document is selected, query using standard query endpoint with fallback
      const response = await fetch('/api/query/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: targetDocId || 'workspace_global',
          question: query,
          session_id: `sess_${Date.now()}`
        })
      });

      if (!response.ok) {
        // Try fallback non-stream query
        const fallbackRes = await fetch('/api/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            document_id: targetDocId || 'workspace_global',
            question: query,
            session_id: `sess_${Date.now()}`
          })
        });

        if (!fallbackRes.ok) {
          const errData = await fallbackRes.json().catch(() => ({}));
          throw new Error(errData.detail || `Server returned HTTP ${fallbackRes.status}`);
        }

        const data = await fallbackRes.json();
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  text: data.answer || "No response generated.",
                  isStreaming: false,
                  confidence: data.confidence_scores?.reducer || 0.90,
                  citations: data.citations || [],
                  agentTrace: data.agent_trace || ['Completed'],
                  followUps: data.follow_up_questions || []
                }
              : msg
          )
        );
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let streamText = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunkStr = decoder.decode(value);
        const lines = chunkStr.split('\n\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.replace('data: ', ''));

              if (data.event === 'step') {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMsgId
                      ? { ...msg, agentTrace: [...msg.agentTrace, data.step] }
                      : msg
                  )
                );
              } else if (data.event === 'token') {
                streamText += data.text;
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMsgId ? { ...msg, text: streamText } : msg
                  )
                );
              } else if (data.event === 'done') {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMsgId
                      ? {
                          ...msg,
                          isStreaming: false,
                          confidence: data.confidence_scores?.reducer || 0.92,
                          citations: data.citations || [],
                          followUps: data.follow_up_questions || []
                        }
                      : msg
                  )
                );
              }
            } catch (e) {}
          }
        }
      }
    } catch (err) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? {
                ...msg,
                text: `Notice: ${err.message || 'Unable to reach backend agent service. Please ensure a document is selected or check backend connectivity.'}`,
                isStreaming: false,
                confidence: 0.0,
                citations: [],
                agentTrace: ['Execution stopped due to connection/document error'],
                followUps: [
                  'How do I upload documents to the Knowledge Base?',
                  'What SQL queries can I run on sales records?'
                ]
              }
            : msg
        )
      );
    } finally {
      setIsStreaming(false);
    }
  };

  const copyToClipboard = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Helper to format text with Markdown bold and code block highlighting
  const renderFormattedText = (rawText) => {
    if (!rawText) return null;
    const lines = rawText.split('\n');

    return (
      <div className="space-y-2">
        {lines.map((line, idx) => {
          if (line.startsWith('### ')) {
            return <h3 key={idx} className="text-base font-bold text-blue-300 pt-2">{line.replace('### ', '')}</h3>;
          }
          if (line.startsWith('## ')) {
            return <h2 key={idx} className="text-lg font-bold text-slate-100 pt-2">{line.replace('## ', '')}</h2>;
          }
          if (line.startsWith('- ') || line.startsWith('* ')) {
            const content = line.substring(2);
            return (
              <div key={idx} className="flex items-start space-x-2 pl-2">
                <span className="text-blue-400 font-bold">•</span>
                <span>{renderInlineFormatting(content)}</span>
              </div>
            );
          }
          if (line.startsWith('```')) {
            return null; // Skip raw backtick lines if encountered alone
          }
          return <p key={idx} className="leading-relaxed">{renderInlineFormatting(line)}</p>;
        })}
      </div>
    );
  };

  const renderInlineFormatting = (str) => {
    if (!str) return '';
    // Format bold **text** and inline `code`
    const parts = str.split(/(\*\*.*?\*\*|`.*?`)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="font-bold text-slate-100">{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code key={i} className="bg-slate-900 px-1.5 py-0.5 rounded text-xs font-mono text-cyan-300 border border-white/10">
            {part.slice(1, -1)}
          </code>
        );
      }
      return part;
    });
  };

  return (
    <div className="flex h-full w-full overflow-hidden bg-[#080c14] relative">
      {/* Active Document Selector Header */}
      <div className="absolute top-0 left-0 right-0 h-14 glass-panel border-b border-white/10 px-6 flex items-center justify-between z-20">
        <div className="flex items-center space-x-3">
          <FileText className="w-4 h-4 text-blue-400" />
          <span className="text-xs font-semibold text-slate-400">Target Document:</span>
          <select
            value={documentId}
            onChange={(e) => setDocumentId(e.target.value)}
            className="bg-slate-900/80 text-xs font-medium text-blue-300 border border-blue-500/30 rounded-lg px-3 py-1.5 focus:outline-none focus:border-blue-400 max-w-xs truncate"
          >
            {documentsList.length === 0 ? (
              <option value="">No documents uploaded (SQL & General query active)</option>
            ) : (
              documentsList.map((doc) => (
                <option key={doc.document_id} value={doc.document_id}>
                  {doc.filename} ({doc.page_count} pgs, {doc.chunk_count} chunks)
                </option>
              ))
            )}
          </select>
        </div>

        <div className="flex items-center space-x-4">
          <button
            onClick={handleClearChat}
            className="text-xs text-slate-400 hover:text-slate-200 flex items-center space-x-1 glass-panel px-2.5 py-1 rounded-lg border border-white/10"
            title="Start New Conversation"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>New Chat</span>
          </button>

          <div className="hidden sm:flex items-center space-x-2 text-xs text-slate-400">
            <span className="flex items-center space-x-1">
              <Cpu className="w-3.5 h-3.5 text-purple-400" />
              <span>Hybrid RAG + SQL</span>
            </span>
            <span className="text-slate-600">|</span>
            <span className="text-emerald-400 font-mono text-[11px]">RRF Active</span>
          </div>
        </div>
      </div>

      {/* Main Chat Stream Container */}
      <div className="flex-1 flex flex-col pt-16 pb-28 overflow-y-auto px-4 md:px-12 max-w-4xl mx-auto w-full space-y-6">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'} space-y-2`}
          >
            <div className="flex items-center space-x-2 text-xs text-slate-400">
              {msg.sender === 'user' ? (
                <>
                  <span className="font-semibold text-slate-300">You</span>
                  <User className="w-3.5 h-3.5 text-blue-400" />
                </>
              ) : (
                <>
                  <Bot className="w-3.5 h-3.5 text-purple-400" />
                  <span className="font-semibold text-purple-300">OmniBrain Agent</span>
                  {msg.confidence > 0 && (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                      {(msg.confidence * 100).toFixed(0)}% Confidence
                    </span>
                  )}
                </>
              )}
            </div>

            <div
              className={`p-4 md:p-5 rounded-2xl max-w-3xl text-sm leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-blue-600/30 border border-blue-500/40 text-slate-100 rounded-tr-none shadow-lg'
                  : 'glass-panel border border-white/10 text-slate-200 rounded-tl-none space-y-3 shadow-xl'
              }`}
            >
              {/* Agent execution live steps badge */}
              {msg.sender === 'assistant' && msg.agentTrace && msg.agentTrace.length > 0 && (
                <div className="p-2.5 rounded-xl bg-black/40 border border-white/5 text-xs text-slate-400 space-y-1 font-mono">
                  <div className="text-[10px] uppercase font-bold text-blue-400 flex items-center space-x-1.5">
                    <Activity className="w-3 h-3 text-blue-400" />
                    <span>Orchestration Trace</span>
                  </div>
                  {msg.agentTrace.map((step, sIdx) => (
                    <div key={sIdx} className="text-slate-300 truncate">
                      → {step}
                    </div>
                  ))}
                </div>
              )}

              {/* Formatted Content */}
              {renderFormattedText(msg.text || (msg.isStreaming ? 'Synthesizing verified response...' : ''))}

              {/* Sources / Citations */}
              {msg.sender === 'assistant' && msg.citations && msg.citations.length > 0 && (
                <div className="pt-3 border-t border-white/10 flex flex-wrap items-center gap-2">
                  <span className="text-xs font-semibold text-slate-400 flex items-center space-x-1">
                    <BookOpen className="w-3.5 h-3.5 text-blue-400" />
                    <span>Citations ({msg.citations.length}):</span>
                  </span>
                  {msg.citations.map((cit, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        setActiveCitations(msg.citations);
                        setShowCitationDrawer(true);
                      }}
                      className="text-xs px-2.5 py-1 rounded-lg glass-panel hover:border-blue-400 text-blue-300 border border-white/10 transition-all flex items-center space-x-1"
                    >
                      <span>{cit.document_name || 'Document'} p.{cit.page || 1}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Action Bar for Assistant Messages */}
            {msg.sender === 'assistant' && !msg.isStreaming && msg.text && (
              <div className="flex items-center space-x-3 text-xs text-slate-500 pt-1">
                <button
                  onClick={() => copyToClipboard(msg.id, msg.text)}
                  className="hover:text-slate-300 flex items-center space-x-1 transition-colors"
                >
                  {copiedId === msg.id ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedId === msg.id ? 'Copied' : 'Copy'}</span>
                </button>
                <span>•</span>
                <button
                  onClick={() => handleSend(messages[messages.length - 2]?.text)}
                  className="hover:text-slate-300 flex items-center space-x-1 transition-colors"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Regenerate</span>
                </button>
              </div>
            )}

            {/* Follow Up Question Chips */}
            {msg.sender === 'assistant' && msg.followUps && msg.followUps.length > 0 && !msg.isStreaming && (
              <div className="flex flex-wrap gap-2 pt-2 max-w-3xl">
                {msg.followUps.map((fq, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(fq)}
                    className="text-xs px-3 py-1.5 rounded-full bg-blue-900/30 hover:bg-blue-800/50 text-blue-300 border border-blue-500/30 transition-all duration-200 text-left flex items-center space-x-1.5 shadow-sm"
                  >
                    <Sparkles className="w-3 h-3 text-blue-400" />
                    <span>{fq}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Floating Bottom Input Bar */}
      <div className="absolute bottom-0 left-0 right-0 p-4 md:p-6 bg-gradient-to-t from-[#080c14] via-[#080c14]/90 to-transparent z-20">
        <div className="max-w-4xl mx-auto glass-panel rounded-2xl p-2 border border-white/10 flex items-center space-x-3 shadow-2xl">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask anything about your document or enterprise database..."
            className="flex-1 bg-transparent px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isStreaming}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 font-semibold text-sm shadow-lg shadow-blue-500/20 disabled:opacity-40 disabled:cursor-not-allowed flex items-center space-x-2 transition-all"
          >
            <span>Send</span>
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Citations Drawer Modal */}
      {showCitationDrawer && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-md bg-[#0d1322] h-full p-6 space-y-6 overflow-y-auto border-l border-white/10 shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <h3 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
                <BookOpen className="w-5 h-5 text-blue-400" />
                <span>Source Citations</span>
              </h3>
              <button
                onClick={() => setShowCitationDrawer(false)}
                className="text-slate-400 hover:text-slate-200 text-sm font-semibold px-3 py-1 rounded-lg glass-panel"
              >
                Close
              </button>
            </div>

            <div className="space-y-4">
              {activeCitations.map((cit, idx) => (
                <div key={idx} className="glass-panel p-4 rounded-xl border border-white/10 space-y-2">
                  <div className="flex items-center justify-between text-xs font-semibold text-blue-400">
                    <span>{cit.document_name || 'Document'}</span>
                    <span>Page {cit.page || 1} • {cit.source_type || 'text'}</span>
                  </div>
                  <p className="text-xs text-slate-300 italic font-mono bg-black/40 p-3 rounded-lg border border-white/5">
                    "{cit.snippet || 'Relevant excerpt'}"
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
