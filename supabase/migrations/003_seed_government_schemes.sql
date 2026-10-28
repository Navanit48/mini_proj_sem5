INSERT INTO public.schemes (
  name, slug, description, ministry, category, target_states,
  benefits_summary, eligibility_summary, application_url, deadline, is_active
) VALUES
(
  'Pradhan Mantri Awas Yojana (PMAY)', 'pradhan-mantri-awas-yojana',
  'Housing for All mission providing affordable housing to urban and rural poor families across India. Subsidized home loans and pucca houses for economically weaker sections.',
  'Ministry of Housing and Urban Affairs', 'Housing', '["All India"]'::jsonb,
  'Interest subsidy of 6.5% on home loans up to ₹6 lakh for 20 years. Direct benefit transfer for house construction up to ₹2.5 lakh.',
  'Annual household income below ₹3 lakh (EWS) or ₹6 lakh (LIG). Must not own a pucca house. First-time homeowner.',
  'https://pmaymis.gov.in', '2027-03-31', true
),
(
  'PM Kisan Samman Nidhi', 'pm-kisan-samman-nidhi',
  'Direct income support of ₹6,000 per year to all landholding farmer families. Amount transferred in three equal installments every four months.',
  'Ministry of Agriculture', 'Agriculture', '["All India"]'::jsonb,
  '₹6,000/year transferred directly to bank account in 3 installments of ₹2,000 each.',
  'Small and marginal farmers with cultivable land holding. Valid Aadhaar and bank account required.',
  'https://pmkisan.gov.in', NULL, true
),
(
  'Ayushman Bharat - PMJAY', 'ayushman-bharat-pmjay',
  'World''s largest health insurance scheme providing ₹5 lakh coverage per family per year for secondary and tertiary care hospitalization to identified vulnerable families.',
  'Ministry of Health and Family Welfare', 'Healthcare', '["All India"]'::jsonb,
  'Free health coverage up to ₹5 lakh per family per year. Covers 1,393 medical packages including surgeries and treatments.',
  'Families identified as per SECC 2011 data. Covers rural and urban poor. BPL families automatically eligible.',
  'https://pmjay.gov.in', NULL, true
),
(
  'Sukanya Samriddhi Yojana', 'sukanya-samriddhi-yojana',
  'Girl child savings scheme under Beti Bachao Beti Padhao campaign. High interest rates and tax benefits for securing future of the girl child.',
  'Ministry of Finance', 'Women & Child', '["All India"]'::jsonb,
  'Interest rate of 8.2% per annum (Q1 2026). Tax free under Sec 80C. Minimum deposit ₹250/year.',
  'Girl child below 10 years of age. Maximum 2 accounts per family. Indian resident.',
  'https://www.nsiindia.gov.in', NULL, true
),
(
  'National Food Security Act (NFSA)', 'national-food-security-act',
  'Provides subsidized food grains to approximately two-thirds of India''s population through the Public Distribution System. Rice at ₹3/kg, wheat at ₹2/kg, coarse grains at ₹1/kg.',
  'Ministry of Consumer Affairs', 'Food Security', '["All India"]'::jsonb,
  'Rice at ₹3/kg, wheat at ₹2/kg, coarse grains at ₹1/kg. 5kg per person per month for priority households.',
  'BPL families, Antyodaya Anna Yojana households. Family annual income below ₹1 lakh.',
  'https://nfsa.gov.in', NULL, true
),
(
  'Post-Matric Scholarship for SC Students', 'post-matric-scholarship-sc',
  'Centrally sponsored scholarship scheme for SC students pursuing post-matriculation education. Covers maintenance allowance and non-refundable fees.',
  'Ministry of Social Justice', 'Education', '["All India"]'::jsonb,
  'Full tuition fee reimbursement. Monthly maintenance allowance ₹500–₹1,200 depending on course. Book allowance included.',
  'SC category student. Annual family income below ₹2.5 lakh. Enrolled in recognized post-matric institution.',
  'https://scholarships.gov.in', '2027-01-31', true
),
(
  'MGNREGA', 'mgnrega',
  'Mahatma Gandhi National Rural Employment Guarantee Act provides 100 days of guaranteed wage employment per year to rural households for unskilled manual work.',
  'Ministry of Rural Development', 'Employment', '["All India"]'::jsonb,
  '100 days guaranteed wage employment per year. Minimum wage as per state norms. Unemployment allowance if work not provided within 15 days.',
  'Adult members of rural households willing to do unskilled manual work. Must have job card.',
  'https://nrega.nic.in', NULL, true
),
(
  'Stand-Up India', 'stand-up-india',
  'Facilitates bank loans between ₹10 lakh and ₹1 crore to SC/ST and women entrepreneurs for setting up greenfield enterprises in manufacturing, services, or trading.',
  'Ministry of Finance', 'Entrepreneurship', '["All India"]'::jsonb,
  'Loans from ₹10 lakh to ₹1 crore. Composite loan covering term loan and working capital. Repayment up to 7 years.',
  'SC/ST or Women entrepreneur. Age 18+. For greenfield enterprise only. No prior default.',
  'https://www.standupmitra.in', NULL, true
),
(
  'Pradhan Mantri Fasal Bima Yojana', 'pm-fasal-bima-yojana',
  'Comprehensive crop insurance scheme providing financial support to farmers suffering crop loss/damage due to natural calamities, pests, and diseases.',
  'Ministry of Agriculture', 'Agriculture', '["All India"]'::jsonb,
  'Premium: 2% for Kharif, 1.5% for Rabi crops. Full insured amount on crop loss. Post-harvest losses covered for 14 days.',
  'All farmers including sharecroppers and tenant farmers growing notified crops. Must have bank account.',
  'https://pmfby.gov.in', '2027-06-30', true
),
(
  'Ujjwala Yojana 2.0', 'ujjwala-yojana-2',
  'Provides free LPG connections to women from BPL households to promote clean cooking fuel and reduce indoor air pollution health hazards.',
  'Ministry of Petroleum', 'Energy', '["All India"]'::jsonb,
  'Free LPG connection including cylinder, regulator, and hose. First LPG refill and stove provided free.',
  'Women from BPL households. Age 18+. No existing LPG connection in household. Valid Aadhaar.',
  'https://www.pmujjwalayojana.com', NULL, true
),
(
  'Digital India Internship Scheme', 'digital-india-internship',
  'Internship program under Digital India initiative for engineering and IT students to gain hands-on experience in government digital projects.',
  'Ministry of Electronics and IT', 'Education', '["All India"]'::jsonb,
  'Monthly stipend of ₹10,000. Certificate of internship. Exposure to live government projects.',
  'B.Tech/M.Tech/MCA students. CGPA above 7.0. Indian citizen. No prior government internship.',
  'https://digitalindia.gov.in', '2027-02-28', true
),
(
  'Atal Pension Yojana', 'atal-pension-yojana',
  'Government-backed pension scheme for workers in the unorganized sector. Guaranteed minimum pension of ₹1,000 to ₹5,000 per month after age 60.',
  'Ministry of Finance', 'Social Security', '["All India"]'::jsonb,
  'Guaranteed pension ₹1,000–₹5,000/month. Government co-contribution of 50%. Spouse pension on death.',
  'Indian citizen. Age 18–40. Bank account with Aadhaar linked. Not already covered under social security scheme.',
  'https://www.npscra.nsdl.co.in/scheme-details.php', NULL, true
)
ON CONFLICT (slug) DO NOTHING;
