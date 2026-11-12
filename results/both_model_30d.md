# Elve model with offer and game-update (news) features: 30-day up/flat/down

_Window 2023-10-01 to 2026-11-11, 4,812 pet variants, 1,504,574 rows. Flat = move under 5%. Class shares down/flat/up: 7.8%, 84.9%, 7.4%._

Walk-forward by month (17 test months), averages:

| model                                 |   accuracy |   macro F1 |   up precision |   up recall |   down precision |   down recall |   log loss |   up avg precision |   up precision @30% recall |   down avg precision |   down precision @30% recall |   top-20 mean 30d change |
|:--------------------------------------|-----------:|-----------:|---------------:|------------:|-----------------:|--------------:|-----------:|-------------------:|---------------------------:|---------------------:|-----------------------------:|-------------------------:|
| always flat                           |      0.774 |      0.288 |          0.000 |       0.000 |            0.000 |         0.000 |      1.560 |              0.101 |                      0.101 |                0.125 |                        0.125 |                  nan     |
| repeat last change (30d)              |      0.681 |      0.492 |          0.290 |       0.453 |            0.335 |         0.431 |      2.205 |              0.186 |                      0.278 |                0.214 |                        0.335 |                    0.062 |
| logistic regression                   |      0.774 |      0.438 |          0.481 |       0.161 |            0.489 |         0.174 |      0.665 |              0.285 |                      0.375 |                0.320 |                        0.406 |                    0.099 |
| gradient boosting                     |      0.771 |      0.442 |          0.442 |       0.156 |            0.489 |         0.193 |      0.655 |              0.279 |                      0.351 |                0.353 |                        0.420 |                    0.110 |
| logistic regression + offers          |      0.775 |      0.446 |          0.483 |       0.166 |            0.509 |         0.191 |      0.648 |              0.301 |                      0.391 |                0.340 |                        0.428 |                    0.113 |
| gradient boosting + offers            |      0.773 |      0.452 |          0.459 |       0.173 |            0.514 |         0.206 |      0.650 |              0.298 |                      0.375 |                0.376 |                        0.462 |                    0.132 |
| logistic regression + events          |      0.775 |      0.446 |          0.489 |       0.160 |            0.493 |         0.194 |      0.661 |              0.286 |                      0.377 |                0.334 |                        0.435 |                    0.101 |
| gradient boosting + events            |      0.770 |      0.444 |          0.435 |       0.160 |            0.526 |         0.199 |      0.663 |              0.276 |                      0.342 |                0.376 |                        0.438 |                    0.110 |
| logistic regression + offers + events |      0.775 |      0.453 |          0.491 |       0.166 |            0.508 |         0.209 |      0.643 |              0.303 |                      0.395 |                0.355 |                        0.462 |                    0.116 |
| gradient boosting + offers + events   |      0.770 |      0.453 |          0.445 |       0.171 |            0.527 |         0.216 |      0.656 |              0.293 |                      0.367 |                0.390 |                        0.462 |                    0.137 |


## Top-20 picks: how solid is the gain

Mean 30-day change of the picks. *new picks every 30d* counts each bet once (daily picks are held 30 days and overlap); *value >= 0.25* leaves out penny pets, where one step of the list is a huge % move.

