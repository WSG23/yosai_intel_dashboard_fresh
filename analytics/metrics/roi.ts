export const calculateROI = (revenue: number, cost: number): number => {
  return cost === 0 ? 0 : (revenue - cost) / cost;
};

export interface ABTestOutcome {
  variant: string;
  conversions: number;
  participants: number;
  revenuePerConversion: number;
  costPerParticipant: number;
}

export interface ROIResult {
  variant: string;
  roi: number;
}

export const linkABTestOutcomes = (outcomes: ABTestOutcome[]): ROIResult[] => {
  return outcomes.map(outcome => {
    const revenue = outcome.conversions * outcome.revenuePerConversion;
    const cost = outcome.participants * outcome.costPerParticipant;
    return {
      variant: outcome.variant,
      roi: calculateROI(revenue, cost),
    };
  });
};

const roi = {
  calculateROI,
  linkABTestOutcomes,
};

export default roi;
