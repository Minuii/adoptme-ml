# Elve model with offer and game-update (news) features: 90-day up/flat/down

_Window 2023-10-01 to 2026-11-12, 4,812 pet variants, 1,506,980 rows. Flat = move under 10%. Class shares down/flat/up: 12.5%, 75.7%, 11.8%._

Walk-forward by month (13 test months), averages:

| model                                 |   accuracy |   macro F1 |   up precision |   up recall |   down precision |   down recall |   log loss |   up avg precision |   up precision @30% recall |   down avg precision |   down precision @30% recall |   top-20 mean 90d change |
|:--------------------------------------|-----------:|-----------:|---------------:|------------:|-----------------:|--------------:|-----------:|-------------------:|---------------------------:|---------------------:|-----------------------------:|-------------------------:|
| always flat                           |      0.623 |      0.251 |          0.000 |       0.000 |            0.000 |         0.000 |      2.609 |              0.157 |                      0.157 |                0.220 |                        0.220 |                  nan     |
| repeat last change (30d)              |      0.579 |      0.449 |          0.350 |       0.351 |            0.431 |         0.322 |      2.911 |              0.222 |                      0.271 |                0.285 |                        0.322 |                    0.142 |
| logistic regression                   |      0.624 |      0.396 |          0.552 |       0.143 |            0.497 |         0.189 |      0.969 |              0.304 |                      0.342 |                0.365 |                        0.413 |                    0.194 |
| gradient boosting                     |      0.585 |      0.408 |          0.376 |       0.209 |            0.450 |         0.247 |      1.006 |              0.276 |                      0.311 |                0.383 |                        0.428 |                    0.133 |
| logistic regression + offers          |      0.609 |      0.402 |          0.531 |       0.160 |            0.503 |         0.225 |      0.945 |              0.342 |                      0.401 |                0.389 |                        0.454 |                    0.245 |
| gradient boosting + offers            |      0.574 |      0.417 |          0.390 |       0.245 |            0.486 |         0.267 |      0.997 |              0.301 |                      0.350 |                0.409 |                        0.476 |                    0.189 |
| logistic regression + events          |      0.623 |      0.400 |          0.536 |       0.148 |            0.488 |         0.197 |      0.966 |              0.306 |                      0.342 |                0.367 |                        0.422 |                    0.192 |
| gradient boosting + events            |      0.586 |      0.391 |          0.355 |       0.196 |            0.478 |         0.199 |      1.033 |              0.262 |                      0.290 |                0.387 |                        0.430 |                    0.128 |
| logistic regression + offers + events |      0.609 |      0.408 |          0.518 |       0.168 |            0.495 |         0.239 |      0.940 |              0.342 |                      0.399 |                0.389 |                        0.456 |                    0.248 |
| gradient boosting + offers + events   |      0.572 |      0.399 |          0.371 |       0.242 |            0.503 |         0.213 |      1.019 |              0.288 |                      0.325 |                0.406 |                        0.467 |                    0.178 |


## Top-20 picks: how solid is the gain

Mean 90-day change of the picks. *new picks every 90d* counts each bet once (daily picks are held 90 days and overlap); *value >= 0.25* leaves out penny pets, where one step of the list is a huge % move.

