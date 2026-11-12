# Elve model with AMVGG value-move features: 7-day up/flat/down

_Window 2023-10-01 to 2026-11-11, 4,812 pet variants, 319,914 rows. Flat = move under 2%. Class shares down/flat/up: 3.4%, 93.4%, 3.3%._

Walk-forward by month (3 test months), averages:

| model                       |   accuracy |   macro F1 |   up precision |   up recall |   down precision |   down recall |   log loss |   up avg precision |   up precision @30% recall |   down avg precision |   down precision @30% recall |   top-20 mean 7d change |
|:----------------------------|-----------:|-----------:|---------------:|------------:|-----------------:|--------------:|-----------:|-------------------:|---------------------------:|---------------------:|-----------------------------:|------------------------:|
| always flat                 |      0.908 |      0.317 |          0.000 |       0.000 |            0.000 |         0.000 |      0.636 |              0.032 |                      0.032 |                0.060 |                        0.060 |                 nan     |
| repeat last change (30d)    |      0.771 |      0.491 |          0.157 |       0.591 |            0.260 |         0.591 |      1.584 |              0.105 |                      0.157 |                0.182 |                        0.260 |                   0.014 |
| AMVGG moved first (30d gap) |      0.769 |      0.418 |          0.067 |       0.264 |            0.224 |         0.350 |      1.598 |              0.042 |                      0.048 |                0.125 |                        0.209 |                  -0.007 |
| logistic regression         |      0.910 |      0.478 |          0.319 |       0.167 |            0.597 |         0.187 |      0.305 |              0.222 |                      0.304 |                0.354 |                        0.501 |                   0.004 |
| gradient boosting           |      0.905 |      0.496 |          0.294 |       0.264 |            0.523 |         0.192 |      0.305 |              0.260 |                      0.348 |                0.360 |                        0.433 |                   0.043 |
| logistic regression + amvgg |      0.911 |      0.493 |          0.341 |       0.211 |            0.588 |         0.192 |      0.302 |              0.257 |                      0.365 |                0.355 |                        0.503 |                   0.025 |
| gradient boosting + amvgg   |      0.917 |      0.567 |          0.415 |       0.298 |            0.614 |         0.310 |      0.284 |              0.316 |                      0.481 |                0.459 |                        0.601 |                   0.088 |


## Top-20 picks: how solid is the gain

Mean 7-day change of the picks. *new picks every 7d* counts each bet once (daily picks are held 7 days and overlap); *value >= 0.25* leaves out penny pets, where one step of the list is a huge % move.

| model                       |   top-20 mean 7d change |   top-20 median |   top-20, new picks every 7d |   top-20, value >= 0.25 |   top-20, default only |   top-20, neon only |   top-20, mega only |   universe mean change |
|:----------------------------|------------------------:|----------------:|-----------------------------:|------------------------:|-----------------------:|--------------------:|--------------------:|-----------------------:|
| always flat                 |                 nan     |         nan     |                      nan     |                 nan     |                nan     |             nan     |             nan     |                 -0.004 |
| repeat last change (30d)    |                   0.014 |           0.000 |                        0.010 |                   0.014 |                  0.010 |               0.010 |               0.010 |                 -0.004 |
| AMVGG moved first (30d gap) |                  -0.007 |           0.000 |                       -0.010 |                  -0.004 |                 -0.012 |              -0.004 |              -0.003 |                 -0.004 |
| logistic regression         |                   0.004 |          -0.014 |                        0.017 |                   0.004 |                  0.016 |               0.014 |               0.004 |                 -0.004 |
| gradient boosting           |                   0.043 |           0.023 |                        0.046 |                   0.042 |                  0.030 |               0.023 |               0.019 |                 -0.004 |
| logistic regression + amvgg |                   0.025 |          -0.009 |                        0.041 |                   0.025 |                  0.033 |               0.025 |               0.017 |                 -0.004 |
| gradient boosting + amvgg   |                   0.088 |           0.055 |                        0.101 |                   0.088 |                  0.048 |               0.043 |               0.039 |                 -0.004 |


### Range over months (90%, months resampled 2,000 times)

| model                       | picks                      |   months |   mean |     5% |    95% |   months beating all pets |
|:----------------------------|:---------------------------|---------:|-------:|-------:|-------:|--------------------------:|
| repeat last change (30d)    | top-20 mean 7d change      |        3 |  0.014 |  0.008 |  0.020 |                     1.000 |
| repeat last change (30d)    | top-20, new picks every 7d |        3 |  0.010 | -0.003 |  0.023 |                     0.667 |
| AMVGG moved first (30d gap) | top-20 mean 7d change      |        3 | -0.007 | -0.014 | -0.000 |                     0.333 |
| AMVGG moved first (30d gap) | top-20, new picks every 7d |        3 | -0.010 | -0.016 | -0.003 |                     0.333 |
| logistic regression         | top-20 mean 7d change      |        3 |  0.004 | -0.049 |  0.058 |                     0.667 |
| logistic regression         | top-20, new picks every 7d |        3 |  0.017 | -0.025 |  0.060 |                     0.667 |
| gradient boosting           | top-20 mean 7d change      |        3 |  0.043 | -0.002 |  0.087 |                     0.667 |
| gradient boosting           | top-20, new picks every 7d |        3 |  0.046 |  0.014 |  0.078 |                     0.667 |
| logistic regression + amvgg | top-20 mean 7d change      |        3 |  0.025 | -0.044 |  0.095 |                     0.667 |
| logistic regression + amvgg | top-20, new picks every 7d |        3 |  0.041 | -0.017 |  0.100 |                     0.667 |
| gradient boosting + amvgg   | top-20 mean 7d change      |        3 |  0.088 |  0.032 |  0.144 |                     0.667 |
| gradient boosting + amvgg   | top-20, new picks every 7d |        3 |  0.101 |  0.034 |  0.168 |                     0.667 |


## Per month: macro F1

| month   |   AMVGG moved first (30d gap) |   always flat |   gradient boosting |   gradient boosting + amvgg |   logistic regression |   logistic regression + amvgg |   repeat last change (30d) |
|:--------|------------------------------:|--------------:|--------------------:|----------------------------:|----------------------:|------------------------------:|---------------------------:|
| 2026-09 |                         0.373 |         0.318 |               0.489 |                       0.536 |                 0.475 |                         0.489 |                      0.441 |
| 2026-10 |                         0.447 |         0.318 |               0.495 |                       0.615 |                 0.503 |                         0.535 |                      0.509 |
| 2026-11 |                         0.433 |         0.316 |               0.503 |                       0.550 |                 0.456 |                         0.455 |                      0.524 |


## Logistic regression: features pushing toward up (+) or down (-), last fold

|                      |   up minus down coef |
|:---------------------|---------------------:|
| gg_days_since_change |               -0.286 |
| pet_dn_14            |               -0.261 |
| pet_dn_3             |               -0.175 |
| pet_up_14            |               -0.167 |
| gg_n_dn_30           |               -0.161 |
| n_up_90              |               -0.145 |
| rarity_common        |               -0.138 |
| rarity_up_share_7    |               -0.135 |
| mkt_up_share_7       |                0.156 |
| pet_up_3             |                0.173 |
| mkt_moves_7          |                0.190 |
| gg_last_change       |                0.253 |
| n_up_30              |                0.274 |
| log_value            |                0.383 |
| last_change          |                0.502 |
| days_since_change    |                1.066 |