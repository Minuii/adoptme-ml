# Elve model with game-update (news) features: 7-day up/flat/down

_Kaggle (GPU, XGBoost), 2026-11-12, commit c27b66e. Summary pasted from the notebook log; the per-month table was not saved.
The earlier local 6-month run (2026-06 → 11) is described in `log.md`._

_Window 2023-10-01 to 2026-11-11, 4,812 pet variants, 2,657,808 rows. Flat = move under 2%. Class shares down/flat/up: 3.4%, 93.4%, 3.3%._

Walk-forward by month (35 test months, 2024-01 → 2026-11), averages:

| model                        | accuracy | macro F1 | up precision | up recall | down precision | down recall | log loss | top-20 mean 7d change | universe mean change |
|:-----------------------------|---------:|---------:|-------------:|----------:|---------------:|------------:|---------:|----------------------:|---------------------:|
| always flat                  |    0.930 |    0.321 |        0.000 |     0.000 |          0.000 |       0.000 |    0.486 |                 0.000 |                0.001 |
| repeat last change (30d)     |    0.800 |    0.447 |        0.165 |     0.512 |          0.149 |       0.446 |    1.386 |                 0.022 |                0.001 |
| logistic regression          |    0.923 |    0.420 |        0.299 |     0.136 |          0.361 |       0.098 |    0.270 |                 0.027 |                0.001 |
| gradient boosting            |    0.929 |    0.410 |        0.384 |     0.113 |          0.434 |       0.080 |    0.244 |                 0.044 |                0.001 |
| logistic regression + events |    0.921 |    0.425 |        0.302 |     0.136 |          0.362 |       0.113 |    0.270 |                 0.026 |                0.001 |
| gradient boosting + events   |    0.929 |    0.418 |        0.347 |     0.106 |          0.498 |       0.102 |    0.242 |                 0.043 |                0.001 |
