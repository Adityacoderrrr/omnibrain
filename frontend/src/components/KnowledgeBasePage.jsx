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
  Plus,
  X,
  FileCheck,
  FileSpreadsheet
} from 'lucide-react';

export default function KnowledgeBasePage({ onSelectDoc }) {
  const [documents, setDocuments] = useState([]);
  const [collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('all');
  const [uploading, setUploading] = useState(false);
  const [selectedDocDetails, setSelectedDocDetails] = useState(null);
  const [newCollectionName, setNewCollectionName] = useState('');
  const [showCreateCol, setShowCreateCol] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [dragOver, setDragOver] = useState(false);

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

  const uploadFile = async (file) => {
    if (!file) return;

    setUploading(true);
    setUploadError(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData,
      });
      if (res.ok) {
        // Poll for processing completion
        fetchDocuments();
        const uploadData = await res.json();
        const pollInterval = setInterval(async () => {
          try {
            const statusRes = await fetch(`/api/documents/${uploadData.document_id}/status`);
            if (statusRes.ok) {
              const statusData = await statusRes.json();
              if (statusData.status === 'ready' || statusData.status === 'failed') {
                clearInterval(pollInterval);
                fetchDocuments();
              }
            }
          } catch (e) {
            clearInterval(pollInterval);
          }
        }, 1000);
      } else {
        const err = await res.json().catch(() => ({}));
        setUploadError(err.detail || 'Upload failed. Supported formats: PDF, DOCX, PPTX, MD, TXT.');
      }
    } catch (err) {
      setUploadError('Network error during file upload.');
    } finally {
      setUploading(false);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) uploadFile(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      uploadFile(e.dataTransfer.files[0]);
    }
  };

  const handleDeleteDoc = async (id) => {
    if (!confirm('Are you sure you want to delete this document and purge its vectors from the index?')) return;
    try {
      await fetch(`/api/documents/${id}`, { method: 'DELETE' });
      fetchDocuments();
      if (selectedDocDetails && selectedDocDetails.document_id === id) {
        setSelectedDocDetails(null);
      }
    } catch (err) {}
  };

  const handleInspectDoc = async (docId) => {
    try {
      const res = await fetch(`/api/documents/${docId}/details`);
      if (res.ok) {
        const details = await res.json();
        setSelectedDocDetails(details);
      }
    } catch (e) {}
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
            Upload, parse, chunk, embed, and inspect enterprise documents across PDF, DOCX, PPTX, Markdown, and TXT formats.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <label className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 font-semibold text-sm shadow-lg shadow-blue-500/20 cursor-pointer flex items-center space-x-2 transition-all">
            <Upload className="w-4 h-4" />
            <span>{uploading ? 'Processing & Ingesting...' : 'Upload Document'}</span>
            <input type="file" onChange={handleFileUpload} className="hidden" accept=".pdf,.docx,.pptx,.md,.txt" />
          </label>
        </div>
      </div>

      {/* Drag & Drop Dropzone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`p-6 rounded-2xl border-2 border-dashed transition-all flex flex-col items-center justify-center space-y-2 cursor-pointer ${
          dragOver
            ? 'border-blue-400 bg-blue-500/10'
            : 'border-white/10 glass-panel hover:border-blue-500/30'
        }`}
      >
        <Upload className="w-8 h-8 text-blue-400" />
        <div className="text-sm font-semibold text-slate-200">
          Drag & drop your files here or click Upload Document
        </div>
        <div className="text-xs text-slate-400">
          Supports PDF (with OCR layout extraction), Word (.docx), PowerPoint (.pptx), Markdown (.md), and Text (.txt)
        </div>
      </div>

      {uploadError && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{uploadError}</span>
          </div>
          <button onClick={() => setUploadError(null)} className="text-red-400 hover:text-red-200">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

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
          placeholder="Search uploaded documents by title..."
          className="flex-1 bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
        />
      </div>

      {/* Documents Grid / Empty State */}
      {filteredDocs.length === 0 ? (
        <div className="glass-panel p-12 rounded-3xl border border-white/10 text-center space-y-4 max-w-xl mx-auto">
          <div className="w-16 h-16 rounded-2xl bg-blue-500/10 text-blue-400 flex items-center justify-center mx-auto border border-blue-500/20">
            <FileSpreadsheet className="w-8 h-8" />
          </div>
          <h3 className="text-xl font-bold text-slate-100">No Documents Found</h3>
          <p className="text-sm text-slate-400 leading-relaxed">
            {searchQuery
              ? `No document matches your search query "${searchQuery}".`
              : "Your knowledge base is currently empty. Upload a PDF, Word document, or Markdown note to get started."}
          </p>
        </div>
      ) : (
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
                      ID: {doc.document_id.slice(0, 14)}...
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
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => onSelectDoc(doc.document_id)}
                      className="px-3 py-1.5 rounded-lg bg-blue-600/30 hover:bg-blue-600/50 text-blue-300 font-semibold text-xs transition-all flex items-center space-x-1"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Query</span>
                    </button>
                    <button
                      onClick={() => handleInspectDoc(doc.document_id)}
                      className="px-2.5 py-1.5 rounded-lg glass-panel hover:bg-white/10 text-slate-300 font-semibold text-xs transition-all"
                    >
                      Inspect
                    </button>
                  </div>

                  <button
                    onClick={() => handleDeleteDoc(doc.document_id)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-all"
                    title="Delete Document & Purge Vectors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Document Inspector Modal */}
      {selectedDocDetails && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel p-6 rounded-2xl max-w-lg w-full border border-white/10 space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
                <FileCheck className="w-5 h-5 text-blue-400" />
                <span>Document Details</span>
              </h3>
              <button
                onClick={() => setSelectedDocDetails(null)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs font-mono">
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-slate-400">Filename:</span>
                <span className="text-slate-200 font-bold">{selectedDocDetails.filename}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-slate-400">Document ID:</span>
                <span className="text-blue-300">{selectedDocDetails.document_id}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-slate-400">Ingestion Status:</span>
                <span className="text-emerald-400 uppercase font-bold">{selectedDocDetails.status}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-slate-400">Page Count:</span>
                <span className="text-slate-200">{selectedDocDetails.page_count}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-slate-400">Chunk Count (BM25 & Vector):</span>
                <span className="text-slate-200">{selectedDocDetails.chunk_count}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-slate-400">File Size:</span>
                <span className="text-slate-200">{selectedDocDetails.file_size_bytes} bytes</span>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => {
                  onSelectDoc(selectedDocDetails.document_id);
                  setSelectedDocDetails(null);
                }}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-xs font-bold"
              >
                Open in Chat Workspace
              </button>
            </div>
          </div>
        </div>
      )}

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
