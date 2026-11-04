# Implementation differences

- Original synthetic observations, revisions, withdrawals and predeclared queries only.
- Actual pipeline availability can lag publication; inclusive UTC boundaries; no fallback after withdrawal.
- Batch sweep uses sorted lists of known event times; worst-case insertion is linear in known event count.
- Timing includes per-call index build and full output construction; excludes input parsing and validation.
- Allocation peaks are measured in separate tracemalloc runs; not process RSS or persisted index size.
- Three fixed query workloads, alternating engine order, three repeats; no minimum speedup target.

Original in-memory data-query benchmark; no investment-return or external historical-data claim.
