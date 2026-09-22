# NPT Taxonomy and Classification

This document defines how drilling activity in the Volve daily drilling reports was
classified as productive vs. non-productive time (NPT), the decisions behind that
classification, and the measured reliability of the result. It is the reference for
Phase 4 of the project.

## Headline result

After rule-based classification and manual review, **non-productive time accounts for
~20.0% of total logged rig time** across the Volve drilling campaign.

| Category | Hours | % of total |
|---|---|---|
| Productive | 30,509.7 | 77.4% |
| **NPT (all sub-categories)** | **7,888.3** | **20.0%** |
| Rig Move / Mobilization (excluded from both) | 997.0 | 2.5% |
| **Total** | **39,395.0** | **100%** |

The headline figure is robust to within about **±0.2 percentage points** — see
*Residual uncertainty* below.

## The two-level taxonomy

Every activity row is assigned a Level-1 category and a Level-2 sub-category. The full
list lives in `data/reference/npt_taxonomy.csv`; the Level-1 structure is:

| Level 1 | Meaning |
|---|---|
| Productive | Time making forward progress on the well (drilling, casing, completion, P&A, logging, etc.) |
| NPT - Wellbore | Downtime caused by the hole itself: instability, losses, well control, corrective sidetrack |
| NPT - Downhole Equipment | Fishing, and BHA / bit / MWD / LWD failure |
| NPT - Surface Equipment | Rig, mud system, and other surface equipment repair/maintenance |
| NPT - External | Weather, materials/logistics, and labor action |
| NPT - Other | HSE/permits, unspecified waits, operational failures of undetermined sub-type |
| Rig Move / Mobilization | Rig skidding, anchoring, transit, rig-up/down — deliberately excluded from both Productive and NPT |

## How NPT was defined (the resolved decision)

Phase 3 surfaced two candidate signals for "NPT" that disagreed by 6x: the source's own
per-row `state == "fail"` flag (narrow, 3.2% of hours) and the `interruption` main
activity (broad, 21.2% of hours). Neither was used directly. The final definition is a
hybrid, decided as follows:

1. **A row is NPT if its final Level-1 category starts with "NPT".** Classification is
   driven by the specific activity and its narrative, not by a single source column.
2. **Rig moves and mobilization are a separate third category**, not forced into the
   productive/NPT binary. A rig skid between wells is neither drilling progress nor a
   failure. This removes ~997 hours that a naive binary would misassign.
3. **Planned vs. corrective work is distinguished by narrative, not activity code.**
   - Circulating for planned bottoms-up = Productive; circulating to clear a pack-off or
     losses = NPT - Wellbore.
   - A planned geological sidetrack = Productive; a sidetrack after losing the hole or
     getting stuck = NPT - Wellbore (Corrective).
4. **The source `fail` flag is an override, not the definition.** Any row the source
   flagged `fail` that the rules had called Productive is promoted to NPT - Other /
   Operational Failure — an explicit failure outranks a keyword guess.

## How classification was carried out

Three stages, each re-runnable:

1. **Rule-based first pass** (`src/04_classify_npt.py`) — a priority cascade: direct
   activity-code lookups for unambiguous cases, then narrative keyword matching for the
   genuine judgment calls, then the `fail` override. Every row gets a Level-1/Level-2
   label, a `confidence` flag (high / medium / low), and `classification_source = "rule"`.
2. **Manual review** (`docs/npt_manual_review.csv`) — all low-confidence NPT-flavored
   rows reviewed 100%, plus fixed-size audit samples of the medium, high, and
   low-Productive tiers. 1,517 rows reviewed in total. Reviewer corrections recorded
   per row; agreed rows left as the rule assigned.
3. **Finalization** (`src/04b_apply_review.py`) — normalizes the reviewer's free-text
   verdicts to canonical taxonomy labels, applies corrections, canonicalizes the rule's
   two provisional fallback labels (`{activity} - Other` -> `Productive / Other`;
   `{activity} (flagged fail)` -> `NPT - Other / Operational Failure`), and writes the
   final table `data/interim/drilling_activity_final.parquet`. Reviewed rows are marked
   `classification_source = "manual"`, the rest `"rule"` — a full audit trail of which
   rows a human verified.