| model                                 |   top-20 mean 90d change |   top-20 median |   top-20, new picks every 90d |   top-20, value >= 0.25 |   top-20, default only |   top-20, neon only |   top-20, mega only |   universe mean change |
|:--------------------------------------|-------------------------:|----------------:|------------------------------:|------------------------:|-----------------------:|--------------------:|--------------------:|-----------------------:|
| always flat                           |                  nan     |         nan     |                       nan     |                 nan     |                nan     |             nan     |             nan     |                  0.007 |
| repeat last change (30d)              |                    0.142 |           0.040 |                         0.121 |                   0.143 |                  0.199 |               0.134 |               0.117 |                  0.007 |
| logistic regression                   |                    0.194 |           0.144 |                         0.185 |                   0.198 |                  0.150 |               0.215 |               0.189 |                  0.007 |
| gradient boosting                     |                    0.133 |           0.049 |                         0.131 |                   0.131 |                  0.160 |               0.123 |               0.124 |                  0.007 |
| logistic regression + offers          |                    0.245 |           0.174 |                         0.250 |                   0.244 |                  0.175 |               0.260 |               0.225 |                  0.007 |
| gradient boosting + offers            |                    0.189 |           0.093 |                         0.167 |                   0.194 |                  0.201 |               0.182 |               0.175 |                  0.007 |
| logistic regression + events          |                    0.192 |           0.137 |                         0.178 |                   0.195 |                  0.152 |               0.212 |               0.180 |                  0.007 |
| gradient boosting + events            |                    0.128 |           0.060 |                         0.146 |                   0.133 |                  0.125 |               0.121 |               0.125 |                  0.007 |
| logistic regression + offers + events |                    0.248 |           0.173 |                         0.233 |                   0.249 |                  0.184 |               0.265 |               0.229 |                  0.007 |
| gradient boosting + offers + events   |                    0.178 |           0.090 |                         0.162 |                   0.196 |                  0.180 |               0.168 |               0.167 |                  0.007 |


### Range over months (90%, months resampled 2,000 times)

| model                                 | picks                       |   months |   mean |    5% |   95% |   months beating all pets |
|:--------------------------------------|:----------------------------|---------:|-------:|------:|------:|--------------------------:|
| repeat last change (30d)              | top-20 mean 90d change      |       13 |  0.142 | 0.100 | 0.188 |                     1.000 |
| repeat last change (30d)              | top-20, new picks every 90d |       13 |  0.121 | 0.069 | 0.179 |                     0.923 |
| logistic regression                   | top-20 mean 90d change      |       13 |  0.194 | 0.111 | 0.283 |                     0.769 |
| logistic regression                   | top-20, new picks every 90d |       13 |  0.185 | 0.077 | 0.302 |                     0.692 |
| gradient boosting                     | top-20 mean 90d change      |       13 |  0.133 | 0.091 | 0.174 |                     1.000 |
| gradient boosting                     | top-20, new picks every 90d |       13 |  0.131 | 0.075 | 0.193 |                     0.846 |
| logistic regression + offers          | top-20 mean 90d change      |       13 |  0.245 | 0.154 | 0.341 |                     0.846 |
| logistic regression + offers          | top-20, new picks every 90d |       13 |  0.250 | 0.141 | 0.368 |                     0.846 |
| gradient boosting + offers            | top-20 mean 90d change      |       13 |  0.189 | 0.131 | 0.245 |                     0.923 |
| gradient boosting + offers            | top-20, new picks every 90d |       13 |  0.167 | 0.094 | 0.255 |                     0.923 |
| logistic regression + events          | top-20 mean 90d change      |       13 |  0.192 | 0.111 | 0.275 |                     0.769 |
| logistic regression + events          | top-20, new picks every 90d |       13 |  0.178 | 0.076 | 0.289 |                     0.769 |
| gradient boosting + events            | top-20 mean 90d change      |       13 |  0.128 | 0.079 | 0.178 |                     1.000 |
| gradient boosting + events            | top-20, new picks every 90d |       13 |  0.146 | 0.081 | 0.219 |                     0.846 |
| logistic regression + offers + events | top-20 mean 90d change      |       13 |  0.248 | 0.155 | 0.337 |                     0.846 |
| logistic regression + offers + events | top-20, new picks every 90d |       13 |  0.233 | 0.127 | 0.352 |                     0.769 |
| gradient boosting + offers + events   | top-20 mean 90d change      |       13 |  0.178 | 0.114 | 0.243 |                     0.923 |
| gradient boosting + offers + events   | top-20, new picks every 90d |       13 |  0.162 | 0.088 | 0.241 |                     0.846 |


