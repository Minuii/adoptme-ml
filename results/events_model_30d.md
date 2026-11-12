# Elve model with game-update (news) features: 30-day up/flat/down

_Kaggle (GPU, XGBoost), 2026-11-12, commit c27b66e. Pasted from the notebook log. This run also tested 2024-01, which
had only one month of training data; the fixed split (from commit after c27b66e) starts 30-day tests at 2024-02._

_Window 2023-10-01 to 2026-11-11, 4,812 pet variants, 2,657,808 rows. Flat = move under 5%. Class shares down/flat/up: 7.8%, 84.9%, 7.4%._

Walk-forward by month (34 test months, 2024-01 → 2026-10), averages:

| model                        | accuracy | macro F1 | up precision | up recall | down precision | down recall | log loss | top-20 mean 30d change | universe mean change |
|:-----------------------------|---------:|---------:|-------------:|----------:|---------------:|------------:|---------:|-----------------------:|---------------------:|
| always flat                  |    0.843 |    0.303 |        0.000 |     0.000 |          0.000 |       0.000 |    1.088 |                  0.004 |                0.005 |
| repeat last change (30d)     |    0.777 |    0.499 |        0.309 |     0.420 |          0.273 |       0.361 |    1.546 |                  0.078 |                0.005 |
| logistic regression          |    0.810 |    0.433 |        0.403 |     0.232 |          0.433 |       0.138 |    0.590 |                  0.074 |                0.005 |
| gradient boosting            |    0.827 |    0.447 |        0.398 |     0.199 |          0.490 |       0.181 |    0.483 |                  0.114 |                0.005 |
| logistic regression + events |    0.806 |    0.442 |        0.406 |     0.239 |          0.440 |       0.168 |    0.619 |                  0.078 |                0.005 |
| gradient boosting + events   |    0.829 |    0.458 |        0.403 |     0.197 |          0.519 |       0.208 |    0.478 |                  0.129 |                0.005 |

Gradient boosting + events beats gradient boosting on macro F1 in 25 of 34 months (1 tie). In the last fold's logistic model,
`ev_mention_30` pushes toward down (pets in recent update posts are new and settle lower).
