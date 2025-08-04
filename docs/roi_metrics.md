# ROI Metrics Methodology

Return on investment (ROI) for A/B experiments is derived by pairing each test outcome with cost and revenue assumptions. The helper in `analytics/metrics/roi.ts` maps raw A/B results to ROI values using the formula:

```
ROI = (revenue - cost) / cost
```

where revenue is computed from conversions and expected revenue per conversion, and cost derives from participants and their cost per acquisition. The utility returns ROI for each variant, enabling rapid comparison of experimental outcomes.
