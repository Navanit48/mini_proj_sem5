import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload, FileText, Image, File, Loader2, CheckCircle2,
  XCircle, Clock, Trash2, Eye, RotateCcw, AlertCircle,
  FileImage, FileType, Plus, X, Download, Sparkles
} from 'lucide-react';
import api from '../lib/api';
import { cn } from '../lib/utils';

const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'application/pdf'];
const MAX_SIZE_MB = 10;

const DOCUMENT_CATEGORIES = [
  { value: 'aadhaar', label: 'Aadhaar Card' },
  { value: 'pan', label: 'PAN Card' },
  { value: 'income_certificate', label: 'Income Certificate' },
  { value: 'caste_certificate', label: 'Caste Certificate' },
  { value: 'domicile', label: 'Domicile Certificate' },
  { value: 'ration_card', label: 'Ration Card' },
  { value: 'bank_passbook', label: 'Bank Passbook' },
  { value: 'land_record', label: 'Land Record' },
  { value: 'marksheet', label: 'Marksheet / Certificate' },
  { value: 'general', label: 'Other' },
];

const statusConfig = {
  uploaded: { icon: Clock, color: 'text-amber-400', bg: 'bg-amber-500/10', label: 'Uploaded' },
  processing: { icon: Loader2, color: 'text-blue-400', bg: 'bg-blue-500/10', label: 'Processing', spin: true },
  completed: { icon: CheckCircle2, color: 'text-emerald-400', bg: 'bg-emerald-500/10', label: 'OCR Complete' },
  failed: { icon: XCircle, color: 'text-rose-400', bg: 'bg-rose-500/10', label: 'Failed' },
};

// Demo data
const DEMO_DOCUMENTS = [
  { id: 'd1', file_name: 'aadhaar_front.jpg', file_type: 'image/jpeg', document_category: 'aadhaar', status: 'completed', file_size_bytes: 245000, uploaded_at: '2026-10-15T10:30:00Z' },
  { id: 'd2', file_name: 'pan_card.png', file_type: 'image/png', document_category: 'pan', status: 'completed', file_size_bytes: 312000, uploaded_at: '2026-10-14T14:20:00Z' },
  { id: 'd3', file_name: 'income_certificate_2026.pdf', file_type: 'application/pdf', document_category: 'income_certificate', status: 'uploaded', file_size_bytes: 156000, uploaded_at: '2026-10-20T09:15:00Z' },
  { id: 'd4', file_name: 'caste_cert.jpg', file_type: 'image/jpeg', document_category: 'caste_certificate', status: 'processing', file_size_bytes: 198000, uploaded_at: '2026-10-22T16:45:00Z' },
  { id: 'd5', file_name: 'bank_passbook_page1.jpg', file_type: 'image/jpeg', document_category: 'bank_passbook', status: 'completed', file_size_bytes: 278000, uploaded_at: '2026-10-10T11:00:00Z' },
];

const formatFileSize = (bytes) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const getFileIcon = (type) => {
  if (type?.startsWith('image')) return FileImage;
  if (type === 'application/pdf') return FileType;
  return File;
};

