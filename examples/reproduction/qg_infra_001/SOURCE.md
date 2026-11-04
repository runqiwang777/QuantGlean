# QG-INFRA-001 original research design

## I1 — three clocks

The event time describes a historical observation; publication time is when its source released it; available_at is when this pipeline could actually use it. Query by actual availability, never by a final revised table.

## I2 — selection and withdrawal

Among event times no later than event_cutoff, select the newest one with any version known at decision_at. Within that event select its latest available revision. Boundaries are inclusive. A known withdrawal returns missing with status withdrawn and does not fall back to an older event. No forecast/future-event semantics are implied.

## I3 — correctness before performance

Compare the batch availability sweep with a simple independent filter-and-sort baseline on every query. Time repeated predeclared workloads including index construction, excluding validation and file I/O. Measure Python allocation peaks separately from timing; these are not total process RSS. No speed threshold or investment-return target is an acceptance condition.
