# Elve model with AMVGG value-move features: 30-day up/flat/down

_Window 2023-10-01 to 2026-11-11, 4,812 pet variants, 319,914 rows. Flat = move under 5%. Class shares down/flat/up: 7.8%, 84.9%, 7.4%._

Walk-forward by month (1 test months), averages:

| model                       |   accuracy |   macro F1 |   up precision |   up recall |   down precision |   down recall |   log loss |   up avg precision |   up precision @30% recall |   down avg precision |   down precision @30% recall |   top-20 mean 30d change |
|:----------------------------|-----------:|-----------:|---------------:|------------:|-----------------:|--------------:|-----------:|-------------------:|---------------------------:|---------------------:|-----------------------------:|-------------------------:|
| always flat                 |      0.857 |      0.308 |          0.000 |       0.000 |            0.000 |         0.000 |      0.987 |              0.044 |                      0.044 |                0.099 |                        0.099 |                  nan     |
| repeat last change (30d)    |      0.737 |      0.495 |          0.212 |       0.618 |            0.269 |         0.404 |      1.819 |              0.148 |                      0.212 |                0.167 |                        0.269 |                    0.015 |
| AMVGG moved first (30d gap) |      0.784 |      0.382 |          0.039 |       0.074 |            0.324 |         0.155 |      1.496 |              0.043 |                      0.044 |                0.134 |                        0.099 |                   -0.053 |
| logistic regression         |      0.852 |      0.440 |          0.274 |       0.336 |            0.574 |         0.049 |      0.545 |              0.220 |                      0.284 |                0.242 |                        0.249 |                    0.001 |
| gradient boosting           |      0.838 |      0.464 |          0.209 |       0.446 |            0.511 |         0.110 |      0.550 |              0.212 |                      0.248 |                0.315 |                        0.424 |                    0.043 |
| logistic regression + amvgg |      0.849 |      0.454 |          0.285 |       0.457 |            0.677 |         0.046 |      0.560 |              0.252 |                      0.373 |                0.233 |                        0.249 |                    0.021 |
| gradient boosting + amvgg   |      0.820 |      0.472 |          0.178 |       0.477 |            0.498 |         0.157 |      0.565 |              0.196 |                      0.230 |                0.361 |                        0.473 |                   -0.018 |


## Top-20 picks: how solid is the gain

Mean 30-day change of the picks. *new picks every 30d* counts each bet once (daily picks are held 30 days and overlap); *value >= 0.25* leaves out penny pets, where one step of the list is a huge % move.

| model                       |   top-20 mean 30d change |   top-20 median |   top-20, new picks every 30d |   top-20, value >= 0.25 |   top-20, default only |   top-20, neon only |   top-20, mega only |   universe mean change |
|:----------------------------|-------------------------:|----------------:|------------------------------:|------------------------:|-----------------------:|--------------------:|--------------------:|-----------------------:|
| always flat                 |                  nan     |         nan     |                       nan     |                 nan     |                nan     |             nan     |             nan     |                 -0.019 |
| repeat last change (30d)    |                    0.015 |           0.000 |                        -0.018 |                   0.014 |                  0.039 |               0.010 |               0.011 |                 -0.019 |
| AMVGG moved first (30d gap) |                   -0.053 |           0.000 |                        -0.033 |                  -0.042 |                 -0.061 |              -0.047 |              -0.026 |                 -0.019 |
| logistic regression         |                    0.001 |           0.020 |                        -0.010 |                   0.001 |                  0.011 |              -0.022 |               0.007 |                 -0.019 |
| gradient boosting           |                    0.043 |           0.000 |                         0.033 |                   0.043 |                  0.014 |              -0.009 |               0.002 |                 -0.019 |
| logistic regression + amvgg |                    0.021 |           0.017 |                         0.075 |                   0.021 |                  0.033 |               0.027 |               0.044 |                 -0.019 |
| gradient boosting + amvgg   |                   -0.018 |           0.000 |                         0.015 |                  -0.018 |                  0.023 |               0.040 |               0.028 |                 -0.019 |


## Per month: macro F1

| month   |   AMVGG moved first (30d gap) |   always flat |   gradient boosting |   gradient boosting + amvgg |   logistic regression |   logistic regression + amvgg |   repeat last change (30d) |
|:--------|------------------------------:|--------------:|--------------------:|----------------------------:|----------------------:|------------------------------:|---------------------------:|
| 2026-10 |                         0.382 |         0.308 |               0.464 |                       0.472 |                 0.440 |                         0.454 |                      0.495 |


## Logistic regression: features pushing toward up (+) or down (-), last fold

|                      |   up minus down coef |
|:---------------------|---------------------:|
| gg_days_since_change |               -0.726 |
| gg_n_up_30           |               -0.492 |
| rarity_up_share_30   |               -0.435 |
| rarity_common        |               -0.432 |
| pet_dn_14            |               -0.406 |
| kind_mega            |               -0.216 |
| mkt_up_share_7       |               -0.197 |
| pet_up_14            |               -0.193 |
| no_potion            |                0.172 |
| rarity_legendary     |                0.205 |
| ret_90               |                0.260 |
| gg_last_change       |                0.287 |
| n_up_90              |                0.396 |
| last_change          |                0.558 |
| log_value            |                0.656 |
| days_since_change    |                2.549 |