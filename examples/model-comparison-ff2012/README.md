# One-paper model comparison: Fama–French international momentum

[简体中文](README_CN.md)

**Result (one run per arm):** Sol and a later exploratory Sol + QuantGlean run produced identical complete monthly factor series. Luna and Luna + QuantGlean both included duplicate rows from other sections of the source files, so neither produced a valid monthly series. This pilot does **not** show that QuantGlean improved reproduction or alpha quality.

The common task asked Sol, Luna, and Luna + QuantGlean to read Fama and French, [*Size, Value, and Momentum in International Stock Returns*](https://www.johnhcochrane.com/s/Fama_French_size_value_momentum_JFE.pdf), and reconstruct four regional winner-minus-loser monthly factors from the [Ken French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html). The last arm additionally read the repository's generic `SKILL.md`. Each arm had one isolated attempt and could read only the four six-portfolio input ZIPs. The official Mom factor ZIPs were held for scoring.

## Official data supplied

The four regional portfolio ZIPs and four official Mom factor ZIPs were downloaded on 2026-11-05 into `D:\Github\QuantGlean\local-work\source-inputs\ff2012`. The paper and library data belong to their respective authors/providers; their raw files stay in ignored local work and are not redistributed by this repository. To obtain them, use the official links below.

| Region | Six size × momentum portfolios | Official Mom factor |
|---|---|---|
| North America | [CSV ZIP](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/North_America_6_Portfolios_ME_Prior_12_2_CSV.zip) | [CSV ZIP](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/North_America_Mom_Factor_CSV.zip) |
| Europe | [CSV ZIP](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Europe_6_Portfolios_ME_Prior_12_2_CSV.zip) | [CSV ZIP](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Europe_Mom_Factor_CSV.zip) |
| Japan | [CSV ZIP](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Japan_6_Portfolios_ME_Prior_12_2_CSV.zip) | [CSV ZIP](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Japan_Mom_Factor_CSV.zip) |
| Asia Pacific ex Japan | [CSV ZIP](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Asia_Pacific_ex_Japan_6_Portfolios_ME_Prior_12_2_CSV.zip) | [CSV ZIP](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Asia_Pacific_ex_Japan_MOM_Factor_CSV.zip) |

The official files identify the data vintage as **202609 Bloomberg**. Each region has 431 overlapping monthly observations, November 1990–September 2026. This is a current-vintage published-portfolio calculation, not the paper's original security-level experiment or historical data vintage. The [international construction notes](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/six_portfolios_momentum_developed.html) describe the relevant regional sorts. The separate [U.S. Mom construction note](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_mom_factor.html) uses a different universe and breakpoints and is not the gold reference here.

## Numeric scoring

The expected monthly aggregation is `0.5 × (Small High + Big High − Small Low − Big Low)` in percentage points, using **only the value-weighted monthly section** of each six-portfolio file. The official regional Mom files serve as a published-value check. Their source series and the six legs are rounded, and three region-month differences reached 0.02 percentage points; this audit does not claim exact identity.

| Arm | Output rows | Distinct region-months | Duplicate rows | Malformed date rows | Numeric result |
|---|---:|---:|---:|---:|---|
| Sol | 1,724 | 1,724 | 0 | 0 | Valid; MAE 0.00391 percentage points against official Mom |
| Sol + QuantGlean (later exploratory run) | 1,724 | 1,724 | 0 | 0 | Valid; identical to Sol on all 1,724 values; MAE 0.00391 percentage points |
| Luna | 6,896 | 1,724 | 5,172 | 0 | Invalid monthly series; error score withheld |
| Luna + QuantGlean | 7,093 | 1,724 | 5,172 | 197 | Invalid monthly series; error score withheld |

The two Luna runs both used data outside the single required monthly value-weighted section. Filtering the best-looking rows after seeing the official values would change the submitted outputs, so this report preserves the original failures. The first Luna attempt encountered an output-directory problem; the directory was created and that arm resumed without changing the task.

A subsequent **development rerun**, after adding a generic multi-section parsing and duplicate-key check to the four Skill languages, still produced 6,896 rows and 5,172 duplicates. It is excluded from the original three-arm comparison because the Skill was edited after inspecting the first result. This failure shows that written guidance alone did not enforce the data contract; the deterministic parser and unique-key gate in the audit/scorer remain necessary.

The user then requested a Sol versus Sol + QuantGlean check. The existing Sol output was retained; a fresh Sol run read the revised generic Skill (SHA-256 `00c7617d3a51622077ba43f26cec559e5155580a9fd6f0f23a20626f7e3421eb`) and the same four permitted portfolio files. It produced exactly the same 1,724 region-month values as Sol without the Skill. Since the Skill revision followed the earlier comparison and each condition has only one run, this is an exploratory paired-case observation, not a stable estimate of a Skill effect.

The independent [audit program](../../scripts/audit-french-momentum.py) reads the eight official ZIPs and reports overlap, source hashes, and aggregate discrepancies. The [arm scorer](../../scripts/score-french-momentum-arms.py) checks submitted model CSVs against the four official Mom files. To reproduce locally, download the eight official ZIPs into a private directory, put the five arm CSVs in separate `sol`, `sol_qg`, `luna`, `luna_qg`, and `luna_qg_v2` subdirectories, and run:

```sh
python scripts/audit-french-momentum.py PRIVATE_DATA_DIRECTORY
python scripts/score-french-momentum-arms.py PRIVATE_DATA_DIRECTORY PRIVATE_ARM_DIRECTORY
```

## Interpretation

This is a single-draw process check. The three initial model responses recognized that the current French portfolio files cannot recreate the paper's stock-level study. Sol supplied the correct monthly section in the numeric task; neither Luna run did, and QuantGlean did not repair that failure. The later Sol + QuantGlean result matched Sol exactly. No strategy extension was backtested. Alpha quality and stable model/skill effects remain unmeasured. The published portfolio files do not supply the point-in-time security returns, positions, liquidity, shorting events, and executable costs required for those candidates.
