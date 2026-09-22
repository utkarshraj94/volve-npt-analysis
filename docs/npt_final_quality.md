# NPT Final Classification Report (after manual review)

```
Total rows: 23447
Rows manually reviewed: 1517

Classification source:
classification_source
rule      21930
manual     1517

=== Manual-review error rate by confidence tier ===
(error rate = % of reviewed rows where the human overrode the rule)
  high    reviewed=  150  overridden=    0  error rate=  0.0%
  medium  reviewed=  150  overridden=   66  error rate= 44.0%
  low     reviewed= 1217  overridden= 1137  error rate= 93.4%
    low breakdown -- NPT-flavored: reviewed=1067 error=97.5% | Productive-flavored: reviewed=150 error=64.7%

NPT hours (rule labels only):    8549.8 (21.70%)
NPT hours (after review):        7888.3 (20.02%)

=== Final Level 1 (hours) ===
final_level1
Productive                  30509.733333
NPT - External               2974.400000
NPT - Surface Equipment      2914.850000
NPT - Downhole Equipment     1008.250000
Rig Move / Mobilization       997.000000
NPT - Other                   545.083333
NPT - Wellbore                445.666667

=== Final Level 1 x Level 2 (hours) ===
final_level1              final_level2          
Productive                Drilling                  5632.733333
                          Casing/Cementing          5050.000000
                          Completion                4258.416667
                          Tripping                  3338.333333
                          Workover                  3334.583333
NPT - Surface Equipment   Repair/Maintenance        2914.850000
Productive                BOP/Wellhead              2397.250000
                          Other                     2224.000000
NPT - External            Weather                   1933.250000
Productive                Plug & Abandon            1650.500000
Rig Move / Mobilization   Mobilization               997.000000
Productive                Circulating                813.000000
NPT - External            Labor Action               746.000000
NPT - Downhole Equipment  Fishing                    581.333333
Productive                Sidetrack (Planned)        557.000000
                          Logging                    556.750000
                          Formation Evaluation       482.666667
NPT - Downhole Equipment  Failure                    426.916667
NPT - External            Materials/Logistics        295.150000
NPT - Other               HSE/Permits                258.083333
                          Operational Failure        211.000000
NPT - Wellbore            Hole Instability           192.166667
                          Losses                     162.500000
Productive                Surveying                  138.250000
                          Perforating                 62.500000
NPT - Wellbore            Well Control                57.500000
NPT - Other               Unclassified                40.000000
                          Unspecified Wait            36.000000
NPT - Wellbore            Sidetrack (Corrective)      33.500000
Productive                Monitoring                  13.750000
```