| model                                 |   top-20 mean 30d change |   top-20 median |   top-20, new picks every 30d |   top-20, value >= 0.25 |   top-20, default only |   top-20, neon only |   top-20, mega only |   universe mean change |
|:--------------------------------------|-------------------------:|----------------:|------------------------------:|------------------------:|-----------------------:|--------------------:|--------------------:|-----------------------:|
| always flat                           |                  nan     |         nan     |                       nan     |                 nan     |                nan     |             nan     |             nan     |                  0.001 |
| repeat last change (30d)              |                    0.062 |           0.008 |                         0.040 |                   0.059 |                  0.089 |               0.055 |               0.052 |                  0.001 |
| logistic regression                   |                    0.099 |           0.062 |                         0.110 |                   0.096 |                  0.096 |               0.099 |               0.084 |                  0.001 |
| gradient boosting                     |                    0.110 |           0.049 |                         0.143 |                   0.110 |                  0.121 |               0.098 |               0.086 |                  0.001 |
| logistic regression + offers          |                    0.113 |           0.074 |                         0.116 |                   0.111 |                  0.111 |               0.108 |               0.093 |                  0.001 |
| gradient boosting + offers            |                    0.132 |           0.070 |                         0.146 |                   0.132 |                  0.141 |               0.111 |               0.098 |                  0.001 |
| logistic regression + events          |                    0.101 |           0.065 |                         0.109 |                   0.097 |                  0.098 |               0.100 |               0.087 |                  0.001 |
| gradient boosting + events            |                    0.110 |           0.050 |                         0.115 |                   0.114 |                  0.124 |               0.103 |               0.086 |                  0.001 |
| logistic regression + offers + events |                    0.116 |           0.074 |                         0.122 |                   0.115 |                  0.116 |               0.112 |               0.100 |                  0.001 |
| gradient boosting + offers + events   |                    0.137 |           0.078 |                         0.140 |                   0.141 |                  0.139 |               0.116 |               0.103 |                  0.001 |


### Range over months (90%, months resampled 2,000 times)

| model                                 | picks                       |   months |   mean |    5% |   95% |   months beating all pets |
|:--------------------------------------|:----------------------------|---------:|-------:|------:|------:|--------------------------:|
| repeat last change (30d)              | top-20 mean 30d change      |       17 |  0.062 | 0.046 | 0.077 |                     1.000 |
| repeat last change (30d)              | top-20, new picks every 30d |       17 |  0.040 | 0.026 | 0.053 |                     0.941 |
| logistic regression                   | top-20 mean 30d change      |       17 |  0.099 | 0.077 | 0.122 |                     0.824 |
| logistic regression                   | top-20, new picks every 30d |       17 |  0.110 | 0.077 | 0.147 |                     0.882 |
| gradient boosting                     | top-20 mean 30d change      |       17 |  0.110 | 0.084 | 0.139 |                     1.000 |
| gradient boosting                     | top-20, new picks every 30d |       17 |  0.143 | 0.107 | 0.181 |                     0.941 |
| logistic regression + offers          | top-20 mean 30d change      |       17 |  0.113 | 0.090 | 0.134 |                     0.941 |
| logistic regression + offers          | top-20, new picks every 30d |       17 |  0.116 | 0.085 | 0.152 |                     0.882 |
| gradient boosting + offers            | top-20 mean 30d change      |       17 |  0.132 | 0.104 | 0.164 |                     1.000 |
| gradient boosting + offers            | top-20, new picks every 30d |       17 |  0.146 | 0.107 | 0.185 |                     1.000 |
| logistic regression + events          | top-20 mean 30d change      |       17 |  0.101 | 0.078 | 0.123 |                     0.941 |
| logistic regression + events          | top-20, new picks every 30d |       17 |  0.109 | 0.071 | 0.148 |                     0.882 |
| gradient boosting + events            | top-20 mean 30d change      |       17 |  0.110 | 0.081 | 0.139 |                     1.000 |
| gradient boosting + events            | top-20, new picks every 30d |       17 |  0.115 | 0.089 | 0.144 |                     1.000 |
| logistic regression + offers + events | top-20 mean 30d change      |       17 |  0.116 | 0.094 | 0.137 |                     1.000 |
| logistic regression + offers + events | top-20, new picks every 30d |       17 |  0.122 | 0.089 | 0.157 |                     0.882 |
| gradient boosting + offers + events   | top-20 mean 30d change      |       17 |  0.137 | 0.105 | 0.168 |                     1.000 |
| gradient boosting + offers + events   | top-20, new picks every 30d |       17 |  0.140 | 0.104 | 0.176 |                     1.000 |


## Per month: macro F1