## Stated error rate (classification reliability)

Error rate = the share of manually reviewed rows where the human overrode the rule. The
tiers are well-calibrated — confidence predicted where the rule struggled:

| Confidence tier | Rows reviewed | Overridden | Error rate |
|---|---|---|---|
| high | 150 | 0 | **0.0%** |
| medium | 150 | 66 | 44.0% |
| low | 1,217 | 1,137 | 93.4% |

Within the low tier: NPT-flavored rows 97.5% overridden, Productive-flavored 64.7%.

The **0% error on the high-confidence audit** is the key credibility result: the
high-confidence tier is the bulk of the data (~17,000 rows), and the audit found no
misclassifications in it — so the large unreviewed remainder is trustworthy. The low
tier being 93% wrong simply confirms those rows genuinely required a human, which is
why all low-confidence NPT rows were reviewed in full rather than sampled.

## Residual uncertainty

The one place unreviewed rows could still bias the headline is the ~2,462 low-confidence
Productive-flavored rows (2,180 hours) that were sampled rather than fully reviewed. In
the 150-row sample of that group, only 6 (~4%) turned out to be hidden NPT — the other
91 overrides were Productive-to-Productive reshuffling that does not change the NPT
total. Extrapolated, at most ~87 hours (~0.2 percentage points) of NPT could be hidden
in the unreviewed remainder. Hence the headline is ~20.0% ± ~0.2pp.

## NPT breakdown by category (the Pareto view)

| Level 1 | Level 2 | Hours | % of NPT |
|---|---|---|---|
| NPT - Surface Equipment | Repair/Maintenance | 2,914.9 | 36.9% |
| NPT - External | Weather | 1,933.3 | 24.5% |
| NPT - External | Labor Action | 746.0 | 9.5% |
| NPT - Downhole Equipment | Fishing | 581.3 | 7.4% |
| NPT - Downhole Equipment | Failure | 426.9 | 5.4% |
| NPT - External | Materials/Logistics | 295.2 | 3.7% |
| NPT - Other | HSE/Permits | 258.1 | 3.3% |
| NPT - Other | Operational Failure | 211.0 | 2.7% |
| NPT - Wellbore | Hole Instability | 192.2 | 2.4% |
| NPT - Wellbore | Losses | 162.5 | 2.1% |
| NPT - Wellbore | Well Control | 57.5 | 0.7% |
| NPT - Other | Unclassified | 40.0 | 0.5% |
| NPT - Other | Unspecified Wait | 36.0 | 0.5% |
| NPT - Wellbore | Sidetrack (Corrective) | 33.5 | 0.4% |

Two categories — surface-equipment repair and weather — account for over 60% of all NPT.
The `Labor Action` category is a single documented event: an oilfield-services (OFS)
strike that suspended operations across 32 well-days (746 hours).

## Known data characteristic: reports don't always sum to 24 hours

220 of 1,750 reports with an operations table (12.6%) log fewer than 24 hours of
activity (see `docs/drilling_hours_not_24.csv`, `notebooks/check_hours_gap.py`).
Confirmed causes, not parsing errors:

1. **Rig-move handovers split one calendar day across two well files.** Example:
   `15_9_F_5_2007-11-19` logs `00:00->23:45` (23.75h, ending "Held tool box talk prior
   to skidding of the cantilever from F-5 to F-15"), and `15_9_F_15_2007-11-19` logs
   `23:45->00:00` (0.25h, "Skidded cantilever from F-5 to F-15") — the same physical
   day, same rig move, across two wellbore files. Together: exactly 24 hours.
2. **Small 15-minute reporting gaps** from manual report compilation (e.g.
   `15_9_F_15_A_2009-01-09` has an unexplained gap between `04:45` and `05:00`).

Every off-24 total is an exact multiple of 0.25h, confirming operations are logged in
15-minute increments and any shortfall is a whole number of missed blocks — not a
rounding bug in `compute_hours()`.

**Implication:** NPT hours are aggregated by summing `hours` directly from the activity
table, never by assuming each report represents exactly 24 hours.
