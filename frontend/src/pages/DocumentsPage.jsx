import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload, FileText, File, Loader2, Trash2, AlertCircle,
  FileImage, FileType, Eye, RefreshCw, UploadCloud,
} from 'lucide-react';
import api from '../lib/api';
import { cn } from '../lib/utils';
import DocumentVerificationPanel, { resolveVerificationBadge } from '../components/documents/DocumentVerificationPanel';

const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'application/pdf'];
const MAX_SIZE_MB = 5;

const DOC_TYPES = [
  { value: 'aadhaar', label: 'Aadhaar Card' },
  { value: 'income_certificate', label: 'Income Certificate' },
  { value: 'caste_certificate', label: 'Caste Certificate' },
  { value: 'bank_passbook', label: 'Bank Passbook' },
  { value: 'photo', label: 'Passport Photo' },
];

const formatFileSize = (bytes = 0) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const getFileIcon = (type) => {
  if (type?.startsWith('image')) return FileImage;
  if (type === 'application/pdf') return FileType;
  return File;
};

const isDocProcessing = (doc) =>
  doc.status === 'processing' ||
  (doc.status === 'pending' && (!doc.verification_status || doc.verification_status === 'pending'));

const DocumentCard = ({ doc, onDelete, onReverify, onReupload }) => {
  const FileIcon = getFileIcon(doc.file_type);
  const docTypeValue = doc.doc_type || doc.document_category || 'aadhaar';
  const categoryLabel = DOC_TYPES.find((c) => c.value === docTypeValue)?.label || docTypeValue.replaceAll('_', ' ');
  const badge = resolveVerificationBadge(doc);
  const StatusIcon = badge.icon;
  const needsReupload = ['Mismatch', 'Needs review'].includes(badge.label);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="bg-card border border-border/50 rounded-2xl p-5 hover:border-border/80 hover:shadow-lg hover:shadow-black/10 transition-all duration-300 group"
    >
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 rounded-xl bg-secondary/60 border border-border/30 flex items-center justify-center shrink-0">
          <FileIcon className="w-5 h-5 text-muted-foreground" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h4 className="text-sm font-semibold text-foreground truncate">{doc.file_name}</h4>
            <span className={cn(
              'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium',
              badge.className,
            )}>
              <StatusIcon className="w-3 h-3" />
              {badge.label}
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">{categoryLabel}</p>

          <div className="flex items-center gap-3 mt-2 text-[11px] text-muted-foreground">
            <span>{formatFileSize(doc.file_size_bytes)}</span>
            <span>
              {doc.uploaded_at
                ? new Date(doc.uploaded_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
                : 'Just now'}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1 shrink-0">
          {doc.signed_url && (
            <a
              href={doc.signed_url}
              target="_blank"
              rel="noreferrer"
              className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary/60 transition-colors"
              title="View document"
            >
              <Eye className="w-4 h-4" />
            </a>
          )}
          <button
            type="button"
            onClick={() => onDelete(doc.id)}
            aria-label={`Delete ${doc.file_name}`}
            className="p-2 rounded-lg text-rose-400/70 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
            title="Delete"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      <DocumentVerificationPanel document={doc} />

      <div className="mt-3 flex flex-wrap items-center gap-2">
        {needsReupload && (
          <button
            type="button"
            onClick={() => onReupload(doc)}
            className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-white hover:bg-primary/90 transition-colors"
          >
            <UploadCloud className="w-3.5 h-3.5" />
            Re-upload
          </button>
        )}
        {!isDocProcessing(doc) && (
          <button
            type="button"
            onClick={() => onReverify(doc.id)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border/60 bg-secondary/40 px-3 py-1.5 text-xs font-medium text-foreground hover:bg-secondary transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Re-verify
          </button>
        )}
      </div>
    </motion.div>
  );
};

const DocumentsPage = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [docType, setDocType] = useState('aadhaar');
  const [dragActive, setDragActive] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [loadError, setLoadError] = useState('');
  const [actionError, setActionError] = useState('');
  const [replacingDoc, setReplacingDoc] = useState(null);

  const fileInputRef = useRef(null);
  const reuploadInputRef = useRef(null);
  const documentsRef = useRef(documents);

  useEffect(() => {
    documentsRef.current = documents;
  }, [documents]);

  const fetchDocuments = useCallback(async () => {
    try {
      const response = await api.get('/documents');
      setDocuments(response.data.documents || []);
      setLoadError('');
    } catch (error) {
      setLoadError(error.response?.data?.detail || 'Documents could not be loaded. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  const pollProcessingDocuments = useCallback(async () => {
    const processingDocs = documentsRef.current.filter(isDocProcessing);
    if (processingDocs.length === 0) return;

    try {
      const updates = await Promise.all(
        processingDocs.map((doc) => api.get(`/documents/${doc.id}/status`).then((res) => res.data)),
      );
      const updatesById = Object.fromEntries(updates.map((u) => [u.id, u]));
      setDocuments((current) =>
        current.map((doc) => (updatesById[doc.id] ? { ...doc, ...updatesById[doc.id] } : doc)),
      );
    } catch {
      fetchDocuments();
    }
  }, [fetchDocuments]);

  useEffect(() => {
    fetchDocuments();
    const interval = setInterval(() => {
      if (documentsRef.current.some(isDocProcessing)) {
        pollProcessingDocuments();
      }
    }, 2500);
    return () => clearInterval(interval);
  }, [fetchDocuments, pollProcessingDocuments]);

  const validateFile = (file) => {
    if (!ACCEPTED_TYPES.includes(file.type)) {
      return 'Only JPG, PNG, and PDF files are allowed.';
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      return `File exceeds ${MAX_SIZE_MB}MB limit.`;
    }
    return '';
  };

  const uploadAndVerify = async (file, selectedDocType, oldDocId = null) => {
    const validationError = validateFile(file);
    if (validationError) {
      setUploadError(validationError);
      return;
    }

    setUploadError('');
    setActionError('');
    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('doc_type', selectedDocType);

      const uploadRes = await api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const created = uploadRes.data;

      if (oldDocId) {
        await api.delete(`/documents/${oldDocId}`).catch(() => {});
        setDocuments((prev) => [
          { ...created, status: 'processing', verification_status: 'pending' },
          ...prev.filter((d) => d.id !== oldDocId),
        ]);
      } else {
        setDocuments((prev) => [
          { ...created, status: 'processing', verification_status: 'pending' },
          ...prev,
        ]);
      }

      await api.post(`/documents/${created.id}/verify`);
    } catch (error) {
      setUploadError(error.response?.data?.detail || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
      setReplacingDoc(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      if (reuploadInputRef.current) reuploadInputRef.current.value = '';
    }
  };

  const handleFilesSelected = (files) => {
    if (!files || files.length === 0) return;
    uploadAndVerify(files[0], docType);
  };

  const handleReuploadTrigger = (doc) => {
    setReplacingDoc(doc);
    reuploadInputRef.current?.click();
  };

  const handleReuploadFile = (files) => {
    if (!files || files.length === 0 || !replacingDoc) return;
    const targetDocType = replacingDoc.doc_type || replacingDoc.document_category || 'aadhaar';
    uploadAndVerify(files[0], targetDocType, replacingDoc.id);
  };

  const handleDelete = async (docId) => {
    setActionError('');
    try {
      await api.delete(`/documents/${docId}`);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch (error) {
      setActionError(error.response?.data?.detail || 'Document could not be deleted. Please try again.');
    }
  };

  const handleReverify = async (docId) => {
    setActionError('');
    setDocuments((current) =>
      current.map((doc) =>
        doc.id === docId ? { ...doc, status: 'processing', verification_status: 'pending' } : doc,
      ),
    );
    try {
      await api.post(`/documents/${docId}/verify`);
    } catch (error) {
      setActionError(error.response?.data?.detail || 'Verification could not be started. Please try again.');
      fetchDocuments();
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
    handleFilesSelected(e.dataTransfer.files);
  };

  const counts = {
    total: documents.length,
    verified: documents.filter((d) => ['verified', 'preliminary_match'].includes(d.verification_status || d.verification?.verification_status)).length,
    mismatch: documents.filter((d) => (d.verification_status || d.verification?.verification_status) === 'mismatch').length,
    review: documents.filter((d) => ['needs_review', 'unreadable'].includes(d.verification_status || d.verification?.verification_status)).length,
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-[28px] font-bold text-foreground tracking-tight">Documents & Verification</h1>
        <p className="text-sm text-muted-foreground mt-1.5">
          Upload JPG, PNG, or PDF documents (up to {MAX_SIZE_MB} MB) to extract fields with OCR + Groq and verify them against your profile.
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Uploaded', value: counts.total, color: 'text-foreground', bg: 'bg-secondary/50' },
          { label: 'Verified', value: counts.verified, color: 'text-emerald-400', bg: 'bg-emerald-500/8' },
          { label: 'Mismatch', value: counts.mismatch, color: 'text-rose-400', bg: 'bg-rose-500/8' },
          { label: 'Needs review', value: counts.review, color: 'text-amber-400', bg: 'bg-amber-500/8' },
        ].map((stat) => (
          <div key={stat.label} className={cn('rounded-xl p-4 border border-border/30', stat.bg)}>
            <p className="text-xs text-muted-foreground font-medium">{stat.label}</p>
            <p className={cn('text-2xl font-bold mt-1', stat.color)}>{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Inline Drag-and-Drop Upload Card */}
      <div className="bg-card border border-border/60 rounded-2xl p-5 sm:p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <h2 className="text-base font-semibold text-foreground">Upload Document</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Select the document type, then drag & drop or browse a file.
            </p>
          </div>
          <div className="sm:w-64">
            <label htmlFor="doc-type-select" className="block text-xs font-medium text-muted-foreground mb-1">
              Document Type
            </label>
            <select
              id="doc-type-select"
              value={docType}
              onChange={(e) => setDocType(e.target.value)}
              disabled={uploading}
              className="w-full px-3.5 py-2 bg-secondary/50 border border-border/50 rounded-xl text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/25 focus:border-primary/40 transition-all"
            >
              {DOC_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => !uploading && fileInputRef.current?.click()}
          onKeyDown={(e) => {
            if ((e.key === 'Enter' || e.key === ' ') && !uploading) {
              e.preventDefault();
              fileInputRef.current?.click();
            }
          }}
          role="button"
          tabIndex={uploading ? -1 : 0}
          aria-label="Drag and drop or select a JPG, PNG, or PDF document"
          className={cn(
            'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200',
            dragActive ? 'border-primary bg-primary/5' : 'border-border/50 hover:border-border/80 hover:bg-secondary/20',
            uploading && 'opacity-60 pointer-events-none',
          )}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED_TYPES.join(',')}
            onChange={(e) => handleFilesSelected(e.target.files)}
            className="hidden"
          />
          <input
            ref={reuploadInputRef}
            type="file"
            accept={ACCEPTED_TYPES.join(',')}
            onChange={(e) => handleReuploadFile(e.target.files)}
            className="hidden"
          />

          {uploading ? (
            <div className="flex flex-col items-center">
              <Loader2 className="w-8 h-8 text-primary animate-spin mb-2" />
              <p className="text-sm font-medium text-foreground">Uploading & starting verification...</p>
            </div>
          ) : (
            <>
              <Upload className={cn('w-8 h-8 mx-auto mb-2.5', dragActive ? 'text-primary' : 'text-muted-foreground/50')} />
              <p className="text-sm font-medium text-foreground">
                {dragActive ? 'Drop your document here' : 'Drag & drop your file here, or click to browse'}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                JPG, PNG, or PDF · Max {MAX_SIZE_MB} MB
              </p>
            </>
          )}
        </div>

        {uploadError && (
          <div className="flex items-center gap-2 text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 px-3.5 py-2.5 rounded-xl">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{uploadError}</span>
          </div>
        )}
      </div>

      {/* Action / Load Errors */}
      {actionError && (
        <div className="flex items-center gap-2 rounded-xl border border-rose-500/20 bg-rose-500/8 p-4 text-sm text-rose-400">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {/* Documents List */}
      {loading ? (
        <div className="flex items-center justify-center h-48">
          <Loader2 className="w-7 h-7 animate-spin text-primary" />
        </div>
      ) : loadError ? (
        <div className="flex items-center justify-between gap-3 rounded-xl border border-rose-500/20 bg-rose-500/8 p-4 text-sm text-rose-400">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{loadError}</span>
          </div>
          <button
            type="button"
            onClick={() => {
              setLoading(true);
              fetchDocuments();
            }}
            className="rounded-lg border border-rose-500/30 px-3 py-1 text-xs font-medium hover:bg-rose-500/10"
          >
            Retry
          </button>
        </div>
      ) : documents.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-14 text-center rounded-2xl border border-dashed border-border/50 bg-card/40">
          <div className="w-14 h-14 rounded-2xl bg-secondary/60 flex items-center justify-center mb-3">
            <FileText className="w-6 h-6 text-muted-foreground/50" />
          </div>
          <p className="text-foreground font-medium">No documents uploaded yet</p>
          <p className="text-xs text-muted-foreground mt-1">
            Upload your Aadhaar, Income Certificate, Caste Certificate, Bank Passbook, or Photo above.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <AnimatePresence>
            {documents.map((doc) => (
              <DocumentCard
                key={doc.id}
                doc={doc}
                onDelete={handleDelete}
                onReverify={handleReverify}
                onReupload={handleReuploadTrigger}
              />
            ))}
          </AnimatePresence>
        </div>
      )}
    </motion.div>
  );
};

export default DocumentsPage;
