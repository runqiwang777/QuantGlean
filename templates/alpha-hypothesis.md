# Alpha Hypothesis Card

[简体中文](alpha-hypothesis_CN.md) · [Worked example](../examples/aqr-century-trend-following/README.md)

Copy this card for one testable idea. Fill unknown fields with `Unknown`; do not infer that an unreported check passed. For process or infrastructure ideas, replace return metrics with measurable research outcomes such as error rate, time, or cost.

## Identity and provenance

- **ID / title:** [stable ID and descriptive title]
- **Status:** [Proposed / Protocol frozen / Tested / Rejected / Inconclusive]
- **Updated:** [date]
- **Source:** [report title, authors, version/date, link]
- **Locator:** [PDF page, section, exhibit, or table; specify page-number convention]
- **Source claim:** [what the authors actually establish]
- **Analyst extension:** [what this card adds; do not attribute it to the authors]
- **Evidence state:** [Source inspected / Source not accessible / Independently reproduced; specify scope]

## Hypothesis and mechanism

- **Alpha type:** [Prediction / Risk Management / Research Process / Other]
- **Testable claim:** [For population X, observable input Y predicts or improves outcome Z relative to baseline B, under conditions C.]
- **Value mechanism:** [causal or economic rationale; label unverified explanations]
- **Alternative explanation:** [exposure, selection, data artifact, or other competing account]
- **Applicability and failure conditions:** [where the mechanism could hold or break]

## Data and implementation

- **Universe and period:** [eligibility at each historical date; intended application]
- **Inputs and availability:** [vendor, publication time, revisions, point-in-time rules]
- **Transformation and action:** [signal, timing, position/workflow mapping, constraints]
- **Missing data and exclusions:** [rules defined before testing]
- **Costs and feasibility:** [fees, spreads, impact, financing, compute or human review as relevant]
- **Unavailable details:** [gaps that prevent full reproduction]

## Validation protocol — specify before running

- **Baseline and ablations:** [matched exposure/risk budget; isolate the proposed contribution]
- **Development / holdout split:** [chronology; how the holdout is protected]
- **Primary metric and decision rule:** [metric, minimum useful improvement, uncertainty rule; freeze values before testing]
- **Robustness and cost stress:** [regimes, parameter sensitivity, dependence-aware uncertainty, multiple trials]
- **Falsification:** [observable result that would reject or narrow the claim]

## Result record

- **Executed:** [Yes / No; date and code/data version if run]
- **Result and uncertainty:** [actual measured outcome, or Not run]
- **Protocol deviations:** [all deviations and whether a fresh holdout is needed]
- **Conclusion:** [Supported within stated scope / Rejected / Inconclusive / Untested]
- **Next step:** [one concrete action]

An inspected source supports a reading note. A proposed card is a research task. Neither establishes independently verified, investable alpha.
