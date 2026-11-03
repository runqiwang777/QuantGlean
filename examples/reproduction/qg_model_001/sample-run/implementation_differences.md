# Implementation differences

- Original synthetic excess-return panel and preannounced eligibility replace any historical market universe.
- 12-1 compounds t-12 through t-2; fixed 6-1 baseline compounds t-6 through t-2.
- Equal-fraction quintiles split boundary ties symmetrically; 50% long top and 50% short bottom, no volatility matching.
- Monthly constant-notional targets; L1 target turnover, flat initial holdings; no intramonth drift/fill simulation.
- Costs are illustrative: commission/spread/impact 1/2/1bp, 100bp annual short borrow, zero roll for this fictional non-futures panel.
- Frozen calendar evaluation and paired moving-block bootstrap are analyst protocol choices.
- Training-only feature means and population scales; one fixed-alpha ridge fit, no model selection or validation refit.
- Forecast baseline is training mean; portfolio baseline is 12-1 momentum. These compare different outcomes.

Reference: see experiment ID, source/evidence and implementation choices in the frozen spec.
Synthetic assets or a user-defined modern universe differ from any original historical sample.
Monthly return accounting does not model individual futures contracts, fills, margin, or intramonth trading.
