# Elve model with offer and game-update (news) features: 7-day up/flat/down

_Window 2023-10-01 to 2026-11-12, 4,812 pet variants, 1,506,980 rows. Flat = move under 2%. Class shares down/flat/up: 3.4%, 93.4%, 3.3%._

Walk-forward by month (19 test months), averages:

| model                                 |   accuracy |   macro F1 |   up precision |   up recall |   down precision |   down recall |   log loss |   up avg precision |   up precision @30% recall |   down avg precision |   down precision @30% recall |   top-20 mean 7d change |
|:--------------------------------------|-----------:|-----------:|---------------:|------------:|-----------------:|--------------:|-----------:|-------------------:|---------------------------:|---------------------:|-----------------------------:|------------------------:|
| always flat                           |      0.900 |      0.316 |          0.000 |       0.000 |            0.000 |         0.000 |      0.694 |              0.046 |                      0.046 |                0.054 |                        0.054 |                 nan     |
| repeat last change (30d)              |      0.724 |      0.456 |          0.182 |       0.570 |            0.190 |         0.532 |      1.910 |              0.125 |                      0.182 |                0.128 |                        0.190 |                   0.019 |
| logistic regression                   |      0.899 |      0.443 |          0.417 |       0.141 |            0.449 |         0.128 |      0.351 |              0.244 |                      0.338 |                0.235 |                        0.302 |                   0.033 |
| gradient boosting                     |      0.903 |      0.434 |          0.494 |       0.129 |            0.552 |         0.108 |      0.328 |              0.272 |                      0.375 |                0.278 |                        0.339 |                   0.051 |
| logistic regression + offers          |      0.899 |      0.443 |          0.431 |       0.142 |            0.461 |         0.121 |      0.343 |              0.255 |                      0.348 |                0.246 |                        0.312 |                   0.037 |
| gradient boosting + offers            |      0.903 |      0.438 |          0.499 |       0.133 |            0.567 |         0.111 |      0.324 |              0.286 |                      0.388 |                0.295 |                        0.359 |                   0.056 |
| logistic regression + events          |      0.899 |      0.447 |          0.422 |       0.136 |            0.446 |         0.141 |      0.349 |              0.244 |                      0.338 |                0.253 |                        0.331 |                   0.033 |
| gradient boosting + events            |      0.903 |      0.442 |          0.478 |       0.119 |            0.559 |         0.136 |      0.330 |              0.264 |                      0.360 |                0.301 |                        0.373 |                   0.053 |
| logistic regression + offers + events |      0.900 |      0.449 |          0.438 |       0.137 |            0.486 |         0.138 |      0.340 |              0.255 |                      0.347 |                0.265 |                        0.342 |                   0.038 |
| gradient boosting + offers + events   |      0.904 |      0.444 |          0.507 |       0.129 |            0.581 |         0.125 |      0.326 |              0.283 |                      0.380 |                0.312 |                        0.386 |                   0.060 |


## Top-20 picks: how solid is the gain

Mean 7-day change of the picks. *new picks every 7d* counts each bet once (daily picks are held 7 days and overlap); *value >= 0.25* leaves out penny pets, where one step of the list is a huge % move.

| model                                 |   top-20 mean 7d change |   top-20 median |   top-20, new picks every 7d |   top-20, value >= 0.25 |   top-20, default only |   top-20, neon only |   top-20, mega only |   universe mean change |
|:--------------------------------------|------------------------:|----------------:|-----------------------------:|------------------------:|-----------------------:|--------------------:|--------------------:|-----------------------:|
| always flat                           |                 nan     |         nan     |                      nan     |                 nan     |                nan     |             nan     |             nan     |                 -0.000 |
| repeat last change (30d)              |                   0.019 |           0.000 |                        0.014 |                   0.018 |                  0.024 |               0.017 |               0.016 |                 -0.000 |
| logistic regression                   |                   0.033 |           0.017 |                        0.030 |                   0.032 |                  0.034 |               0.029 |               0.026 |                 -0.000 |
| gradient boosting                     |                   0.051 |           0.026 |                        0.052 |                   0.051 |                  0.047 |               0.043 |               0.038 |                 -0.000 |
| logistic regression + offers          |                   0.037 |           0.019 |                        0.034 |                   0.037 |                  0.037 |               0.033 |               0.030 |                 -0.000 |
| gradient boosting + offers            |                   0.056 |           0.028 |                        0.056 |                   0.056 |                  0.052 |               0.047 |               0.043 |                 -0.000 |
| logistic regression + events          |                   0.033 |           0.017 |                        0.032 |                   0.033 |                  0.035 |               0.030 |               0.026 |                 -0.000 |
| gradient boosting + events            |                   0.053 |           0.027 |                        0.054 |                   0.053 |                  0.044 |               0.042 |               0.038 |                 -0.000 |
| logistic regression + offers + events |                   0.038 |           0.020 |                        0.037 |                   0.038 |                  0.038 |               0.033 |               0.030 |                 -0.000 |
| gradient boosting + offers + events   |                   0.060 |           0.031 |                        0.061 |                   0.060 |                  0.049 |               0.044 |               0.041 |                 -0.000 |


