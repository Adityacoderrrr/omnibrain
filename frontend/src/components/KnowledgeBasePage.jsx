import React, { useState, useEffect } from 'react';
import {
  Upload,
  FileText,
  Trash2,
  Edit3,
  Tag,
  Search,
  CheckCircle2,
  Clock,
  AlertCircle,
  FolderPlus,
  Eye,
  Sparkles,
  Layers,
  Database,
  RefreshCw,
  Plus
} from 'lucide-react';

export default function KnowledgeBasePage({ onSelectDoc }) {
  const [documents, setDocuments] = useState([]);
  const [collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('all'); // 'all' or collection_id
  const [uploading, setUploading] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [newCollectionName, setNewCollectionName] = useState('');
  const [showCreateCol, setShowCreateCol] = useState(false);

  const fetchDocuments = () => {
    setLoading(true);
    fetch('/api/documents')
      .then((res) => res.json())
      .then((data) => {
        setDocuments(data.documents || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  const fetchCollections = () => {
    fetch('/api/collections')
      .then((res) => res.json())
      .then((data) => setCollections(data.collections || []))
      .catch(() => {});
  };

  useEffect(() => {
    fetchDocuments();
    fetchCollections();
  }, []);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData,
      });
      if (res.ok) {
        fetchDocuments();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDoc = async (id) => {
    if (!confirm('Are you sure you want to delete this document and purge its vectors?')) return;
    try {
      await fetch(`/api/documents/${id}`, { method: 'DELETE' });
      fetchDocuments();
    } catch (err) {}
  };

  const handleCreateCollection = async () => {
    if (!newCollectionName.trim()) return;
    try {
      await fetch('/api/collections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newCollectionName }),
      });
      setNewCollectionName('');
      setShowCreateCol(false);
      fetchCollections();
    } catch (err) {}
  };

  const filteredDocs = documents.filter((doc) =>
    (doc.filename || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="h-full w-full overflow-y-auto p-6 md:p-10 space-y-8 bg-[#080c14]">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-100 flex items-center space-x-3">
            <Database className="w-8 h-8 text-blue-400" />
            <span>Knowledge Base Manager</span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Upload, manage, tag, and inspect documents across PDF, DOCX, PPTX, Markdown, TXT, and Image formats.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <label className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 font-semibold text-sm shadow-lg shadow-blue-500/20 cursor-pointer flex items-center space-x-2 transition-all">
            <Upload className="w-4 h-4" />
            <span>{uploading ? 'Uploading...' : 'Upload Document'}</span>
            <input type="file" onChange={handleFileUpload} className="hidden" />
          </label>
        </div>
      </div>

      {/* Collections Bar */}
      <div className="flex items-center space-x-3 overflow-x-auto pb-2">
        <button
          onClick={() => setActiveTab('all')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'all'
              ? 'bg-blue-600/30 text-blue-300 border border-blue-500/40'
              : 'glass-panel text-slate-400 hover:text-slate-200'
          }`}
        >
          All Documents ({documents.length})
        </button>
        {collections.map((col) => (
          <button
            key={col.collection_id}
            onClick={() => setActiveTab(col.collection_id)}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === col.collection_id
                ? 'bg-purple-600/30 text-purple-300 border border-purple-500/40'
                : 'glass-panel text-slate-400 hover:text-slate-200'
            }`}
          >
            {col.name} ({col.document_count || 0})
          </button>
        ))}
        <button
          onClick={() => setShowCreateCol(true)}
          className="px-3 py-2 rounded-xl text-xs font-semibold glass-panel text-slate-400 hover:text-slate-200 flex items-center space-x-1"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New Collection</span>
        </button>
      </div>

      {/* Search Bar */}
      <div className="glass-panel rounded-2xl p-3 border border-white/10 flex items-center space-x-3">
        <Search className="w-4 h-4 text-slate-400 ml-2" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search documents by title..."
          className="flex-1 bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
        />
      </div>

      {/* Documents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredDocs.map((doc) => {
          const isReady = doc.status === 'ready';
          return (
            <div
              key={doc.document_id}
              className="glass-panel-interactive p-6 rounded-2xl border border-white/10 space-y-4 flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold text-xs border border-blue-500/30">
                    <FileText className="w-5 h-5" />
                  </div>

                  <span
                    className={`text-[10px] font-semibold px-2.5 py-1 rounded-full uppercase tracking-wider ${
                      isReady
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    }`}
                  >
                    {doc.status}
                  </span>
                </div>

                <div>
                  <h3 className="font-bold text-slate-100 text-base truncate">{doc.filename}</h3>
                  <p className="text-xs text-slate-400 mt-1 font-mono">
                    ID: {doc.document_id.slice(0, 12)}...
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-white/10 text-xs">
                  <div>
                    <span className="text-slate-500">Pages:</span>{' '}
                    <span className="font-semibold text-slate-200">{doc.page_count || 1}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Chunks:</span>{' '}
                    <span className="font-semibold text-slate-200">{doc.chunk_count || 0}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-white/10">
                <button
                  onClick={() => onSelectDoc(doc.document_id)}
                  className="px-3 py-1.5 rounded-lg bg-blue-600/30 hover:bg-blue-600/50 text-blue-300 font-semibold text-xs transition-all flex items-center space-x-1"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Query Doc</span>
                </button>

                <button
                  onClick={() => handleDeleteDoc(doc.document_id)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-all"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Create Collection Modal */}
      {showCreateCol && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel p-6 rounded-2xl max-w-md w-full border border-white/10 space-y-4">
            <h3 className="text-lg font-bold text-slate-100">Create New Collection</h3>
            <input
              type="text"
              value={newCollectionName}
              onChange={(e) => setNewCollectionName(e.target.value)}
              placeholder="e.g. Financial Reports 2026"
              className="w-full bg-slate-900 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-400"
            />
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowCreateCol(false)}
                className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateCollection}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-xs font-bold"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
