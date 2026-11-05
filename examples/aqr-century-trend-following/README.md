# Worked example: from a trend-following paper to a research task

[简体中文](README_CN.md) · [Source and evidence map](SOURCE.md) · [Blank card](../../templates/alpha-hypothesis.md)

> An authored, source-checked demonstration of QuantGlean. It is not an archived model benchmark or a replicated backtest. Prepared 2026-10-30.
> Source: Hurst, Ooi, and Pedersen, *A Century of Evidence on Trend-Following Investing*, 2017 working-paper version. See [SOURCE.md](SOURCE.md) for the exact PDF and page convention.
> Primary type: Strategy and portfolio research. Supporting type: Factor and signal research.

## Input

Supply [`SKILL.md`](../../SKILL.md), the exact PDF linked in SOURCE.md, and the [card template](../../templates/alpha-hypothesis.md). A link alone is insufficient if the assistant cannot retrieve it.

```text
Analyze A Century of Evidence on Trend-Following Investing using QuantGlean.
Use the 26-page working-paper version specified in SOURCE.md.
Output English, with a short quick read followed by detailed analysis.
Focus on how signal design, risk allocation, and implementation interact.
Cite one-based PDF pages/exhibits. Separate source claims from your inference.
Propose one testable extension in the attached Alpha Hypothesis Card format.
Do not fabricate performance statistics or claim that a backtest was run.
```

The prompt is a reusable input specification. The note below is an edited reference output; it does not guarantee identical output from a particular model.

## Quick read

