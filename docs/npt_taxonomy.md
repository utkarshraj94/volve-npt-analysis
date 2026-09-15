\# NPT Taxonomy



\## Two candidate NPT signals in the source data



The DDR operations table (`data/interim/drilling\_activity.parquet`) carries two

independent columns that could each define "non-productive time." They disagree

by an order of magnitude, so which one to use is a deliberate decision, not a

given:



| Definition | Column | Hours | % of total (39,395h) |

|---|---|---|---|

| Narrow — explicit failure flag | `state == "fail"` | 1,265.5 | 3.21% |

| Broad — non-drilling-progress activity | `phase == "interruption"` | 8,342.25 | 21.2% |



`state` is a per-row status the source data assigns to the operation itself

(`ok`/`fail`); `phase` is the top-level activity category (`drilling`,

`interruption`, `formation evaluation`, `plug abandon`, `workover`, `moving`,

`completion`).



\## Why the broad definition needs sub-categorization, not blanket use



`phase == "interruption"` mixes activities that are not equivalent from an NPT

perspective. Breakdown by hours:



| activity\_code | Hours | Genuinely NPT? |

|---|---|---|

| other | 2,680.9 | unclear — needs narrative review |

| waiting on weather | 1,924.5 | yes, but not equipment failure |

| repair | 1,215.0 | yes |

| sidetrack | 590.0 | questionable — this is corrective drilling, not idle time |

| fish | 568.3 | yes |

| maintain | 562.8 | yes |

| wait | 522.0 | yes |

| lost circulation | 160.8 | yes |

| rig up/down | 62.3 | questionable — routine, not a failure |

| well control | 55.8 | yes |



\*\*Decision: TBD in Phase 4.\*\* Candidate approach: define NPT as `phase ==

"interruption"` minus `sidetrack` and `rig up/down` (routine, not idle time),

plus all `state == "fail"` rows regardless of phase (an explicit failure during

an otherwise "productive" phase should still count). This needs the narrative

text for the `other` bucket (2,680.9h, the single largest interruption

sub-category) reviewed before finalizing, since it's currently unclassified.



\## Known data characteristic: reports don't always sum to 24 hours



220 of 1,750 reports with an operations table (12.6%) log fewer than 24 hours

of activity (see `docs/drilling\_hours\_not\_24.csv`, `notebooks/check\_hours\_gap.py`).

Confirmed causes, not parsing errors:



1\. \*\*Rig-move handovers split one calendar day across two well files.\*\* Example:

&#x20;  `15\_9\_F\_5\_2007-11-19` logs `00:00→23:45` (23.75h, ending "Held tool box talk

&#x20;  prior to skidding of the cantilever from F-5 to F-15"), and

&#x20;  `15\_9\_F\_15\_2007-11-19` logs `23:45→00:00` (0.25h, "Skidded cantilever from

&#x20;  F-5 to F-15") — the same physical day, same rig move, split across two

&#x20;  different wellbore report files. Together: exactly 24 hours.

2\. \*\*Small 15-minute reporting gaps\*\* from manual report compilation (e.g.

&#x20;  `15\_9\_F\_15\_A\_2009-01-09` has an unexplained gap between `04:45` and `05:00`).



Every off-24 total is an exact multiple of 0.25h, confirming operations are

logged in 15-minute increments and any shortfall is a whole number of missed

blocks — not a rounding bug in `compute\_hours()`.



\*\*Implication for Phase 4:\*\* NPT hours should be aggregated by summing

`hours` directly from `drilling\_activity.parquet`, never by assuming each

report\_id represents exactly 24 hours.

