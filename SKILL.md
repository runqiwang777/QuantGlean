# QuantGlean Skill · 量研拾萃

## Purpose

Analyze a user-provided quantitative or financial research report and produce a GitHub-renderable Markdown research note. Work like a careful quantitative researcher: explain the report's value-creation mechanism, supporting evidence, assumptions, limitations, and transferability. Do not merely paraphrase the report.

QuantGlean (量研拾萃) is a lightweight analysis skill. It does not independently validate unpublished data, execute strategies, or provide investment advice. Never claim that a reported result is verified unless the source provides evidence and the analysis actually checks it.

## Workflow

### 1. Establish the source and scope

- Identify the report title, author or institution, publication date, source link, and subject when available.
- State when information is missing. Do not invent bibliographic details, data, or results.
- Determine the report's central research object, intended output, and evidence type.

### 2. Route by research type

Choose one primary type and, only when it clarifies the analysis, at most one supporting type:

1. Factor and signal research
2. Strategy and portfolio research
3. Agent and AI for quantitative research
4. Market review and industry outlook
5. Macro, asset allocation, and risk management
6. Fund and asset management research
7. Data engineering and research infrastructure
8. Policy, events, and thematic investing

Use the report's research object, intended output, and evidence to choose. For example, a ranking signal suggests factor research; target weights or trading rules suggest portfolio research; an automated research workflow suggests Agent research; a market-state outlook suggests market review. Do not force factor IC, backtests, or trading alpha onto reports where they do not apply.

### 3. Locate the contribution and explain the mechanism

Answer:

- What problem does the report address, and why does it matter?
- What is the main contribution relative to a reasonable baseline or existing process?
- What method, data, system, or evidence supports the claim?
- How could the method create value, and for whom?
- Which assumptions and conditions are necessary?
- What can fail, and what is not established by the report?
- Which parts may transfer to another market, period, asset, or research workflow?

Distinguish reported facts, the authors' interpretations, forecasts, and recommendations. Attribute claims to the report when appropriate. Separate evidence from inference and label your own inference clearly.

### 4. Analyze the type-specific dimensions

Use only dimensions relevant to the report. Adapt or omit sections rather than filling a checklist mechanically.

**Factor and signal research:** prediction target; economic rationale; signal definition and transformations; data provenance and point-in-time correctness; look-ahead and survivorship bias; IC/RankIC and portfolio tests if reported; incremental value, exposures, turnover, decay, out-of-sample stability, costs, and capacity.

**Strategy and portfolio research:** signal-to-position mapping; construction and constraints; risk budget; rebalance frequency; leverage and cash; benchmark; attribution; drawdowns; transaction and market impact costs; execution and capacity.

**Agent and AI research:** task automated and automation boundary; agent roles and workflow; state, loops, and stop conditions; data and tool use; intermediate verification; reviewer or judge design; recovery and versioning; explainability, auditability, reproducibility; comparison baseline; hallucination, model drift, privacy, latency, and operating costs.

**Market review and industry outlook:** separate realized facts from causal explanations, forecasts, and portfolio implications. Consider returns, earnings expectations, valuation, liquidity, flows, positioning, crowding, risk appetite, style, policy, rates, and currencies where relevant. Identify scenarios and observable triggers; do not force a factor-alpha conclusion.

**Macro, allocation, and risk:** transmission channels; indicator timing and revision; frequency alignment; regime definition; asset sensitivity; defense or hedge design; crisis sample adequacy; false positives and misses; structural breaks; distinguish return improvement from drawdown control.

**Fund and asset management:** performance and risk; flows and share classes; manager skill and style drift; holdings; fees; channels; fund size and capacity; team stability and organizational quality.

**Data and infrastructure:** research bottleneck; data model and provenance; point-in-time controls; quality checks; versioning; caching and compute; scalability; auditability; failure modes; maintenance cost; whether engineering choices alter statistical conclusions.

**Policy, events, and themes:** event and expectation gap; transmission chain; beneficiaries and harmed sectors; supply-chain mapping; exposure purity; orders and earnings validation; priced-in status; theme lifecycle; crowding; catalysts and falsification conditions.

### 5. Assess alpha without overclaiming

Alpha may refer to more than return prediction. Select only mechanisms supported by the report:

- **Prediction Alpha:** improved prediction of returns or relevant outcomes.
- **Risk Management Alpha:** reduced drawdown, volatility, or tail exposure.
- **Research Process Alpha:** faster research or more effective iteration.
- **Information Processing Alpha:** better extraction of signals from complex information.
- **Decision Consistency Alpha:** reduced avoidable decision noise.
- **Data Quality Alpha:** value from more accurate, timely, point-in-time data.
- **Infrastructure Alpha:** value from scalable, reliable research systems.
- **Organizational Alpha:** value from retained knowledge and collaboration.

For each mechanism discussed, state its logic, evidence, use case, failure risk, and a possible validation or improvement step. Distinguish a plausible mechanism from demonstrated, net-of-cost investment alpha.

### 6. Apply empirical checks when applicable

Only when the report includes a model, forecast, statistical test, or backtest, inspect relevant items: target and assumptions; train/validation/test separation; leakage and look-ahead; parameter selection and multiple testing; baseline; sample length and market regimes; costs and market impact; capacity; beta and style exposure; out-of-sample stability; and cross-market transfer. Report unavailable checks as unknown, not as passed.

### 7. Write the note

Use a two-layer structure: a concise quick read followed by a substantive analysis. “Concise” applies to the opening summary; do not reduce the full note to a skeletal outline when the report contains meaningful evidence and detail.

Recommended template (adapt headings to the report):

```markdown
# [Report title]: Research Note

> Source: [link or citation]
> Report date: [date or not stated]
> Primary type: [type]
> Supporting type: [type or none]
> Scope: Research and educational analysis; not investment advice.

## Quick Read
- **Takeaway:** One sentence stating the central logic and value.
- **Question:** The problem addressed.
- **Approach:** The method or evidence.
- **Conclusion:** The main finding and its qualification.
- **Contribution:** What is useful or distinctive.

## Detailed Analysis
### Background and Problem
### Method, Data, and Evidence
### Findings and Interpretation
### Contribution and Value Mechanism
### Scope, Assumptions, and Failure Modes
### Strengths and Limitations
### Reproducibility and Further Work
### Assessment
```

Include only useful sections, but cover the core question, method/evidence, conclusion, contribution, limitations, applicability, and value mechanism across the note. Use tables only when they improve comparison or traceability. Preserve source links for material claims where possible.

### 8. Maintain a report index when requested

If the user maintains a collection README, add one row for the new note with its link, a short English topic label (two or three words), report title, a single-sentence Chinese main idea (roughly 30–70 Chinese characters), date, and evidence-based recommendation markers. Use `🚀` for a clearly distinctive contribution, `🧩` for a coherent question-method-validation-application framework, and `🔁` for enough detail to support meaningful reproduction. Use only justified markers; use `-` if none apply. Do not fabricate dates, links, or reproducibility.

## Markdown and quality checks

- Produce standard GitHub-renderable Markdown.
- Keep claims traceable to the supplied report; mark uncertainty and missing evidence.
- Keep formulas readable and syntactically complete. Do not break a formula across source lines in a way that changes its meaning.
- Use consistent terminology and define specialized terms when needed.
- Do not fabricate metrics, citations, assumptions, or validation results.
- End with a balanced assessment of what the report establishes and what would need further verification.

