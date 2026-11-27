-- Expand documents verification status/columns, ocr_results confidence_score, and PNG storage MIME support.
ALTER TABLE public.documents
  ADD COLUMN IF NOT EXISTS doc_type TEXT,
  ADD COLUMN IF NOT EXISTS raw_text TEXT,
  ADD COLUMN IF NOT EXISTS extracted_fields JSONB NOT NULL DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS ocr_confidence NUMERIC,
  ADD COLUMN IF NOT EXISTS mismatch_details JSONB NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS verified_at TIMESTAMPTZ;

ALTER TABLE public.documents
  DROP CONSTRAINT IF EXISTS documents_status_check,
  ADD CONSTRAINT documents_status_check
    CHECK (status IN ('pending', 'uploaded', 'processing', 'completed', 'failed'));

ALTER TABLE public.documents
  DROP CONSTRAINT IF EXISTS documents_verification_status_check,
  ADD CONSTRAINT documents_verification_status_check
    CHECK (verification_status IN ('pending', 'verified', 'mismatch', 'preliminary_match', 'needs_review', 'unreadable'));

ALTER TABLE public.ocr_results
  ADD COLUMN IF NOT EXISTS confidence_score NUMERIC NOT NULL DEFAULT 0;

CREATE UNIQUE INDEX IF NOT EXISTS idx_ocr_results_document_id_unique
  ON public.ocr_results(document_id);

ALTER TABLE public.ocr_results
  DROP CONSTRAINT IF EXISTS ocr_results_verification_status_check,
  ADD CONSTRAINT ocr_results_verification_status_check
    CHECK (verification_status IN ('pending', 'verified', 'mismatch', 'preliminary_match', 'needs_review', 'unreadable'));

UPDATE storage.buckets
SET file_size_limit = 10485760,
    allowed_mime_types = ARRAY['application/pdf', 'image/jpeg', 'image/png']
WHERE id = 'documents';
