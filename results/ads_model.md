# Elve model with trade-ad features: 7-day up/flat/down

_Run on Kaggle (GPU, XGBoost) on 2026-11-12 from commit 6cb8632, with the Elvebredd ad backfill about 60% complete.
Summary table pasted from the notebook output; the per-month file was not downloaded. Rerun `python elve_model.py ads`
after the backfill finishes to replace this._

_Window with ad features: 2025-02-24 to 2026-11-11, 802 pets, 1,504,574 rows. Flat = move under 2%.
Ad feature coverage: Elvebredd 95–99% of rows, AMVGG 11–12% (its ads start 2026-08-20)._

Walk-forward by month (19 test months, 2025-05 to 2026-11), averages:

| model                     | accuracy | macro F1 | up precision | up recall | down precision | down recall | log loss | top-20 mean 7d change | universe mean change |
|:--------------------------|---------:|---------:|-------------:|----------:|---------------:|------------:|---------:|----------------------:|---------------------:|
| always flat               |    0.900 |    0.316 |        0.000 |     0.000 |          0.000 |       0.000 |    0.693 |                -0.001 |                 -0.0 |
| repeat last change (30d)  |    0.724 |    0.456 |        0.181 |     0.570 |          0.191 |       0.533 |    1.910 |                 0.019 |                 -0.0 |
| logistic regression       |    0.899 |    0.457 |        0.404 |     0.158 |          0.443 |       0.154 |    0.353 |                 0.034 |                 -0.0 |
| gradient boosting         |    0.902 |    0.439 |        0.458 |     0.145 |          0.537 |       0.113 |    0.330 |                 0.045 |                 -0.0 |
| logistic regression + ads |    0.899 |    0.458 |        0.414 |     0.161 |          0.457 |       0.149 |    0.346 |                 0.039 |                 -0.0 |
| gradient boosting + ads   |    0.903 |    0.440 |        0.479 |     0.143 |          0.544 |       0.113 |    0.326 |                 0.055 |                 -0.0 |
