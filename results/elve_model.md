# Elve-only model: 7-day up/flat/down

_Window 2025-07-14 to 2026-11-10, 4,848 pet variants, 1,099,642 rows. Flat = move under 2%. Class shares down/flat/up: 6.0%, 89.1%, 4.9%._

Walk-forward by month (13 test months), averages:

| model                    |   accuracy |   macro F1 |   up precision |   up recall |   down precision |   down recall |   log loss |   top-20 mean 7d change |   universe mean change |
|:-------------------------|-----------:|-----------:|---------------:|------------:|-----------------:|--------------:|-----------:|------------------------:|-----------------------:|
| always flat              |      0.883 |      0.312 |          0.000 |       0.000 |            0.000 |         0.000 |      0.809 |                  -0.001 |                 -0.002 |
| repeat last change (30d) |      0.686 |      0.455 |          0.181 |       0.583 |            0.214 |         0.571 |      2.168 |                   0.017 |                 -0.002 |
| logistic regression      |      0.883 |      0.475 |          0.443 |       0.174 |            0.494 |         0.188 |      0.406 |                   0.038 |                 -0.002 |
| gradient boosting        |      0.883 |      0.466 |          0.483 |       0.192 |            0.496 |         0.156 |      0.388 |                   0.051 |                 -0.002 |


## Per month

| month   |   always flat |   gradient boosting |   logistic regression |   repeat last change (30d) |
|:--------|--------------:|--------------------:|----------------------:|---------------------------:|
| 2025-11 |         0.320 |               0.482 |                 0.470 |                      0.465 |
| 2025-12 |         0.316 |               0.355 |                 0.474 |                      0.465 |
| 2026-01 |         0.317 |               0.525 |                 0.452 |                      0.441 |
| 2026-02 |         0.324 |               0.435 |                 0.445 |                      0.450 |
| 2026-03 |         0.308 |               0.368 |                 0.369 |                      0.501 |
| 2026-04 |         0.289 |               0.434 |                 0.411 |                      0.437 |
| 2026-05 |         0.299 |               0.413 |                 0.440 |                      0.269 |
| 2026-06 |         0.310 |               0.451 |                 0.515 |                      0.453 |
| 2026-07 |         0.313 |               0.505 |                 0.522 |                      0.479 |
| 2026-08 |         0.313 |               0.464 |                 0.493 |                      0.466 |
| 2026-09 |         0.318 |               0.514 |                 0.488 |                      0.442 |
| 2026-10 |         0.318 |               0.530 |                 0.580 |                      0.509 |
| 2026-11 |         0.316 |               0.581 |                 0.512 |                      0.535 |


## Logistic regression: features pushing toward up (+) or down (-), last fold

|                    |   up minus down coef |
|:-------------------|---------------------:|
| pet_dn_14          |               -0.287 |
| n_dn_30            |               -0.217 |
| rarity_legendary   |               -0.208 |
| rarity_up_share_7  |               -0.200 |
| kind_mega          |               -0.158 |
| pet_dn_3           |               -0.115 |
| rarity_ultra rare  |               -0.093 |
| ret_1              |               -0.069 |
| rarity_common      |                0.123 |
| rarity_up_share_30 |                0.131 |
| ret_7              |                0.172 |
| rarity_uncommon    |                0.184 |
| pet_up_3           |                0.237 |
| n_up_30            |                0.276 |
| log_value          |                0.303 |
| last_change        |                0.431 |