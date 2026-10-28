-- Eligibility rule definitions and per-scheme results used by the API.
CREATE TABLE IF NOT EXISTS public.scheme_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scheme_id UUID NOT NULL REFERENCES public.schemes(id) ON DELETE CASCADE,
  rule_definition JSONB NOT NULL DEFAULT '{}'::jsonb,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.eligibility_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  check_id UUID NOT NULL REFERENCES public.eligibility_checks(id) ON DELETE CASCADE,
  scheme_id UUID NOT NULL REFERENCES public.schemes(id) ON DELETE CASCADE,
  match_percentage NUMERIC NOT NULL DEFAULT 0,
  matched_rules JSONB NOT NULL DEFAULT '[]'::jsonb,
  failed_rules JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scheme_rules_scheme_id
  ON public.scheme_rules(scheme_id);
CREATE INDEX IF NOT EXISTS idx_eligibility_results_check_id
  ON public.eligibility_results(check_id);

ALTER TABLE public.scheme_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.eligibility_checks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.eligibility_results ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS scheme_rules_read_authenticated ON public.scheme_rules;
DROP POLICY IF EXISTS rules_read ON public.scheme_rules;
DROP POLICY IF EXISTS rules_service_all ON public.scheme_rules;
CREATE POLICY scheme_rules_read_authenticated ON public.scheme_rules
  FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS eligibility_checks_read_own ON public.eligibility_checks;
DROP POLICY IF EXISTS checks_own ON public.eligibility_checks;
DROP POLICY IF EXISTS checks_service ON public.eligibility_checks;
CREATE POLICY eligibility_checks_read_own ON public.eligibility_checks
  FOR SELECT TO authenticated USING (user_id = (SELECT auth.uid()));

DROP POLICY IF EXISTS eligibility_results_read_own ON public.eligibility_results;
DROP POLICY IF EXISTS results_read ON public.eligibility_results;
DROP POLICY IF EXISTS results_service ON public.eligibility_results;
CREATE POLICY eligibility_results_read_own ON public.eligibility_results
  FOR SELECT TO authenticated USING (
    EXISTS (
      SELECT 1
      FROM public.eligibility_checks AS checks
      WHERE checks.id = eligibility_results.check_id
        AND checks.user_id = (SELECT auth.uid())
    )
  );

GRANT SELECT ON public.scheme_rules TO authenticated;
GRANT SELECT ON public.eligibility_checks, public.eligibility_results TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.scheme_rules TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.eligibility_checks TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.eligibility_results TO service_role;

-- Seed the established rule definitions for current MVP schemes without
-- replacing rules that may already have been customized.
INSERT INTO public.scheme_rules (scheme_id, rule_definition)
SELECT schemes.id, seeds.rule_definition
FROM public.schemes AS schemes
JOIN (VALUES
  ('pradhan-mantri-awas-yojana', '{"operator":"and","conditions":[{"field":"annual_income","op":"lte","value":600000},{"field":"category","op":"in","value":["general","obc","sc","st","ews"]}]}'::jsonb),
  ('pm-kisan-samman-nidhi', '{"operator":"and","conditions":[{"field":"occupation","op":"eq","value":"farmer"},{"field":"land_holding_acres","op":"gt","value":0}]}'::jsonb),
  ('ayushman-bharat-pmjay', '{"operator":"or","conditions":[{"field":"is_bpl","op":"eq","value":"true"},{"field":"annual_income","op":"lte","value":100000}]}'::jsonb),
  ('national-food-security-act', '{"operator":"and","conditions":[{"field":"is_bpl","op":"eq","value":"true"},{"field":"annual_income","op":"lte","value":100000}]}'::jsonb),
  ('post-matric-scholarship-sc', '{"operator":"and","conditions":[{"field":"category","op":"eq","value":"sc"},{"field":"annual_income","op":"lte","value":250000}]}'::jsonb),
  ('stand-up-india', '{"operator":"or","conditions":[{"field":"category","op":"in","value":["sc","st"]},{"field":"gender","op":"eq","value":"female"}]}'::jsonb),
  ('mgnrega', '{"operator":"and","conditions":[{"field":"occupation","op":"in","value":["farmer","labourer","daily-wage","unemployed"]}]}'::jsonb),
  ('ujjwala-yojana-2', '{"operator":"and","conditions":[{"field":"is_bpl","op":"eq","value":"true"},{"field":"gender","op":"eq","value":"female"}]}'::jsonb),
  ('atal-pension-yojana', '{"operator":"and","conditions":[{"field":"annual_income","op":"lte","value":500000}]}'::jsonb)
) AS seeds(slug, rule_definition) ON schemes.slug = seeds.slug
WHERE NOT EXISTS (
  SELECT 1 FROM public.scheme_rules AS existing
  WHERE existing.scheme_id = schemes.id AND existing.is_active = TRUE
);
