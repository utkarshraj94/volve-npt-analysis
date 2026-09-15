# Drilling Reports Data Quality Report

```
Report files found: 1759
Reports with no Operations table: 9
  15_9_19_A_1980-01-01, 15_9_19_A_1997-07-25, 15_9_F_11_T2_2013-04-01, 15_9_F_14_2007-12-04, 15_9_F_15_2018-01-25, 15_9_F_1_C_2014-03-31, 15_9_F_4_2008-03-31, 15_9_F_4_2016-10-01, 15_9_F_5_2007-11-15
Activity rows parsed: 23447
Distinct wells (filename form): 26

Main activity value counts:
main_activity
drilling                9137
plug abandon            4595
interruption            3577
completion              2944
workover                2221
formation evaluation     732
moving                   241

Phase (hole section) value counts:
phase
post-completion    5640
plug abandon       4595
8.5 in hole        3645
completion         2944
12.25 in hole      2347
17.5 in hole       1879
26 in hole         1239
36 in hole          729
6 in hole           329
NaN                  92
9.875 in hole         8

State value counts:
state
ok      22967
fail      480

NPT (state == fail) hours: 1265.5 of 39395.0 total (3.21%)

Reports where activity hours don't sum to 24h: 220 of 1750

Actual-drilling rows where depth decreased vs. the previous drilling row for that well: 265 of 1822
```
