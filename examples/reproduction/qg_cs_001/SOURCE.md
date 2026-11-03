# QG-CS-001 source and analyst choices

Primary source: Kenneth R. French, Monthly Momentum Factor construction notes.
URL: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_mom_factor.html
Inspected 2026-11-03; source HTML SHA256: c7ed8899d0074238675c4267bdaf6d02887c562a4894c6da223aa1562f38c77a

## E1 — formation window

The source describes a momentum sort using prior months 2 through 12, omitting the immediately preceding month.

## E2 — original construction boundary

Its momentum factor combines size-conditioned value-weighted portfolios and specific historical stock eligibility. QuantGlean instead tests equal-fraction quintiles on original fictional excess returns. The fixed 6-1 comparator, costs, universe, evaluation and bootstrap are analyst-defined choices.

We link the source; no source page, market return file or chart is redistributed.
