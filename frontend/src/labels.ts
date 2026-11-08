// Plain-English labels shown to analysts instead of internal codes.

export const ALERT_TYPE_LABEL: Record<string, string> = {
  UPI_MULE_CHAIN: 'UPI mule pattern',
  STRUCTURING: 'Cash just under ₹50,000',
  MULE_ACCOUNT: 'Money passed straight through',
  LAYERING: 'Layering chain',
  VELOCITY_ABUSE: 'Rapid repeated payments',
  FAN_IN_AGGREGATION: 'Many payers into one account',
  FAN_OUT_DISPERSION: 'One account paying many',
  ISOLATION_FOREST: 'Unusual transaction (ML)',
};

export const alertTypeLabel = (t?: string | null) => (t ? ALERT_TYPE_LABEL[t] ?? t.replace(/_/g, ' ').toLowerCase() : '—');

export const TIER_LABEL: Record<string, string> = {
  TIER_1_URGENT: 'Tier 1 · urgent',
  TIER_2_PRIORITY: 'Tier 2 · priority',
  TIER_3_ROUTINE: 'Tier 3 · routine',
};

export const REVIEW_LABEL: Record<string, string> = {
  AGREE: 'Approved',
  DISAGREE: 'Disagreed',
  OVERRIDE: 'Decision changed',
};

/** Sort key so the most urgent cases come first: Tier 1, 2, 3, then "don't file". */
export const urgencyRank = (decision?: string | null, tier?: string | null) =>
  decision === 'FILE_STR' ? ({ TIER_1_URGENT: 0, TIER_2_PRIORITY: 1, TIER_3_ROUTINE: 2 } as Record<string, number>)[tier ?? ''] ?? 2 : 3;

const PLANNER_KEY = 'sentinelgraph.plannerMode';
export const getPlannerMode = (): 'static' | 'adaptive' => {
  try {
    return localStorage.getItem(PLANNER_KEY) === 'adaptive' ? 'adaptive' : 'static';
  } catch {
    return 'static';
  }
};
export const setPlannerMode = (mode: 'static' | 'adaptive') => {
  try {
    localStorage.setItem(PLANNER_KEY, mode);
  } catch {
    /* storage unavailable — the default plan is used */
  }
};

/** Review queue order used everywhere: unreviewed first, then most urgent, then newest. */
export const byReviewOrder = <T extends { analyst_review?: string | null; filing_decision?: string | null; filing_tier?: string | null; created_at: string }>(a: T, b: T) =>
  (a.analyst_review ? 1 : 0) - (b.analyst_review ? 1 : 0) ||
  urgencyRank(a.filing_decision, a.filing_tier) - urgencyRank(b.filing_decision, b.filing_tier) ||
  new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
