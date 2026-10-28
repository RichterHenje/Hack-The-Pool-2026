# Layer joins, blind loop layers2 (seed 31415)

| class | ok | of | misses |
| --- | ---: | ---: | --- |
| A1 | 2 | 2 | – |
| A2 | 1 | 1 | – |
| C1 | 3 | 5 | C1-1, C1-5 |
| C2 | 3 | 3 | – |
| L1 | 2 | 2 | – |
| L2 | 1 | 1 | – |

| join disabled | class | ok while disabled | scorer can fail |
| --- | --- | ---: | --- |
| J1 | A1 | 0 of 2 | True |
| J2 | L1 | 0 of 2 | True |
| J3 | C1 | 0 of 5 | True |