| month   |   always flat |   gradient boosting |   gradient boosting + events |   gradient boosting + offers |   gradient boosting + offers + events |   logistic regression |   logistic regression + events |   logistic regression + offers |   logistic regression + offers + events |   repeat last change (30d) |
|:--------|--------------:|--------------------:|-----------------------------:|-----------------------------:|--------------------------------------:|----------------------:|-------------------------------:|-------------------------------:|----------------------------------------:|---------------------------:|
| 2025-06 |         0.303 |               0.450 |                        0.464 |                        0.459 |                                 0.478 |                 0.351 |                          0.388 |                          0.368 |                                   0.397 |                      0.494 |
| 2025-07 |         0.298 |               0.485 |                        0.474 |                        0.463 |                                 0.468 |                 0.370 |                          0.398 |                          0.377 |                                   0.403 |                      0.514 |
| 2025-08 |         0.310 |               0.448 |                        0.451 |                        0.448 |                                 0.451 |                 0.418 |                          0.433 |                          0.401 |                                   0.414 |                      0.498 |
| 2025-09 |         0.312 |               0.428 |                        0.434 |                        0.422 |                                 0.426 |                 0.465 |                          0.467 |                          0.451 |                                   0.454 |                      0.538 |
| 2025-10 |         0.298 |               0.421 |                        0.426 |                        0.416 |                                 0.427 |                 0.434 |                          0.443 |                          0.433 |                                   0.440 |                      0.521 |
| 2025-11 |         0.300 |               0.437 |                        0.431 |                        0.445 |                                 0.443 |                 0.453 |                          0.446 |                          0.445 |                                   0.443 |                      0.498 |
| 2025-12 |         0.285 |               0.410 |                        0.384 |                        0.401 |                                 0.395 |                 0.444 |                          0.440 |                          0.444 |                                   0.443 |                      0.513 |
| 2026-01 |         0.305 |               0.433 |                        0.437 |                        0.453 |                                 0.454 |                 0.502 |                          0.495 |                          0.519 |                                   0.517 |                      0.492 |
| 2026-02 |         0.295 |               0.441 |                        0.429 |                        0.473 |                                 0.457 |                 0.429 |                          0.419 |                          0.448 |                                   0.436 |                      0.499 |
| 2026-03 |         0.264 |               0.367 |                        0.380 |                        0.378 |                                 0.391 |                 0.380 |                          0.391 |                          0.396 |                                   0.407 |                      0.505 |
| 2026-04 |         0.159 |               0.230 |                        0.224 |                        0.244 |                                 0.238 |                 0.248 |                          0.241 |                          0.265 |                                   0.253 |                      0.411 |
| 2026-05 |         0.276 |               0.491 |                        0.461 |                        0.491 |                                 0.480 |                 0.455 |                          0.455 |                          0.480 |                                   0.478 |                      0.339 |
| 2026-06 |         0.289 |               0.471 |                        0.467 |                        0.496 |                                 0.486 |                 0.544 |                          0.541 |                          0.539 |                                   0.540 |                      0.521 |
| 2026-07 |         0.296 |               0.475 |                        0.504 |                        0.503 |                                 0.501 |                 0.513 |                          0.532 |                          0.526 |                                   0.534 |                      0.537 |
| 2026-08 |         0.297 |               0.511 |                        0.528 |                        0.530 |                                 0.529 |                 0.475 |                          0.491 |                          0.493 |                                   0.511 |                      0.494 |
| 2026-09 |         0.307 |               0.495 |                        0.510 |                        0.513 |                                 0.516 |                 0.471 |                          0.495 |                          0.491 |                                   0.515 |                      0.486 |
| 2026-10 |         0.308 |               0.517 |                        0.539 |                        0.553 |                                 0.556 |                 0.499 |                          0.514 |                          0.508 |                                   0.523 |                      0.495 |


## Logistic regression: features pushing toward up (+) or down (-), last fold

|                     |   up minus down coef |
|:--------------------|---------------------:|
| elve_demand_chg     |               -0.339 |
| pet_dn_14           |               -0.221 |
| rarity_legendary    |               -0.167 |
| n_dn_30             |               -0.161 |
| ev_mention_30       |               -0.135 |
| rarity_ultra rare   |               -0.133 |
| ev_mention_7        |               -0.092 |
| pet_dn_3            |               -0.081 |
| ev_age              |                0.195 |
| elve_offer_7        |                0.204 |
| rarity_uncommon     |                0.206 |
| mkt_up_share_7      |                0.224 |
| days_since_change   |                0.310 |
| last_change         |                0.324 |
| elve_kind_demand_14 |                0.332 |
| elve_demand_7       |                0.702 |