### Range over months (90%, months resampled 2,000 times)

| model                                 | picks                      |   months |   mean |    5% |   95% |   months beating all pets |
|:--------------------------------------|:---------------------------|---------:|-------:|------:|------:|--------------------------:|
| repeat last change (30d)              | top-20 mean 7d change      |       19 |  0.019 | 0.014 | 0.023 |                     1.000 |
| repeat last change (30d)              | top-20, new picks every 7d |       19 |  0.014 | 0.009 | 0.020 |                     0.895 |
| logistic regression                   | top-20 mean 7d change      |       19 |  0.033 | 0.020 | 0.043 |                     0.947 |
| logistic regression                   | top-20, new picks every 7d |       19 |  0.030 | 0.019 | 0.039 |                     0.947 |
| gradient boosting                     | top-20 mean 7d change      |       19 |  0.051 | 0.038 | 0.065 |                     0.947 |
| gradient boosting                     | top-20, new picks every 7d |       19 |  0.052 | 0.038 | 0.067 |                     0.947 |
| logistic regression + offers          | top-20 mean 7d change      |       19 |  0.037 | 0.025 | 0.047 |                     0.947 |
| logistic regression + offers          | top-20, new picks every 7d |       19 |  0.034 | 0.025 | 0.042 |                     0.947 |
| gradient boosting + offers            | top-20 mean 7d change      |       19 |  0.056 | 0.044 | 0.071 |                     0.947 |
| gradient boosting + offers            | top-20, new picks every 7d |       19 |  0.056 | 0.041 | 0.072 |                     0.947 |
| logistic regression + events          | top-20 mean 7d change      |       19 |  0.033 | 0.020 | 0.044 |                     0.947 |
| logistic regression + events          | top-20, new picks every 7d |       19 |  0.032 | 0.021 | 0.040 |                     0.947 |
| gradient boosting + events            | top-20 mean 7d change      |       19 |  0.053 | 0.039 | 0.066 |                     0.947 |
| gradient boosting + events            | top-20, new picks every 7d |       19 |  0.054 | 0.040 | 0.069 |                     0.947 |
| logistic regression + offers + events | top-20 mean 7d change      |       19 |  0.038 | 0.026 | 0.048 |                     0.947 |
| logistic regression + offers + events | top-20, new picks every 7d |       19 |  0.037 | 0.027 | 0.046 |                     0.947 |
| gradient boosting + offers + events   | top-20 mean 7d change      |       19 |  0.060 | 0.046 | 0.075 |                     1.000 |
| gradient boosting + offers + events   | top-20, new picks every 7d |       19 |  0.061 | 0.045 | 0.079 |                     0.947 |


## Per month: macro F1