const DocumentCard = ({ doc, onDelete, onRetryOcr }) => {
  const status = statusConfig[doc.status] || statusConfig.uploaded;
  const StatusIcon = status.icon;
  const FileIcon = getFileIcon(doc.file_type);
  const categoryLabel = DOCUMENT_CATEGORIES.find(c => c.value === doc.document_category)?.label || doc.document_category;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className="bg-card border border-border/50 rounded-2xl p-5 hover:border-border/80 hover:shadow-lg hover:shadow-black/10 transition-all duration-300 group"
    >
      <div className="flex items-start gap-4">
        {/* File Icon */}
        <div className="w-12 h-12 rounded-xl bg-secondary/60 border border-border/30 flex items-center justify-center shrink-0">
          <FileIcon className="w-5 h-5 text-muted-foreground" />
        </div>

        <div className="flex-1 min-w-0">
          {/* Name & Category */}
          <h4 className="text-sm font-semibold text-foreground truncate">{doc.file_name}</h4>
          <p className="text-xs text-muted-foreground mt-0.5">{categoryLabel}</p>

          {/* Meta Row */}
          <div className="flex items-center gap-3 mt-2.5">
            <span className={cn('inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-md', status.bg, status.color)}>
              <StatusIcon className={cn('w-3 h-3', status.spin && 'animate-spin')} />
              {status.label}
            </span>
            <span className="text-[11px] text-muted-foreground">{formatFileSize(doc.file_size_bytes)}</span>
            <span className="text-[11px] text-muted-foreground">
              {new Date(doc.uploaded_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
          {doc.status === 'failed' && (
            <button
              onClick={() => onRetryOcr(doc.id)}
              className="p-2 rounded-lg text-amber-400 hover:bg-amber-500/10 transition-colors"
              title="Retry OCR"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={() => onDelete(doc.id)}
            className="p-2 rounded-lg text-rose-400/70 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
            title="Delete"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </motion.div>
  );
};

const DocumentsPage = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [uploadCategory, setUploadCategory] = useState('general');
  const [dragActive, setDragActive] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await api.get('/documents');
      setDocuments(response.data.documents || []);
    } catch (error) {
      console.error('Failed to load documents, using demo', error);
      setDocuments(DEMO_DOCUMENTS);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (files) => {
    if (!files || files.length === 0) return;
    const file = files[0];

    // Validate
    if (!ACCEPTED_TYPES.includes(file.type)) {
      setUploadError('Only JPEG, PNG, and PDF files are allowed.');
      return;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setUploadError(`File exceeds ${MAX_SIZE_MB}MB limit.`);
      return;
    }

    setUploadError('');
    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('document_category', uploadCategory);

      const response = await api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setDocuments(prev => [response.data, ...prev]);
      setShowUpload(false);
      setUploadCategory('general');
    } catch (error) {
      console.error('Upload failed', error);
      // Demo fallback
      const newDoc = {
        id: `demo-${Date.now()}`,
        file_name: file.name,
        file_type: file.type,
        document_category: uploadCategory,
        status: 'uploaded',
        file_size_bytes: file.size,
        uploaded_at: new Date().toISOString(),
      };
      setDocuments(prev => [newDoc, ...prev]);
      setShowUpload(false);
      setUploadCategory('general');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId) => {
    try {
      await api.delete(`/documents/${docId}`);
    } catch (error) {
      console.error('Delete failed (demo mode)', error);
    }
    setDocuments(prev => prev.filter(d => d.id !== docId));
  };

  const handleRetryOcr = async (docId) => {
    try {
      await api.post(`/documents/${docId}/ocr`);
      setDocuments(prev => prev.map(d => d.id === docId ? { ...d, status: 'processing' } : d));
    } catch (error) {
      console.error('OCR retry failed', error);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    handleUpload(e.dataTransfer.files);
  };

  const statusCounts = {
    total: documents.length,
    completed: documents.filter(d => d.status === 'completed').length,
    pending: documents.filter(d => d.status === 'uploaded' || d.status === 'processing').length,
    failed: documents.filter(d => d.status === 'failed').length,
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl sm:text-[28px] font-bold text-foreground tracking-tight">Documents</h1>
          <p className="text-sm text-muted-foreground mt-1.5">
            Upload and manage your identity documents. AI-powered OCR extracts fields automatically.
          </p>
        </div>
        <button
          onClick={() => setShowUpload(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-white bg-primary hover:bg-primary/90 transition-all shadow-lg shadow-primary/20"
        >
          <Plus className="w-4 h-4" />
          Upload
        </button>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Total', value: statusCounts.total, color: 'text-foreground', bg: 'bg-secondary/50' },
          { label: 'OCR Complete', value: statusCounts.completed, color: 'text-emerald-400', bg: 'bg-emerald-500/8' },
          { label: 'Pending', value: statusCounts.pending, color: 'text-amber-400', bg: 'bg-amber-500/8' },
          { label: 'Failed', value: statusCounts.failed, color: 'text-rose-400', bg: 'bg-rose-500/8' },
        ].map((stat) => (
          <div key={stat.label} className={cn('rounded-xl p-4 border border-border/30', stat.bg)}>
            <p className="text-xs text-muted-foreground font-medium">{stat.label}</p>
            <p className={cn('text-2xl font-bold mt-1', stat.color)}>{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Upload Modal */}
      <AnimatePresence>
        {showUpload && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
            onClick={() => !uploading && setShowUpload(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-card border border-border/60 rounded-2xl p-6 w-full max-w-lg shadow-2xl"
            >
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-lg font-semibold text-foreground">Upload Document</h3>
                <button onClick={() => !uploading && setShowUpload(false)} className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary/60 transition-colors">
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Category Select */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-foreground mb-1.5">Document Type</label>
                <select
                  value={uploadCategory}
                  onChange={e => setUploadCategory(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-secondary/50 border border-border/50 rounded-xl text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/25 focus:border-primary/40 transition-all appearance-none"
                >
                  {DOCUMENT_CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                </select>
              </div>

              {/* Drop Zone */}
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => !uploading && fileInputRef.current?.click()}
                className={cn(
                  'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200',
                  dragActive ? 'border-primary bg-primary/5' : 'border-border/50 hover:border-border/80 hover:bg-secondary/20',
                  uploading && 'opacity-50 pointer-events-none'
                )}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={ACCEPTED_TYPES.join(',')}
                  onChange={e => handleUpload(e.target.files)}
                  className="hidden"
                />
                {uploading ? (
                  <div className="flex flex-col items-center">
                    <Loader2 className="w-8 h-8 text-primary animate-spin mb-3" />
                    <p className="text-sm font-medium text-foreground">Uploading & processing...</p>
                  </div>
                ) : (
                  <>
                    <Upload className={cn('w-8 h-8 mx-auto mb-3', dragActive ? 'text-primary' : 'text-muted-foreground/40')} />
                    <p className="text-sm font-medium text-foreground mb-1">
                      {dragActive ? 'Drop file here' : 'Click to upload or drag & drop'}
                    </p>
                    <p className="text-xs text-muted-foreground">JPEG, PNG, or PDF up to {MAX_SIZE_MB}MB</p>
                  </>
                )}
              </div>

              {uploadError && (
                <div className="mt-3 flex items-center gap-2 text-xs text-rose-400 bg-rose-500/8 px-3 py-2 rounded-lg">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  {uploadError}
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Documents List */}
      {loading ? (
        <div className="flex items-center justify-center h-48">
          <Loader2 className="w-7 h-7 animate-spin text-primary" />
        </div>
      ) : documents.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-16 h-16 rounded-2xl bg-secondary/60 flex items-center justify-center mb-4">
            <FileText className="w-7 h-7 text-muted-foreground/40" />
          </div>
          <p className="text-muted-foreground font-medium">No documents yet</p>
          <p className="text-sm text-muted-foreground/60 mt-1 mb-4">Upload your first document to get started</p>
          <button
            onClick={() => setShowUpload(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-primary bg-primary/8 hover:bg-primary/14 transition-all"
          >
            <Upload className="w-4 h-4" />
            Upload Document
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <AnimatePresence>
            {documents.map((doc) => (
              <DocumentCard
                key={doc.id}
                doc={doc}
                onDelete={handleDelete}
                onRetryOcr={handleRetryOcr}
              />
            ))}
          </AnimatePresence>
        </div>
      )}
    </motion.div>
  );
};

export default DocumentsPage;
