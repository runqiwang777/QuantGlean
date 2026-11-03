# QG-MODEL-001 analyst research design

This original note proposes a fixed-split ridge experiment. It is not an external paper result.

## D1 — causal features

At holding month t, momentum compounds simple excess returns t-12 through t-2; reversal is minus t-1 return; volatility is the annualized sample standard deviation over t-12 through t-1.

## D2 — model and validation

Fit feature means/scales and one ridge model only on eligible training rows. Alpha is fixed at 1. Compare validation/test MSE with the constant training-mean predictor. Portfolio diagnostics rank the prediction and separately compare with fixed 12-1 momentum. There is no tuning, refit on validation, or untouched real-world holdout claim.

## References and differences

Momentum convention context: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_mom_factor.html
Optional Qlib model API: https://qlib.readthedocs.io/en/latest/start/integration.html
The equal-fraction synthetic portfolios are not the French size/value-weighted momentum factor.
