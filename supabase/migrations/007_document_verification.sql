-- Extend documents table for OCR extraction and profile verification.
ALTER TABLE public.documents
  ADD COLUMN IF NOT EXISTS doc_type TEXT
    CHECK (doc_type IN ('aadhaar', 'income_certificate', 'caste_certificate', 'bank_passbook', 'photo')),
  ADD COLUMN IF NOT EXISTS storage_path TEXT,
  ADD COLUMN IF NOT EXISTS raw_text TEXT,
  ADD COLUMN IF NOT EXISTS extracted_fields JSONB NOT NULL DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS ocr_confidence NUMERIC,
  ADD COLUMN IF NOT EXISTS verification_status TEXT NOT NULL DEFAULT 'pending'
    CHECK (verification_status IN ('pending', 'verified', 'mismatch', 'needs_review')),
  ADD COLUMN IF NOT EXISTS mismatch_details JSONB NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS verified_at TIMESTAMPTZ;

-- Allow both legacy statuses and the new 'pending' workflow status.
ALTER TABLE public.documents DROP CONSTRAINT IF EXISTS documents_status_check;
ALTER TABLE public.documents
  ADD CONSTRAINT documents_status_check
  CHECK (status IN ('pending', 'uploaded', 'processing', 'completed', 'failed'));

CREATE INDEX IF NOT EXISTS idx_documents_user_uploaded
  ON public.documents(user_id, uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_verification_status
  ON public.documents(user_id, verification_status);

-- Ensure per-user RLS on public.documents.
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "docs_own" ON public.documents;
DROP POLICY IF EXISTS "docs_service" ON public.documents;
DROP POLICY IF EXISTS documents_owner_all ON public.documents;
DROP POLICY IF EXISTS documents_service_all ON public.documents;

CREATE POLICY documents_owner_all ON public.documents
  FOR ALL TO authenticated
  USING (user_id = (SELECT auth.uid()))
  WITH CHECK (user_id = (SELECT auth.uid()));

CREATE POLICY documents_service_all ON public.documents
  FOR ALL TO service_role
  USING (true)
  WITH CHECK (true);

GRANT SELECT, INSERT, UPDATE, DELETE ON public.documents TO authenticated, service_role;

-- Ensure private storage bucket 'documents' with 5 MB limit and jpg/png/pdf MIME types.
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'documents',
  'documents',
  false,
  5242880,
  ARRAY['image/jpeg', 'image/png', 'application/pdf']
)
ON CONFLICT (id) DO UPDATE SET
  public = false,
  file_size_limit = EXCLUDED.file_size_limit,
  allowed_mime_types = EXCLUDED.allowed_mime_types;

DROP POLICY IF EXISTS "docs_upload" ON storage.objects;
DROP POLICY IF EXISTS "docs_read" ON storage.objects;
DROP POLICY IF EXISTS "docs_delete" ON storage.objects;
DROP POLICY IF EXISTS "service_storage" ON storage.objects;
DROP POLICY IF EXISTS documents_bucket_owner_insert ON storage.objects;
DROP POLICY IF EXISTS documents_bucket_owner_select ON storage.objects;
DROP POLICY IF EXISTS documents_bucket_owner_update ON storage.objects;
DROP POLICY IF EXISTS documents_bucket_owner_delete ON storage.objects;
DROP POLICY IF EXISTS documents_bucket_service_all ON storage.objects;

CREATE POLICY documents_bucket_owner_insert ON storage.objects
  FOR INSERT TO authenticated
  WITH CHECK (
    bucket_id = 'documents'
    AND (storage.foldername(name))[1] = (SELECT auth.uid()::text)
  );

CREATE POLICY documents_bucket_owner_select ON storage.objects
  FOR SELECT TO authenticated
  USING (
    bucket_id = 'documents'
    AND (storage.foldername(name))[1] = (SELECT auth.uid()::text)
  );

CREATE POLICY documents_bucket_owner_update ON storage.objects
  FOR UPDATE TO authenticated
  USING (
    bucket_id = 'documents'
    AND (storage.foldername(name))[1] = (SELECT auth.uid()::text)
  )
  WITH CHECK (
    bucket_id = 'documents'
    AND (storage.foldername(name))[1] = (SELECT auth.uid()::text)
  );

CREATE POLICY documents_bucket_owner_delete ON storage.objects
  FOR DELETE TO authenticated
  USING (
    bucket_id = 'documents'
    AND (storage.foldername(name))[1] = (SELECT auth.uid()::text)
  );

CREATE POLICY documents_bucket_service_all ON storage.objects
  FOR ALL TO service_role
  USING (true)
  WITH CHECK (true);
