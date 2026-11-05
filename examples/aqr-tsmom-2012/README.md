# QuantGlean case study: AQR Time Series Momentum (2012)

**Case status:** portfolio-return audit completed; underlying strategy reconstruction not possible from the published workbook alone.

This case asks two separate questions:

1. Can QuantGlean turn a real quantitative paper into a source-linked research specification?
2. Can we independently check statistics from the authors’ published strategy-return series?

It does **not** claim QuantGlean discovered or reproduced the alpha from raw market data.

## Source-backed research specification

Moskowitz, Ooi, and Pedersen study time-series momentum across 58 liquid futures and forward instruments in equity indices, currencies, commodities, and sovereign bonds. Their central result is that an instrument’s own past 12-month excess return predicts its future return. Their paper reports evidence over January 1985–December 2009 and tests alternative horizons, holding periods, and subsamples.

The strategy is time-series based: it uses each market’s own past return, rather than ranking securities against peers. The exact portfolio construction includes signal direction, volatility scaling, diversification, and transaction-cost assumptions. See the evidence map in [SOURCE.md](SOURCE.md).

## Data and rights boundary

AQR publishes a workbook titled *Time Series Momentum: Original Paper Data*. It labels the contents as the original monthly TSMOM factor series used in the 2012 paper, January 1985–December 2009, across the aggregate factor and equity, currency, fixed-income, and commodity sleeves. AQR asks users to credit AQR Capital Management, LLC and follow the terms in the workbook.

The workbook contains **portfolio return series**, not the 58 underlying instrument-level return histories, signals, volatility estimates, or positions. Therefore it supports a check of reported portfolio-level return statistics; it does not support an independent reconstruction of the strategy engine. The workbook is not included in this repository. Download it from the official [AQR data page](https://www.aqr.com/Insights/Datasets/Time-Series-Momentum-Original-Paper-Data), review its current terms, and keep it local.

**Privacy and redistribution:** do not commit or upload the workbook. The source provides the data for research and asks for attribution; that is not an open-source redistribution license.

## Result from the original-paper workbook

We locally inspected the workbook downloaded from AQR on 2026-11-05. SHA-256: `91bdbae6366ccb0693581b690236dc14862562a98ee83052c4f440f8b6ae0db8`

The workbook contains 300 monthly rows from January 1985 through December 2009. On the aggregate `TSMOM` column, the following simple descriptive calculations from the monthly return series give:

- arithmetic average return × 12: **17.08%**
- sample standard deviation × √12: **12.33%**
- annualized Sharpe from arithmetic mean / sample standard deviation × √12: **1.385**
- geometric annualized return from compounding all 300 monthly values: **17.60%**

These are calculations over the published factor-return series, not a reconstruction of the underlying 58 instruments. They are not presented as an exact match to a specific paper exhibit because the selected summary convention must first be mapped to that exhibit’s exact portfolio definition, fees, and risk scaling.

For a repeatable local calculation, run:

```powershell
python scripts/summarize-aqr-tsmom.py "D:\path\to\Time-Series-Momentum-Original-Paper-Data.xlsx"
```

The script emits only aggregate descriptive statistics and the workbook hash. It never copies the workbook or its monthly rows into repository outputs.

## What this case establishes

- The paper’s research object, signal family, sample, and key implementation dependencies can be converted into a structured research note with evidence locators.
- The public original-paper workbook provides a useful independent input for checking portfolio-level calculations.
- The current QuantGlean engine cannot validate the paper’s original result from raw inputs using this workbook alone.

## What it does not establish

- It does not prove QuantGlean discovered the time-series momentum effect.
- It does not independently recreate the signal or portfolio from instrument-level market data.
- It does not establish that the historical return is available today, investable, or predictive out of sample.
- It does not show that QuantGlean improves analysts’ accuracy or research time; that requires a separate blinded comparison against human references.

## Next evidence needed for a stronger reproduction

A raw-data reproduction requires authorized instrument-level excess-return histories for the original 58 markets, point-in-time availability, the paper’s volatility and portfolio-weight construction, and cost assumptions. The workbook does not contain those inputs. Without a data license or a provider that permits research and redistribution of derived outputs, the reproducible public case should remain at the portfolio-return audit level.
