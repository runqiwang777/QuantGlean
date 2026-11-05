# Source and evidence map

## Paper

Tobias J. Moskowitz, Yao Hua Ooi, and Lasse Heje Pedersen, “Time Series Momentum,” *Journal of Financial Economics* 104(2), 228–250 (2012), DOI [10.1016/j.jfineco.2011.11.003](https://doi.org/10.1016/j.jfineco.2011.11.003). Author-hosted paper: [PDF](https://pages.stern.nyu.edu/~lpederse/papers/TimeSeriesMomentum.pdf). AQR research page: [Time Series Momentum](https://www.aqr.com/Insights/Research/Journal-Article/Time-Series-Momentum).

## Data

AQR, [Time Series Momentum: Original Paper Data](https://www.aqr.com/Insights/Datasets/Time-Series-Momentum-Original-Paper-Data). The page identifies the workbook as the original paper data: monthly TSMOM factors, January 1985–December 2009, built from 58 underlying liquid instruments. The [AQR Data Library description](https://www.aqr.com/Insights/Datasets/About-the-AQR-Data-Library) says the workbooks contain hypothetical portfolio returns, asks for citation to AQR Capital Management, LLC, and explains that original datasets are kept static for replication. It also says to follow terms included in each workbook.

Local workbook inspected 2026-11-05:
- Filename: `Time-Series-Momentum-Original-Paper-Data.xlsx`
- SHA-256: `91bdbae6366ccb0693581b690236dc14862562a98ee83052c4f440f8b6ae0db8`
- Sheets: `TSMOM factors`, `Disclosures`
- Return columns: `TSMOM`, `TSMOM^EQ`, `TSMOM^FX`, `TSMOM^FI`, `TSMOM^CM`
- Monthly observations: 300, 1985-01-31 through 2009-12-31.

The source page requests AQR attribution and compliance with the workbook terms. This repository contains links, methodology, and aggregate derived calculations only; it does not contain the workbook or its monthly observations.

## Claims and locators

| ID | Claim used in this case | Evidence |
|---|---|---|
| P1 | The paper studies 58 liquid futures and forwards across equity indices, currencies, commodities, and sovereign bonds. | Abstract; AQR paper page |
| P2 | Past 12-month own-market excess return is the central predictor; persistence lasts about a year and partially reverses over longer horizons. | Abstract; AQR paper page |
| P3 | The paper’s main sample covers January 1985–December 2009. | Paper Figure 2 caption / sample discussion; AQR original-data page |
| P4 | AQR workbook contains aggregate and four asset-class TSMOM portfolio-return series. | Workbook cover and headers; locally inspected |
| P5 | The workbook is not instrument-level raw data; it cannot independently reproduce the signal and portfolio construction. | Workbook’s listed fields contrasted with paper’s 58-instrument method; inference |
| P6 | The strategy needs explicit signal, volatility sizing, diversification, execution, and costs to interpret results. | Paper strategy methodology and data/cost discussion |
| P7 | AQR asks users to credit AQR Capital Management, LLC and follow workbook terms. | AQR data library page |

## Interpretation boundary

P1–P4 and P6–P7 are source-supported descriptions. P5 is an inference from the published workbook’s contents and the paper’s method. The local summary statistics are calculations on the AQR-published aggregate series; they are not independent evidence of the underlying anomaly and are not a paper-exhibit match until definitions are reconciled.
