# Production Data Quality Report

```
Row count: 15634
Date range: 2007-09-01 00:00:00 to 2016-12-01 00:00:00
Distinct wellbores: 7

Nulls per column:
  ON_STREAM_HRS: 285
  AVG_DOWNHOLE_PRESSURE: 6654
  AVG_DOWNHOLE_TEMPERATURE: 6654
  AVG_DP_TUBING: 6654
  AVG_ANNULUS_PRESS: 7744
  AVG_CHOKE_SIZE_P: 6715
  AVG_CHOKE_UOM: 6473
  AVG_WHP_P: 6479
  AVG_WHT_P: 6488
  DP_CHOKE_SIZE: 294
  BORE_OIL_VOL: 6473
  BORE_GAS_VOL: 6473
  BORE_WAT_VOL: 6473
  BORE_WI_VOL: 9928

Duplicate (date, wellbore) rows: 0

WELL_TYPE / FLOW_KIND mismatches: 18
BORE_OIL_VOL: 0 negative rows, 1153 zero rows
BORE_GAS_VOL: 0 negative rows, 1150 zero rows
BORE_WAT_VOL: 4 negative rows, 1526 zero rows

Date coverage per wellbore:
   wellbore first_date  last_date  days_present  expected_days  gap_days
 15/9-F-1 C 2014-04-07 2016-04-21           746            746         0
  15/9-F-11 2013-07-08 2016-09-17          1165           1168         3
  15/9-F-12 2008-02-12 2016-09-17          3056           3141        85
  15/9-F-14 2008-02-12 2016-09-17          3056           3141        85
15/9-F-15 D 2014-01-12 2016-09-17           978            980         2
   15/9-F-4 2007-09-01 2016-12-01          3327           3380        53
   15/9-F-5 2007-09-01 2016-09-18          3306           3306         0
```
