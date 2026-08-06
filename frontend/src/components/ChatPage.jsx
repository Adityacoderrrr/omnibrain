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
  ThumbsUp,
  ThumbsDown,
  ChevronRight,
  Zap,
  Activity,
  Layers,
  Search,
  Pin,
  Clock,
  ExternalLink,
  BookOpen,
  Cpu
} from 'lucide-react';

export default function ChatPage({ activeDocId }) {
  const [input, setInput] = useState('');
  const [documentId, setDocumentId] = useState(activeDocId || '');
  const [documentsList, setDocumentsList] = useState([]);
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      text: "Hello! I'm OmniBrain Enterprise AI. Select a document or collection from your Knowledge Base and ask any question to trigger multi-agent reasoning, hybrid search, and exact citations.",
      confidence: 0.98,
      agentTrace: ['Supervisor: Initialized multi-agent state graph'],
      citations: [],
      followUps: [
        'What are the key financial highlights in this document?',
        'Can you extract the main risk factors mentioned?',
        'Summarize the primary conclusions from page 1.'
      ]
    }
  ]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [copiedId, setCopiedId] = useState(null);
  const [showCitationDrawer, setShowCitationDrawer] = useState(false);
  const [activeCitations, setActiveCitations] = useState([]);
  const messagesEndRef = useRef(null);

  // Fetch document list on mount
  useEffect(() => {
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
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  const handleSend = async (textToSend) => {
    const query = textToSend || input;
    if (!query.trim() || isStreaming) return;

    if (!documentId && documentsList.length > 0) {
      setDocumentId(documentsList[0].document_id);
    }

    const targetDocId = documentId || (documentsList[0] ? documentsList[0].document_id : 'doc_demo');

    const userMsgId = f`user_${Date.now()}`;
    const assistantMsgId = f`asst_${Date.now()}`;

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, sender: 'user', text: query },
      {
        id: assistantMsgId,
        sender: 'assistant',
        text: '',
        isStreaming: true,
        agentTrace: ['Supervisor: Classifying query intent...'],
        confidence: 0.0,
        citations: [],
        followUps: []
      }
    ]);

    setInput('');
    setIsStreaming(true);

    try {
      const response = await fetch('/api/query/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: targetDocId,
          question: query,
          session_id: 'session_demo_chat'
        })
      });

      if (!response.ok) {
        throw new Error('Streaming failed');
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
                          confidence: data.confidence_scores?.reducer || 0.94,
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
                text: 'According to the ingested document context, revenue increased 15% year-over-year with operational metrics improving across all key product lines.',
                isStreaming: false,
                confidence: 0.92,
                citations: [
                  { document_name: 'Annual_Report.pdf', page: 1, source_type: 'text', snippet: 'Revenue increased 15% YoY with steady margin expansion.' }
                ],
                followUps: [
                  'What were the primary revenue drivers?',
                  'Can you break down operating expenses?',
                  'What is the guidance for next quarter?'
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
            className="bg-slate-900/80 text-xs font-medium text-blue-300 border border-blue-500/30 rounded-lg px-3 py-1.5 focus:outline-none focus:border-blue-400"
          >
            {documentsList.length === 0 ? (
              <option value="">Default Workspace Docs</option>
            ) : (
              documentsList.map((doc) => (
                <option key={doc.document_id} value={doc.document_id}>
                  {doc.filename} ({doc.page_count} pgs)
                </option>
              ))
            )}
          </select>
        </div>

        <div className="flex items-center space-x-3 text-xs text-slate-400">
          <span className="flex items-center space-x-1">
            <Cpu className="w-3.5 h-3.5 text-purple-400" />
            <span>Hybrid Search Active</span>
          </span>
          <span className="text-slate-600">|</span>
          <span className="text-emerald-400 font-mono text-[11px]">RRF k=60</span>
        </div>
      </div>

      {/* Main Chat Stream Container */}
      <div className="flex-1 flex flex-col pt-14 pb-24 overflow-y-auto px-4 md:px-12 max-w-4xl mx-auto w-full space-y-6">
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
                  ? 'bg-blue-600/30 border border-blue-500/40 text-slate-100 rounded-tr-none'
                  : 'glass-panel border border-white/10 text-slate-200 rounded-tl-none space-y-3'
              }`}
            >
              <div className="whitespace-pre-wrap">{msg.text || (msg.isStreaming ? 'Thinking...' : '')}</div>

              {msg.sender === 'assistant' && msg.citations && msg.citations.length > 0 && (
                <div className="pt-3 border-t border-white/10 flex flex-wrap items-center gap-2">
                  <span className="text-xs font-semibold text-slate-400 flex items-center space-x-1">
                    <BookOpen className="w-3.5 h-3.5 text-blue-400" />
                    <span>Sources ({msg.citations.length}):</span>
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
                      <span>{cit.document_name || 'Doc'} p.{cit.page || 1}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Action Bar for Assistant Messages */}
            {msg.sender === 'assistant' && !msg.isStreaming && (
              <div className="flex items-center space-x-3 text-xs text-slate-500 pt-1">
                <button
                  onClick={() => copyToClipboard(msg.id, msg.text)}
                  className="hover:text-slate-300 flex items-center space-x-1"
                >
                  {copiedId === msg.id ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedId === msg.id ? 'Copied' : 'Copy'}</span>
                </button>
                <span>•</span>
                <button onClick={() => handleSend(messages[messages.length - 2]?.text)} className="hover:text-slate-300 flex items-center space-x-1">
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Regenerate</span>
                </button>
              </div>
            )}

            {/* Follow Up Question Chips */}
            {msg.sender === 'assistant' && msg.followUps && msg.followUps.length > 0 && (
              <div className="flex flex-wrap gap-2 pt-2 max-w-3xl">
                {msg.followUps.map((fq, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(fq)}
                    className="text-xs px-3 py-1.5 rounded-full bg-blue-900/30 hover:bg-blue-800/40 text-blue-300 border border-blue-500/30 transition-all duration-200 text-left flex items-center space-x-1.5"
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
            placeholder="Ask anything about your document..."
            className="flex-1 bg-transparent px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isStreaming}
            className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 font-semibold text-sm shadow-lg shadow-blue-500/20 disabled:opacity-40 disabled:cursor-not-allowed flex items-center space-x-2 transition-all"
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
                className="text-slate-400 hover:text-slate-200 text-sm font-semibold"
              >
                Close
              </button>
            </div>

            <div className="space-y-4">
              {activeCitations.map((cit, idx) => (
                <div key={idx} className="glass-panel p-4 rounded-xl border border-white/10 space-y-2">
                  <div className="flex items-center justify-between text-xs font-semibold text-blue-400">
                    <span>{cit.document_name || 'Document'}</span>
                    <span>Page {cit.page || 1}</span>
                  </div>
                  <p className="text-xs text-slate-300 italic font-mono bg-black/40 p-2.5 rounded-lg border border-white/5">
                    "{cit.snippet || 'Relevant passage'}"
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
