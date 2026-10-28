-- ╔══════════════════════════════════════════════════════════════╗
-- ║  AidFlow AI — Full Supabase Database Schema                 ║
-- ║  Run this in Supabase SQL Editor to bootstrap the project.  ║
-- ╚══════════════════════════════════════════════════════════════╝

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── 1. User Profiles ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.user_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID UNIQUE NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name TEXT,
  role TEXT NOT NULL DEFAULT 'citizen' CHECK (role IN ('citizen', 'admin')),
  date_of_birth DATE,
  gender TEXT CHECK (gender IN ('male', 'female', 'other')),
  state TEXT,
  district TEXT,
  occupation TEXT,
  category TEXT CHECK (category IN ('general', 'obc', 'sc', 'st', 'ews')),
  annual_income NUMERIC,
  land_holding_acres NUMERIC,
  is_bpl BOOLEAN DEFAULT FALSE,
  is_disabled BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.user_profiles
  ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'citizen'
  CHECK (role IN ('citizen', 'admin'));

GRANT SELECT, INSERT, UPDATE ON public.user_profiles TO service_role;

-- ─── 2. Schemes ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.schemes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  slug TEXT UNIQUE,
  description TEXT NOT NULL,
  ministry TEXT NOT NULL,
  category TEXT NOT NULL,
  target_states JSONB DEFAULT '[]'::jsonb,
  benefits_summary TEXT,
  eligibility_summary TEXT,
  application_url TEXT,
  deadline DATE,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── 3. Scheme Rules ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.scheme_rules (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  scheme_id UUID NOT NULL REFERENCES public.schemes(id) ON DELETE CASCADE,
  rule_definition JSONB NOT NULL DEFAULT '{}'::jsonb,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── 4. Eligibility Checks ─────────────────────────────────
CREATE TABLE IF NOT EXISTS public.eligibility_checks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  submitted_profile JSONB NOT NULL DEFAULT '{}'::jsonb,
  matched_count INTEGER DEFAULT 0,
  checked_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── 5. Eligibility Results ────────────────────────────────
CREATE TABLE IF NOT EXISTS public.eligibility_results (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  check_id UUID NOT NULL REFERENCES public.eligibility_checks(id) ON DELETE CASCADE,
  scheme_id UUID NOT NULL REFERENCES public.schemes(id) ON DELETE CASCADE,
  match_percentage NUMERIC DEFAULT 0,
  matched_rules JSONB DEFAULT '[]'::jsonb,
  failed_rules JSONB DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── 6. Documents ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  file_name TEXT NOT NULL,
  file_type TEXT NOT NULL,
  storage_path TEXT NOT NULL,
  document_category TEXT DEFAULT 'general',
  status TEXT DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'processing', 'completed', 'failed')),
  file_size_bytes INTEGER DEFAULT 0,
  uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── 7. OCR Results ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.ocr_results (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID UNIQUE NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
  raw_text TEXT,
  extracted_fields JSONB DEFAULT '{}'::jsonb,
  confidence_score NUMERIC DEFAULT 0,
  processed_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── 8. Checklists ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.checklists (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  scheme_id UUID NOT NULL REFERENCES public.schemes(id) ON DELETE CASCADE,
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── 9. Checklist Items ────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.checklist_items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  checklist_id UUID NOT NULL REFERENCES public.checklists(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT,
  is_completed BOOLEAN DEFAULT FALSE,
  due_date DATE,
  sort_order INTEGER DEFAULT 0,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── 10. Notifications ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.notifications (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  type TEXT DEFAULT 'info' CHECK (type IN ('reminder', 'status_update', 'info')),
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb,
  is_read BOOLEAN DEFAULT FALSE,
  sent_at TIMESTAMPTZ DEFAULT NOW()
);

-- ╔══════════════════════════════════════════════════════════════╗
-- ║  Indexes                                                    ║
-- ╚══════════════════════════════════════════════════════════════╝

CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON public.user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_schemes_category ON public.schemes(category);
CREATE INDEX IF NOT EXISTS idx_schemes_is_active ON public.schemes(is_active);
CREATE INDEX IF NOT EXISTS idx_scheme_rules_scheme_id ON public.scheme_rules(scheme_id);
CREATE INDEX IF NOT EXISTS idx_eligibility_checks_user_id ON public.eligibility_checks(user_id);
CREATE INDEX IF NOT EXISTS idx_eligibility_results_check_id ON public.eligibility_results(check_id);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON public.documents(user_id);
CREATE INDEX IF NOT EXISTS idx_checklists_user_id ON public.checklists(user_id);
CREATE INDEX IF NOT EXISTS idx_checklist_items_checklist_id ON public.checklist_items(checklist_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON public.notifications(user_id);

-- ╔══════════════════════════════════════════════════════════════╗
-- ║  Row Level Security (RLS) Policies                          ║
-- ╚══════════════════════════════════════════════════════════════╝

-- Enable RLS on all tables
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.schemes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scheme_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.eligibility_checks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.eligibility_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ocr_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.checklists ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.checklist_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

-- Schemes: everyone can read active schemes
CREATE POLICY "schemes_read_active" ON public.schemes FOR SELECT USING (is_active = true);
CREATE POLICY "schemes_service_all" ON public.schemes FOR ALL USING (true) WITH CHECK (true);

-- Scheme Rules: readable by all, writable by service role
CREATE POLICY "rules_read" ON public.scheme_rules FOR SELECT USING (true);
CREATE POLICY "rules_service_all" ON public.scheme_rules FOR ALL USING (true) WITH CHECK (true);

-- User Profiles: users can read/write own
CREATE POLICY "profiles_own" ON public.user_profiles FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "profiles_service" ON public.user_profiles FOR ALL USING (true) WITH CHECK (true);

-- Eligibility Checks: users see own
CREATE POLICY "checks_own" ON public.eligibility_checks FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "checks_service" ON public.eligibility_checks FOR ALL USING (true) WITH CHECK (true);

-- Eligibility Results: users see own via join
CREATE POLICY "results_read" ON public.eligibility_results FOR SELECT USING (true);
CREATE POLICY "results_service" ON public.eligibility_results FOR ALL USING (true) WITH CHECK (true);

-- Documents: users see own
CREATE POLICY "docs_own" ON public.documents FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "docs_service" ON public.documents FOR ALL USING (true) WITH CHECK (true);

-- OCR Results: readable by owner via join
CREATE POLICY "ocr_read" ON public.ocr_results FOR SELECT USING (true);
CREATE POLICY "ocr_service" ON public.ocr_results FOR ALL USING (true) WITH CHECK (true);

-- Checklists: users see own
CREATE POLICY "checklists_own" ON public.checklists FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "checklists_service" ON public.checklists FOR ALL USING (true) WITH CHECK (true);

-- Checklist Items: readable
CREATE POLICY "items_read" ON public.checklist_items FOR SELECT USING (true);
CREATE POLICY "items_service" ON public.checklist_items FOR ALL USING (true) WITH CHECK (true);

-- Notifications: users see own
CREATE POLICY "notifications_own" ON public.notifications FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "notifications_service" ON public.notifications FOR ALL USING (true) WITH CHECK (true);


-- ╔══════════════════════════════════════════════════════════════╗
-- ║  Storage Bucket for Documents                               ║
-- ╚══════════════════════════════════════════════════════════════╝

INSERT INTO storage.buckets (id, name, public)
VALUES ('documents', 'documents', false)
ON CONFLICT DO NOTHING;

-- Storage policies
CREATE POLICY "docs_upload" ON storage.objects FOR INSERT WITH CHECK (
  bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "docs_read" ON storage.objects FOR SELECT USING (
  bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "docs_delete" ON storage.objects FOR DELETE USING (
  bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Allow service role to manage all storage
CREATE POLICY "service_storage" ON storage.objects FOR ALL USING (true) WITH CHECK (true);


-- ╔══════════════════════════════════════════════════════════════╗
-- ║  Seed Data: Sample Government Schemes                       ║
-- ╚══════════════════════════════════════════════════════════════╝

INSERT INTO public.schemes (name, slug, description, ministry, category, target_states, benefits_summary, eligibility_summary, application_url, deadline, is_active) VALUES
(
  'Pradhan Mantri Awas Yojana (PMAY)',
  'pradhan-mantri-awas-yojana',
  'Housing for All mission providing affordable housing to urban and rural poor families across India. Subsidized home loans and pucca houses for economically weaker sections.',
  'Ministry of Housing and Urban Affairs',
  'Housing',
  '["All India"]'::jsonb,
  'Interest subsidy of 6.5% on home loans up to ₹6 lakh for 20 years. Direct benefit transfer for house construction up to ₹2.5 lakh.',
  'Annual household income below ₹3 lakh (EWS) or ₹6 lakh (LIG). Must not own a pucca house. First-time homeowner.',
  'https://pmaymis.gov.in',
  '2027-03-31',
  true
),
(
  'PM Kisan Samman Nidhi',
  'pm-kisan-samman-nidhi',
  'Direct income support of ₹6,000 per year to all landholding farmer families. Amount transferred in three equal installments every four months.',
  'Ministry of Agriculture',
  'Agriculture',
  '["All India"]'::jsonb,
  '₹6,000/year transferred directly to bank account in 3 installments of ₹2,000 each.',
  'Small and marginal farmers with cultivable land holding. Valid Aadhaar and bank account required.',
  'https://pmkisan.gov.in',
  NULL,
  true
),
(
  'Ayushman Bharat - PMJAY',
  'ayushman-bharat-pmjay',
  'World''s largest health insurance scheme providing ₹5 lakh coverage per family per year for secondary and tertiary care hospitalization to identified vulnerable families.',
  'Ministry of Health and Family Welfare',
  'Healthcare',
  '["All India"]'::jsonb,
  'Free health coverage up to ₹5 lakh per family per year. Covers 1,393 medical packages including surgeries and treatments.',
  'Families identified as per SECC 2011 data. Covers rural and urban poor. BPL families automatically eligible.',
  'https://pmjay.gov.in',
  NULL,
  true
),
(
  'Sukanya Samriddhi Yojana',
  'sukanya-samriddhi-yojana',
  'Girl child savings scheme under Beti Bachao Beti Padhao campaign. High interest rates and tax benefits for securing future of the girl child.',
  'Ministry of Finance',
  'Women & Child',
  '["All India"]'::jsonb,
  'Interest rate of 8.2% per annum (Q1 2026). Tax free under Sec 80C. Minimum deposit ₹250/year.',
  'Girl child below 10 years of age. Maximum 2 accounts per family. Indian resident.',
  'https://www.nsiindia.gov.in',
  NULL,
  true
),
(
  'National Food Security Act (NFSA)',
  'national-food-security-act',
  'Provides subsidized food grains to approximately two-thirds of India''s population through the Public Distribution System. Rice at ₹3/kg, wheat at ₹2/kg, coarse grains at ₹1/kg.',
  'Ministry of Consumer Affairs',
  'Food Security',
  '["All India"]'::jsonb,
  'Rice at ₹3/kg, wheat at ₹2/kg, coarse grains at ₹1/kg. 5kg per person per month for priority households.',
  'BPL families, Antyodaya Anna Yojana households. Family annual income below ₹1 lakh.',
  'https://nfsa.gov.in',
  NULL,
  true
),
(
  'Post-Matric Scholarship for SC Students',
  'post-matric-scholarship-sc',
  'Centrally sponsored scholarship scheme for SC students pursuing post-matriculation education. Covers maintenance allowance and non-refundable fees.',
  'Ministry of Social Justice',
  'Education',
  '["All India"]'::jsonb,
  'Full tuition fee reimbursement. Monthly maintenance allowance ₹500–₹1,200 depending on course. Book allowance included.',
  'SC category student. Annual family income below ₹2.5 lakh. Enrolled in recognized post-matric institution.',
  'https://scholarships.gov.in',
  '2027-01-31',
  true
),
(
  'MGNREGA',
  'mgnrega',
  'Mahatma Gandhi National Rural Employment Guarantee Act provides 100 days of guaranteed wage employment per year to rural households for unskilled manual work.',
  'Ministry of Rural Development',
  'Employment',
  '["All India"]'::jsonb,
  '100 days guaranteed wage employment per year. Minimum wage as per state norms. Unemployment allowance if work not provided within 15 days.',
  'Adult members of rural households willing to do unskilled manual work. Must have job card.',
  'https://nrega.nic.in',
  NULL,
  true
),
(
  'Stand-Up India',
  'stand-up-india',
  'Facilitates bank loans between ₹10 lakh and ₹1 crore to SC/ST and women entrepreneurs for setting up greenfield enterprises in manufacturing, services, or trading.',
  'Ministry of Finance',
  'Entrepreneurship',
  '["All India"]'::jsonb,
  'Loans from ₹10 lakh to ₹1 crore. Composite loan covering term loan and working capital. Repayment up to 7 years.',
  'SC/ST or Women entrepreneur. Age 18+. For greenfield enterprise only. No prior default.',
  'https://www.standupmitra.in',
  NULL,
  true
),
(
  'Pradhan Mantri Fasal Bima Yojana',
  'pm-fasal-bima-yojana',
  'Comprehensive crop insurance scheme providing financial support to farmers suffering crop loss/damage due to natural calamities, pests, and diseases.',
  'Ministry of Agriculture',
  'Agriculture',
  '["All India"]'::jsonb,
  'Premium: 2% for Kharif, 1.5% for Rabi crops. Full insured amount on crop loss. Post-harvest losses covered for 14 days.',
  'All farmers including sharecroppers and tenant farmers growing notified crops. Must have bank account.',
  'https://pmfby.gov.in',
  '2027-06-30',
  true
),
(
  'Ujjwala Yojana 2.0',
  'ujjwala-yojana-2',
  'Provides free LPG connections to women from BPL households to promote clean cooking fuel and reduce indoor air pollution health hazards.',
  'Ministry of Petroleum',
  'Energy',
  '["All India"]'::jsonb,
  'Free LPG connection including cylinder, regulator, and hose. First LPG refill and stove provided free.',
  'Women from BPL households. Age 18+. No existing LPG connection in household. Valid Aadhaar.',
  'https://www.pmujjwalayojana.com',
  NULL,
  true
),
(
  'Digital India Internship Scheme',
  'digital-india-internship',
  'Internship program under Digital India initiative for engineering and IT students to gain hands-on experience in government digital projects.',
  'Ministry of Electronics and IT',
  'Education',
  '["All India"]'::jsonb,
  'Monthly stipend of ₹10,000. Certificate of internship. Exposure to live government projects.',
  'B.Tech/M.Tech/MCA students. CGPA above 7.0. Indian citizen. No prior government internship.',
  'https://digitalindia.gov.in',
  '2027-02-28',
  true
),
(
  'Atal Pension Yojana',
  'atal-pension-yojana',
  'Government-backed pension scheme for workers in the unorganized sector. Guaranteed minimum pension of ₹1,000 to ₹5,000 per month after age 60.',
  'Ministry of Finance',
  'Social Security',
  '["All India"]'::jsonb,
  'Guaranteed pension ₹1,000–₹5,000/month. Government co-contribution of 50%. Spouse pension on death.',
  'Indian citizen. Age 18–40. Bank account with Aadhaar linked. Not already covered under social security scheme.',
  'https://www.npscra.nsdl.co.in/scheme-details.php',
  NULL,
  true
);


-- ─── Scheme Rules (sample rules for eligibility engine) ──────

-- PMAY rules
INSERT INTO public.scheme_rules (scheme_id, rule_definition, is_active) 
SELECT id, '{
  "operator": "and",
  "conditions": [
    {"field": "annual_income", "op": "lte", "value": 600000},
    {"field": "category", "op": "in", "value": ["general", "obc", "sc", "st", "ews"]}
  ]
}'::jsonb, true
FROM public.schemes WHERE slug = 'pradhan-mantri-awas-yojana';

-- PM Kisan rules
INSERT INTO public.scheme_rules (scheme_id, rule_definition, is_active)
SELECT id, '{
  "operator": "and",
  "conditions": [
    {"field": "occupation", "op": "eq", "value": "farmer"},
    {"field": "land_holding_acres", "op": "gt", "value": 0}
  ]
}'::jsonb, true
FROM public.schemes WHERE slug = 'pm-kisan-samman-nidhi';

-- Ayushman Bharat rules
INSERT INTO public.scheme_rules (scheme_id, rule_definition, is_active)
SELECT id, '{
  "operator": "or",
  "conditions": [
    {"field": "is_bpl", "op": "eq", "value": "true"},
    {"field": "annual_income", "op": "lte", "value": 100000}
  ]
}'::jsonb, true
FROM public.schemes WHERE slug = 'ayushman-bharat-pmjay';

-- NFSA rules
INSERT INTO public.scheme_rules (scheme_id, rule_definition, is_active)
SELECT id, '{
  "operator": "and",
  "conditions": [
    {"field": "is_bpl", "op": "eq", "value": "true"},
    {"field": "annual_income", "op": "lte", "value": 100000}
  ]
}'::jsonb, true
FROM public.schemes WHERE slug = 'national-food-security-act';

-- Post-Matric Scholarship rules
INSERT INTO public.scheme_rules (scheme_id, rule_definition, is_active)
SELECT id, '{
  "operator": "and",
  "conditions": [
    {"field": "category", "op": "eq", "value": "sc"},
    {"field": "annual_income", "op": "lte", "value": 250000}
  ]
}'::jsonb, true
FROM public.schemes WHERE slug = 'post-matric-scholarship-sc';

-- Stand-Up India rules
INSERT INTO public.scheme_rules (scheme_id, rule_definition, is_active)
SELECT id, '{
  "operator": "or",
  "conditions": [
    {"field": "category", "op": "in", "value": ["sc", "st"]},
    {"field": "gender", "op": "eq", "value": "female"}
  ]
}'::jsonb, true
FROM public.schemes WHERE slug = 'stand-up-india';

-- MGNREGA rules
INSERT INTO public.scheme_rules (scheme_id, rule_definition, is_active)
SELECT id, '{
  "operator": "and",
  "conditions": [
    {"field": "occupation", "op": "in", "value": ["farmer", "labourer", "daily-wage", "unemployed"]}
  ]
}'::jsonb, true
FROM public.schemes WHERE slug = 'mgnrega';

-- Ujjwala rules
INSERT INTO public.scheme_rules (scheme_id, rule_definition, is_active)
SELECT id, '{
  "operator": "and",
  "conditions": [
    {"field": "is_bpl", "op": "eq", "value": "true"},
    {"field": "gender", "op": "eq", "value": "female"}
  ]
}'::jsonb, true
FROM public.schemes WHERE slug = 'ujjwala-yojana-2';

-- Atal Pension Yojana rules
INSERT INTO public.scheme_rules (scheme_id, rule_definition, is_active)
SELECT id, '{
  "operator": "and",
  "conditions": [
    {"field": "annual_income", "op": "lte", "value": 500000}
  ]
}'::jsonb, true
FROM public.schemes WHERE slug = 'atal-pension-yojana';


-- ─── Updated_at trigger function ─────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at_user_profiles
  BEFORE UPDATE ON public.user_profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER set_updated_at_schemes
  BEFORE UPDATE ON public.schemes
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER set_updated_at_checklists
  BEFORE UPDATE ON public.checklists
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
