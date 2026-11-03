# Implementation differences

- Original synthetic monthly excess returns replace the original 67-market long-history sample.
- 36-month sample covariance, annual volatility floor 1%, target volatility 10%, gross leverage capped at 2.
- Average equal-risk horizon weights then covariance scale; lag one monthly period.
- Reset constant-notional target exposures monthly; no intramonth execution or wealth-normalized drift.
- Illustrative costs are explicit but not calibrated: commission 1bp, spread 2bp, impact 1bp per unit turnover; annual financing 100bp above unit gross; roll 1bp per unit exposure/month.
- Fixed evaluation period and paired 6-month block bootstrap are analyst choices, not source-paper reproductions.

Reference: QG-TF-001; see the original paper source/evidence links in the frozen spec.
Synthetic assets or a user-defined modern universe differ from the original historical sample.
Monthly return accounting does not model individual futures contracts, fills, margin, or intramonth trading.
