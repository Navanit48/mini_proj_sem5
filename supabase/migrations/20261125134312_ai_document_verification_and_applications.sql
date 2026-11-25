-- Extend the existing one-to-one OCR result with explicitly preliminary checks.
ALTER TABLE public.ocr_results
  ADD COLUMN IF NOT EXISTS detected_document_type TEXT,
  ADD COLUMN IF NOT EXISTS document_type_confidence NUMERIC NOT NULL DEFAULT 0
    CHECK (document_type_confidence BETWEEN 0 AND 100),
  ADD COLUMN IF NOT EXISTS verification_status TEXT NOT NULL DEFAULT 'needs_review'
    CHECK (verification_status IN ('preliminary_match', 'needs_review', 'unreadable')),
  ADD COLUMN IF NOT EXISTS validation_summary TEXT,
  ADD COLUMN IF NOT EXISTS mismatches JSONB NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS warnings JSONB NOT NULL DEFAULT '[]'::jsonb;

-- OCR output belongs to the owner of the source document.
DROP POLICY IF EXISTS "ocr_read" ON public.ocr_results;
DROP POLICY IF EXISTS "ocr_service" ON public.ocr_results;
DROP POLICY IF EXISTS ocr_results_owner_read ON public.ocr_results;
DROP POLICY IF EXISTS ocr_results_service_all ON public.ocr_results;
CREATE POLICY ocr_results_owner_read ON public.ocr_results
  FOR SELECT TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.documents AS document
      WHERE document.id = ocr_results.document_id
        AND document.user_id = (SELECT auth.uid())
    )
  );
CREATE POLICY ocr_results_service_all ON public.ocr_results
  FOR ALL TO service_role
  USING (true)
  WITH CHECK (true);
GRANT SELECT ON public.ocr_results TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.ocr_results TO service_role;

CREATE TABLE IF NOT EXISTS public.applications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  application_code TEXT NOT NULL UNIQUE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  scheme_id UUID NOT NULL REFERENCES public.schemes(id) ON DELETE RESTRICT,
  eligibility_check_id UUID REFERENCES public.eligibility_checks(id) ON DELETE SET NULL,
  status TEXT NOT NULL DEFAULT 'submitted'
    CHECK (status IN ('submitted', 'under_review', 'ai_document_verification', 'ready_for_government_submission')),
  profile_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
  eligibility_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
  submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.application_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  application_id UUID NOT NULL REFERENCES public.applications(id) ON DELETE CASCADE,
  document_id UUID REFERENCES public.documents(id) ON DELETE SET NULL,
  document_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
  attached_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (application_id, document_id)
);

CREATE TABLE IF NOT EXISTS public.application_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  application_id UUID NOT NULL REFERENCES public.applications(id) ON DELETE CASCADE,
  status TEXT NOT NULL
    CHECK (status IN ('submitted', 'under_review', 'ai_document_verification', 'ready_for_government_submission')),
  description TEXT NOT NULL,
  progress SMALLINT NOT NULL CHECK (progress BETWEEN 0 AND 100),
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (application_id, status)
);

CREATE INDEX IF NOT EXISTS idx_applications_user_submitted
  ON public.applications(user_id, submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_applications_scheme
  ON public.applications(scheme_id);
CREATE INDEX IF NOT EXISTS idx_application_documents_application
  ON public.application_documents(application_id);
CREATE INDEX IF NOT EXISTS idx_application_documents_document
  ON public.application_documents(document_id);
CREATE INDEX IF NOT EXISTS idx_application_events_application_time
  ON public.application_events(application_id, occurred_at);

ALTER TABLE public.applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.application_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.application_events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS applications_owner_read ON public.applications;
CREATE POLICY applications_owner_read ON public.applications
  FOR SELECT TO authenticated
  USING (user_id = (SELECT auth.uid()));

DROP POLICY IF EXISTS application_documents_owner_read ON public.application_documents;
CREATE POLICY application_documents_owner_read ON public.application_documents
  FOR SELECT TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.applications AS application
      WHERE application.id = application_documents.application_id
        AND application.user_id = (SELECT auth.uid())
    )
  );

DROP POLICY IF EXISTS application_events_owner_read ON public.application_events;
CREATE POLICY application_events_owner_read ON public.application_events
  FOR SELECT TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.applications AS application
      WHERE application.id = application_events.application_id
        AND application.user_id = (SELECT auth.uid())
    )
  );

GRANT SELECT ON public.applications, public.application_documents, public.application_events TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE
  ON public.applications, public.application_documents, public.application_events
  TO service_role;