| month   |   always flat |   gradient boosting |   gradient boosting + events |   gradient boosting + offers |   gradient boosting + offers + events |   logistic regression |   logistic regression + events |   logistic regression + offers |   logistic regression + offers + events |   repeat last change (30d) |
|:--------|--------------:|--------------------:|-----------------------------:|-----------------------------:|--------------------------------------:|----------------------:|-------------------------------:|-------------------------------:|----------------------------------------:|---------------------------:|
| 2025-05 |         0.323 |               0.381 |                        0.409 |                        0.399 |                                 0.398 |                 0.353 |                          0.366 |                          0.368 |                                   0.390 |                      0.463 |
| 2025-06 |         0.324 |               0.377 |                        0.409 |                        0.386 |                                 0.425 |                 0.337 |                          0.348 |                          0.340 |                                   0.378 |                      0.410 |
| 2025-07 |         0.320 |               0.364 |                        0.384 |                        0.351 |                                 0.372 |                 0.368 |                          0.399 |                          0.371 |                                   0.412 |                      0.445 |
| 2025-08 |         0.325 |               0.391 |                        0.384 |                        0.383 |                                 0.381 |                 0.403 |                          0.412 |                          0.394 |                                   0.404 |                      0.419 |
| 2025-09 |         0.324 |               0.383 |                        0.374 |                        0.367 |                                 0.373 |                 0.465 |                          0.439 |                          0.451 |                                   0.433 |                      0.491 |
| 2025-10 |         0.320 |               0.405 |                        0.430 |                        0.392 |                                 0.416 |                 0.465 |                          0.464 |                          0.456 |                                   0.450 |                      0.529 |
| 2025-11 |         0.320 |               0.365 |                        0.363 |                        0.372 |                                 0.370 |                 0.447 |                          0.437 |                          0.447 |                                   0.438 |                      0.465 |
| 2025-12 |         0.316 |               0.348 |                        0.385 |                        0.369 |                                 0.385 |                 0.457 |                          0.463 |                          0.458 |                                   0.460 |                      0.465 |
| 2026-01 |         0.317 |               0.475 |                        0.478 |                        0.496 |                                 0.492 |                 0.466 |                          0.460 |                          0.468 |                                   0.464 |                      0.441 |
| 2026-02 |         0.324 |               0.449 |                        0.458 |                        0.477 |                                 0.478 |                 0.461 |                          0.454 |                          0.459 |                                   0.455 |                      0.450 |
| 2026-03 |         0.308 |               0.389 |                        0.405 |                        0.410 |                                 0.421 |                 0.400 |                          0.409 |                          0.403 |                                   0.414 |                      0.500 |
| 2026-04 |         0.288 |               0.389 |                        0.385 |                        0.404 |                                 0.399 |                 0.399 |                          0.397 |                          0.399 |                                   0.393 |                      0.436 |
| 2026-05 |         0.299 |               0.405 |                        0.399 |                        0.412 |                                 0.407 |                 0.433 |                          0.432 |                          0.438 |                                   0.435 |                      0.268 |
| 2026-06 |         0.310 |               0.476 |                        0.467 |                        0.485 |                                 0.478 |                 0.472 |                          0.478 |                          0.467 |                                   0.473 |                      0.453 |
| 2026-07 |         0.313 |               0.489 |                        0.517 |                        0.498 |                                 0.521 |                 0.501 |                          0.505 |                          0.496 |                                   0.498 |                      0.479 |
| 2026-08 |         0.313 |               0.499 |                        0.508 |                        0.506 |                                 0.531 |                 0.476 |                          0.479 |                          0.478 |                                   0.485 |                      0.466 |
| 2026-09 |         0.318 |               0.521 |                        0.530 |                        0.528 |                                 0.532 |                 0.478 |                          0.491 |                          0.484 |                                   0.495 |                      0.441 |
| 2026-10 |         0.318 |               0.613 |                        0.616 |                        0.547 |                                 0.543 |                 0.576 |                          0.581 |                          0.573 |                                   0.573 |                      0.509 |
| 2026-11 |         0.315 |               0.520 |                        0.501 |                        0.535 |                                 0.517 |                 0.464 |                          0.469 |                          0.473 |                                   0.477 |                      0.524 |


## Logistic regression: features pushing toward up (+) or down (-), last fold

|                     |   up minus down coef |
|:--------------------|---------------------:|
| elve_demand_chg     |               -0.314 |
| pet_dn_14           |               -0.229 |
| rarity_up_share_7   |               -0.205 |
| rarity_legendary    |               -0.188 |
| n_dn_30             |               -0.133 |
| ev_mention_30       |               -0.132 |
| rarity_ultra rare   |               -0.099 |
| pet_dn_3            |               -0.086 |
| ev_age              |                0.188 |
| rarity_up_share_30  |                0.202 |
| n_up_30             |                0.206 |
| days_since_change   |                0.207 |
| pet_up_3            |                0.208 |
| elve_kind_demand_14 |                0.287 |
| last_change         |                0.349 |
| elve_demand_7       |                0.724 |