## Per month: macro F1

| month   |   always flat |   gradient boosting |   gradient boosting + events |   gradient boosting + offers |   gradient boosting + offers + events |   logistic regression |   logistic regression + events |   logistic regression + offers |   logistic regression + offers + events |   repeat last change (30d) |
|:--------|--------------:|--------------------:|-----------------------------:|-----------------------------:|--------------------------------------:|----------------------:|-------------------------------:|-------------------------------:|----------------------------------------:|---------------------------:|
| 2025-08 |         0.288 |               0.464 |                        0.456 |                        0.453 |                                 0.457 |                 0.377 |                          0.409 |                          0.377 |                                   0.406 |                      0.495 |
| 2025-09 |         0.283 |               0.437 |                        0.418 |                        0.441 |                                 0.410 |                 0.391 |                          0.390 |                          0.387 |                                   0.391 |                      0.497 |
| 2025-10 |         0.272 |               0.444 |                        0.420 |                        0.449 |                                 0.428 |                 0.396 |                          0.399 |                          0.397 |                                   0.400 |                      0.466 |
| 2025-11 |         0.276 |               0.445 |                        0.409 |                        0.449 |                                 0.423 |                 0.423 |                          0.428 |                          0.435 |                                   0.438 |                      0.495 |
| 2025-12 |         0.273 |               0.441 |                        0.400 |                        0.458 |                                 0.415 |                 0.458 |                          0.459 |                          0.463 |                                   0.468 |                      0.490 |
| 2026-01 |         0.265 |               0.465 |                        0.429 |                        0.487 |                                 0.440 |                 0.453 |                          0.454 |                          0.461 |                                   0.466 |                      0.493 |
| 2026-02 |         0.177 |               0.340 |                        0.311 |                        0.369 |                                 0.341 |                 0.276 |                          0.278 |                          0.298 |                                   0.308 |                      0.375 |
| 2026-03 |         0.164 |               0.315 |                        0.308 |                        0.346 |                                 0.326 |                 0.295 |                          0.302 |                          0.337 |                                   0.347 |                      0.384 |
| 2026-04 |         0.157 |               0.320 |                        0.300 |                        0.350 |                                 0.323 |                 0.312 |                          0.308 |                          0.354 |                                   0.355 |                      0.424 |
| 2026-05 |         0.261 |               0.459 |                        0.446 |                        0.478 |                                 0.470 |                 0.405 |                          0.404 |                          0.410 |                                   0.414 |                      0.317 |
| 2026-06 |         0.274 |               0.414 |                        0.406 |                        0.452 |                                 0.429 |                 0.479 |                          0.475 |                          0.481 |                                   0.479 |                      0.471 |
| 2026-07 |         0.285 |               0.369 |                        0.392 |                        0.354 |                                 0.383 |                 0.461 |                          0.463 |                          0.415 |                                   0.413 |                      0.476 |
| 2026-08 |         0.289 |               0.387 |                        0.384 |                        0.337 |                                 0.344 |                 0.425 |                          0.431 |                          0.415 |                                   0.422 |                      0.448 |


## Logistic regression: features pushing toward up (+) or down (-), last fold

|                     |   up minus down coef |
|:--------------------|---------------------:|
| elve_demand_chg     |               -0.336 |
| rarity_legendary    |               -0.239 |
| rarity_ultra rare   |               -0.188 |
| pet_dn_14           |               -0.178 |
| mkt_moves_7         |               -0.168 |
| ev_mention_30       |               -0.104 |
| n_dn_30             |               -0.098 |
| rarity_up_share_30  |               -0.079 |
| elve_offer_7        |                0.197 |
| ev_age              |                0.237 |
| last_change         |                0.249 |
| rarity_uncommon     |                0.289 |
| elve_want_7         |                0.317 |
| elve_kind_demand_14 |                0.401 |
| days_since_change   |                0.439 |
| elve_demand_7       |                0.573 |