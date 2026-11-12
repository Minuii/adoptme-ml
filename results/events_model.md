# Elve model with game-update (news) features: 7-day up/flat/down

_Window 2023-10-01 to 2026-11-11, 4,812 pet variants, 2,657,808 rows. Flat = move under 2%. Class shares down/flat/up: 3.4%, 93.4%, 3.3%._

Walk-forward by month (6 test months), averages:

| model                        |   accuracy |   macro F1 |   up precision |   up recall |   down precision |   down recall |   log loss |   top-20 mean 7d change |   universe mean change |
|:-----------------------------|-----------:|-----------:|---------------:|------------:|-----------------:|--------------:|-----------:|------------------------:|-----------------------:|
| always flat                  |      0.894 |      0.315 |          0.000 |       0.000 |            0.000 |         0.000 |      0.735 |                  -0.001 |                  0.000 |
| repeat last change (30d)     |      0.719 |      0.479 |          0.204 |       0.629 |            0.209 |         0.597 |      1.943 |                   0.023 |                  0.000 |
| logistic regression          |      0.890 |      0.516 |          0.357 |       0.244 |            0.430 |         0.262 |      0.372 |                   0.026 |                  0.000 |
| gradient boosting            |      0.898 |      0.511 |          0.496 |       0.249 |            0.548 |         0.197 |      0.314 |                   0.062 |                  0.000 |
| logistic regression + events |      0.889 |      0.522 |          0.360 |       0.240 |            0.428 |         0.290 |      0.370 |                   0.027 |                  0.000 |
| gradient boosting + events   |      0.896 |      0.517 |          0.485 |       0.231 |            0.542 |         0.234 |      0.316 |                   0.063 |                  0.000 |


## Per month

| month   |   always flat |   gradient boosting |   gradient boosting + events |   logistic regression |   logistic regression + events |   repeat last change (30d) |
|:--------|--------------:|--------------------:|-----------------------------:|----------------------:|-------------------------------:|---------------------------:|
| 2026-06 |         0.310 |               0.469 |                        0.475 |                 0.503 |                          0.504 |                      0.453 |
| 2026-07 |         0.313 |               0.505 |                        0.524 |                 0.521 |                          0.524 |                      0.479 |
| 2026-08 |         0.313 |               0.505 |                        0.508 |                 0.500 |                          0.517 |                      0.466 |
| 2026-09 |         0.318 |               0.502 |                        0.514 |                 0.489 |                          0.498 |                      0.441 |
| 2026-10 |         0.318 |               0.533 |                        0.547 |                 0.598 |                          0.605 |                      0.509 |
| 2026-11 |         0.316 |               0.555 |                        0.536 |                 0.482 |                          0.483 |                      0.524 |


## Logistic regression: features pushing toward up (+) or down (-), last fold

|                    |   up minus down coef |
|:-------------------|---------------------:|
| age_days           |               -0.324 |
| rarity_legendary   |               -0.267 |
| pet_dn_14          |               -0.203 |
| kind_mega          |               -0.160 |
| n_dn_30            |               -0.155 |
| ev_mention_30      |               -0.152 |
| rarity_up_share_7  |               -0.137 |
| pet_dn_3           |               -0.072 |
| days_since_change  |                0.165 |
| pet_up_3           |                0.165 |
| n_up_30            |                0.193 |
| ev_age             |                0.196 |
| rarity_uncommon    |                0.197 |
| rarity_up_share_30 |                0.301 |
| last_change        |                0.431 |
| log_value          |                0.438 |