- **Question:** How much confidence should a researcher place in a strategy supported by a long historical sample?
- **Source takeaway:** The authors present long-run evidence for trend following; the design and reported results are located in E1–E4 of the [evidence map](SOURCE.md#evidence-map--证据定位).
- **Contribution as assessed here:** A useful research baseline should specify both the trading signal and the surrounding portfolio construction. Otherwise, an apparent signal improvement may be a risk-budget change.
- **Practical implication:** Treat the report as a starting point for controlled experiments. Preserve the distinction between historical evidence, an economic explanation, and an executable strategy.

## Detailed analysis

### Background and research object

This note routes the report to portfolio research because the object of interest is a trading process with multiple interacting choices. The signal lens supports the analysis, but ranking assets by cross-sectional attractiveness would answer a different question. A reading that stops at the direction rule misses the decisions needed to obtain portfolio returns.

For a new researcher, the hard problem is attribution: how much comes from the information in the signal, and how much from sizing, diversification, leverage, or implementation? This is the question our proposed experiment isolates.

### Method and evidence

Use E1–E3 to reconstruct a dependency chain: eligible instruments → observable returns → signal → risk allocation → execution and costs. Each arrow needs a time convention. A portfolio calculated using a month-end close cannot automatically be assumed executable at that same close after all inputs are known.

Maintain separate records for the report's specification and your implementation choices. If a zero-signal convention, execution lag, or missing-data rule is not recovered from the source and appendices, record the gap. Do not quietly fill it in and call the result an exact replication.

### Findings and interpretation

E4 is a source-reported result, not a calculation reproduced here. The important inference is limited: historical breadth is a useful challenge to a narrow sample story, but it does not remove all model-selection uncertainty. Historical extension and genuinely unseen forward testing are different forms of evidence.

E5 should prompt a timing question: could an investor identify those windows before they ended? A retrospective stress description can help characterize a strategy, but it is not a live crisis-entry rule. A future test should define stress episodes separately from the strategy outcome and retain failures as well as successes.

### Value mechanism and limitations — analyst interpretation

**Prediction hypothesis:** persistent price adjustment could make past direction informative. Demonstrating a historical association alone does not identify its cause; alternative explanations require separate tests.

**Portfolio hypothesis:** diversifying across signal horizons may reduce dependence on a single lookback choice. That is a proposed extension, not a claim that the paper establishes the ensemble's superiority to a matched single-horizon baseline.

**Risk-management implication:** a changing strategy exposure could complement a traditional allocation. This must be evaluated at a matched risk budget and with recovery speed, tail behavior, and implementation included. A useful complement need not protect every abrupt reversal.

Three practical limitations follow. First, historical instrument availability can be confused with a universe constructed from today's survivors. Second, proxy returns must be separated from actually tradable contracts; E6 makes this especially relevant. Third, omitted or uncertain costs in E3 justify sensitivity analysis rather than a single confident net-return claim.

### Reproduction and further work

Start with one modern, documented universe whose individual contracts, rolls, timestamps, and financing conventions can be audited. Save a data manifest and code version. Reconstruct the baseline before trying improvements. Compare matched risk and leverage; report turnover and costs alongside performance. Label any departure from the source explicitly.

The card below narrows the work to one attribution question. It deliberately leaves unavailable data and unexecuted results visible.

## Filled Alpha Hypothesis Card

### Identity and provenance

- **ID / title:** QG-TF-001 — Does a multi-horizon ensemble add value at matched risk?
- **Status / updated:** Proposed / 2026-10-30. Protocol not yet frozen.
- **Source / locator:** [SOURCE.md](SOURCE.md), E2. Evidence state: source inspected; no independent replication.
- **Source claim:** Strategy specification in E2.
- **Analyst extension:** Test incremental ensemble value against a fixed single-horizon baseline; no superiority is attributed to the authors.

### Hypothesis and mechanism

- **Alpha type:** Prediction / portfolio construction.
- **Testable claim:** On a specified modern futures universe, the source-style ensemble improves net Sharpe relative to a fixed 12-month direction baseline under the same ex ante risk budget.
- **Mechanism:** Averaging horizons might reduce sensitivity to a poorly chosen time scale. This is unverified.
- **Alternative explanation:** Differences may arise from leverage, turnover, exposures, or cost assumptions rather than better information.
- **Failure conditions:** Choppy reversals, extra trading costs, redundant signals, or improvements confined to one selected sample.

### Data and implementation

- **Universe / period:** Not yet selected. Freeze historical eligibility and sample boundaries before results are computed. Do not select instruments from realized winners.
- **Inputs / availability:** Contract prices, rolls, multipliers, financing, and executable cost estimates are needed. Vendor and timestamp rules are unknown pending data selection.
- **Transformation / action:** Use E2 as the construction reference; lock volatility estimation, weight aggregation, leverage limits, and execution lag. Resolve missing conventions before testing.
- **Missing data / exclusions:** Record incomplete histories; define eligibility and warm-up in advance. Do not backfill positions using future availability.
- **Costs / feasibility:** Measure turnover and apply contract-specific costs plus a stress scenario; include financing and roll implementation. Values are not yet estimated.
- **Unavailable details:** Audited data, full implementation specification, and realistic cost calibration.

### Proposed validation protocol — not executed

- **Baseline / ablations:** Fixed 12-month baseline; ensemble; individual short-horizon variants as diagnostics. Match risk budgets and constraints. Do not choose the best holdout baseline retrospectively.
- **Split:** Use chronological development and a reserved external period. Any already-inspected period is not genuinely unseen; log prior access and add prospective evidence if needed.
- **Primary metric / rule:** Net Sharpe difference versus the baseline. Proposed research rule: support an improvement only if the difference is positive and the lower bound of a dependence-aware 95% bootstrap interval exceeds zero; an upper bound at or below zero rejects the positive-increment claim; otherwise mark inconclusive. Freeze the resampling design before execution.
- **Robustness:** Compare cost stress, market subgroups, horizon ablations, realized risk, turnover, and leverage. Record all trials and distinguish secondary diagnostics from the primary test.
- **Falsification:** A rejected primary claim, or an apparent benefit explained entirely by unmatched exposure, would remove the ensemble's claimed incremental value in this setting. A future deployment would require a separate economic-materiality threshold.

### Result record

- **Executed:** No.
- **Result / uncertainty:** Not run; no measured return, Sharpe, or confidence interval.
- **Protocol deviations:** Not applicable yet.
- **Conclusion:** Untested hypothesis; no verified investment alpha.
- **Next step:** Select a documented dataset and freeze the implementation, chronology, and decision rule before calculating outcomes.

## Analyst review of this example

**What was checked:** source identity and PDF length; strategy and cost passages; exhibit locators and captions. No source PDF or figures are republished in this example.

**What the note does well:** it identifies an attribution problem, separates source claims from the proposed extension, and turns uncertainty into a bounded research task.

**What still limits it:** there is no executable implementation, validated data manifest, or measured result. The missing details are part of the task, not evidence that the method works.

**What to check in another assistant's output:** whether it uses the right PDF version, treats historical stress windows as retrospective, and keeps the filled card's status untested. A fluent answer that invents a Sharpe improvement fails this example.
