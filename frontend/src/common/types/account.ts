// Mirrors fireguard-api's PlanName enum and PLAN_FEATURES / MOCK_PLAN_PRICES maps.
// TS enums are avoided (project's erasableSyntaxOnly compiler option forbids them).
export type PlanId = 'student' | 'basic' | 'pro' | 'enterprise' | 'government'

export const PLAN_ORDER: PlanId[] = ['student', 'basic', 'pro', 'enterprise', 'government']

export type BillingModel = 'free' | 'per-report' | 'subscription' | 'contact-sales'

export interface PlanFeatures {
  pdfAnalysis: boolean
  externalApi: boolean
}

export interface PlanDefinition {
  id: PlanId
  name: string
  tagline: string
  analysisInput: string
  reportLimitLabel: string
  billingLabel: string
  billingModel: BillingModel
  /** Mock checkout amount in LKR, matching fireguard-api's MOCK_PLAN_PRICES. Null = not self-serve. */
  mockAmount: number | null
  requiresInstitutionalEmail: boolean
  features: PlanFeatures
}

// Prices come straight from fireguard-api/app/main.py's MOCK_PLAN_PRICES so the UI
// never quotes a number the gateway wouldn't actually charge.
export const PLAN_CATALOG: Record<PlanId, PlanDefinition> = {
  student: {
    id: 'student',
    name: 'Student',
    tagline: 'Learn fire code with text-based audits.',
    analysisInput: 'Text description only',
    reportLimitLabel: '5 reports / month',
    billingLabel: 'Free',
    billingModel: 'free',
    mockAmount: null,
    requiresInstitutionalEmail: true,
    features: { pdfAnalysis: false, externalApi: false },
  },
  basic: {
    id: 'basic',
    name: 'Basic',
    tagline: 'Pay only for the audits you run.',
    analysisInput: 'Text + PDF plans',
    reportLimitLabel: '1 credit per report',
    billingLabel: 'Pay per report',
    billingModel: 'per-report',
    mockAmount: 2500,
    requiresInstitutionalEmail: false,
    features: { pdfAnalysis: true, externalApi: false },
  },
  pro: {
    id: 'pro',
    name: 'Pro',
    tagline: 'For consultants auditing continuously.',
    analysisInput: 'Text + PDF plans',
    reportLimitLabel: 'Unlimited reports',
    billingLabel: 'Subscription',
    billingModel: 'subscription',
    mockAmount: 7500,
    requiresInstitutionalEmail: false,
    features: { pdfAnalysis: true, externalApi: false },
  },
  enterprise: {
    id: 'enterprise',
    name: 'Enterprise',
    tagline: 'Embed compliance into your own systems.',
    analysisInput: 'Text + PDF plans',
    reportLimitLabel: 'Unlimited reports',
    billingLabel: 'Subscription',
    billingModel: 'subscription',
    mockAmount: 25000,
    requiresInstitutionalEmail: false,
    features: { pdfAnalysis: true, externalApi: true },
  },
  government: {
    id: 'government',
    name: 'Government',
    tagline: 'Jurisdiction-wide review and oversight.',
    analysisInput: 'Text + PDF plans',
    reportLimitLabel: 'Unlimited reports',
    billingLabel: 'Annual agreement',
    billingModel: 'contact-sales',
    mockAmount: null,
    requiresInstitutionalEmail: false,
    features: { pdfAnalysis: true, externalApi: true },
  },
}

// Matches fireguard-api/app/schemas.py::AccountResponse.
export interface AccountResponse {
  id: string
  username: string
  email: string | null
  plan: PlanId
  email_verified: boolean
  reports_used_this_month: number
  reports_remaining: number | null
  pdf_export_enabled: boolean
  chatbot_enabled: boolean
  external_api_enabled: boolean
  payment_required: boolean
}
