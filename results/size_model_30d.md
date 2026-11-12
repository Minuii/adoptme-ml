# Elve size model (offers + news): expected % change over 30 days, with a 10-90% range

_Window 2023-10-01 to 2026-11-11, 1,504,574 rows (offer months only). Flat = move under 5%. Class shares down/flat/up: 7.8%, 84.9%, 7.4%._

Walk-forward by month (17 test months), averages. pp = percentage points of value change.

| model                    |   MAE (pp) |   MAE on movers (pp) |   direction right on movers |   rank IC |   top-20 mean 30d change |
|:-------------------------|-----------:|---------------------:|----------------------------:|----------:|-------------------------:|
| no change                |      5.163 |               21.930 |                       0.000 |   nan     |                  nan     |
| repeat last change (30d) |      6.374 |               20.490 |                       0.445 |     0.325 |                    0.067 |
| direct regression        |      7.123 |               18.854 |                       0.752 |     0.331 |                    0.104 |
| two-part (expected)      |      6.610 |               19.147 |                       0.753 |     0.331 |                    0.120 |
| median (q50)             |      5.067 |               20.928 |                       0.741 |     0.348 |                    0.114 |


## Top-20 picks: how solid is the gain

Mean 30-day change of the picks. *new picks every 30d* counts each bet once (daily picks are held 30 days and overlap); *value >= 0.25* leaves out penny pets, where one step of the list is a huge % move.

| model                    |   top-20 mean 30d change |   top-20 median |   top-20, new picks every 30d |   top-20, value >= 0.25 |   top-20, default only |   top-20, neon only |   top-20, mega only |   universe mean change |
|:-------------------------|-------------------------:|----------------:|------------------------------:|------------------------:|-----------------------:|--------------------:|--------------------:|-----------------------:|
| no change                |                  nan     |         nan     |                       nan     |                 nan     |                nan     |             nan     |             nan     |                  0.001 |
| repeat last change (30d) |                    0.067 |           0.009 |                         0.060 |                   0.066 |                  0.106 |               0.060 |               0.049 |                  0.001 |
| direct regression        |                    0.104 |           0.035 |                         0.088 |                   0.112 |                  0.104 |               0.094 |               0.086 |                  0.001 |
| two-part (expected)      |                    0.120 |           0.038 |                         0.100 |                   0.136 |                  0.115 |               0.114 |               0.098 |                  0.001 |
| median (q50)             |                    0.114 |           0.076 |                         0.145 |                   0.107 |                  0.119 |               0.095 |               0.091 |                  0.001 |


### Range over months (90%, months resampled 2,000 times)

| model                    | picks                       |   months |   mean |    5% |   95% |   months beating all pets |
|:-------------------------|:----------------------------|---------:|-------:|------:|------:|--------------------------:|
| repeat last change (30d) | top-20 mean 30d change      |       17 |  0.067 | 0.039 | 0.097 |                     1.000 |
| repeat last change (30d) | top-20, new picks every 30d |       17 |  0.060 | 0.025 | 0.101 |                     0.824 |
| direct regression        | top-20 mean 30d change      |       17 |  0.104 | 0.068 | 0.146 |                     0.882 |
| direct regression        | top-20, new picks every 30d |       17 |  0.088 | 0.065 | 0.112 |                     0.941 |
| two-part (expected)      | top-20 mean 30d change      |       17 |  0.120 | 0.089 | 0.153 |                     1.000 |
| two-part (expected)      | top-20, new picks every 30d |       17 |  0.100 | 0.075 | 0.123 |                     0.941 |
| median (q50)             | top-20 mean 30d change      |       17 |  0.114 | 0.082 | 0.147 |                     1.000 |
| median (q50)             | top-20, new picks every 30d |       17 |  0.145 | 0.108 | 0.184 |                     1.000 |


## Range (10%-90% quantiles)

Coverage should be about 0.80. A zero-width range means the model expects no change at all.

|                            |   10-90% range |
|:---------------------------|---------------:|
| coverage                   |          0.819 |
| coverage on movers         |          0.292 |
| mean width (pp)            |          9.500 |
| share of zero-width ranges |          0.000 |


## Per month: rank IC

| month   |   direct regression |   median (q50) |   no change |   repeat last change (30d) |   two-part (expected) |
|:--------|--------------------:|---------------:|------------:|---------------------------:|----------------------:|
| 2025-06 |               0.310 |          0.336 |         nan |                      0.247 |                 0.329 |
| 2025-07 |               0.351 |          0.376 |         nan |                      0.301 |                 0.345 |
| 2025-08 |               0.249 |          0.345 |         nan |                      0.337 |                 0.226 |
| 2025-09 |               0.215 |          0.331 |         nan |                      0.368 |                 0.195 |
| 2025-10 |               0.278 |          0.317 |         nan |                      0.317 |                 0.260 |
| 2025-11 |               0.287 |          0.308 |         nan |                      0.317 |                 0.280 |
| 2025-12 |               0.327 |          0.338 |         nan |                      0.315 |                 0.303 |
| 2026-01 |               0.295 |          0.359 |         nan |                      0.336 |                 0.311 |
| 2026-02 |               0.366 |          0.377 |         nan |                      0.314 |                 0.364 |
| 2026-03 |               0.392 |          0.365 |         nan |                      0.339 |                 0.385 |
| 2026-04 |               0.351 |          0.353 |         nan |                      0.269 |                 0.360 |
| 2026-05 |               0.422 |          0.418 |         nan |                      0.305 |                 0.425 |
| 2026-06 |               0.396 |          0.422 |         nan |                      0.413 |                 0.415 |
| 2026-07 |               0.393 |          0.383 |         nan |                      0.395 |                 0.392 |
| 2026-08 |               0.410 |          0.412 |         nan |                      0.376 |                 0.445 |
| 2026-09 |               0.283 |          0.272 |         nan |                      0.288 |                 0.267 |
| 2026-10 |               0.308 |          0.208 |         nan |                      0.288 |                 0.322 |


## Forecast from 2026-11-11: top 15 expected rises and drops (full list in forecast_30d.csv)

| name            | label             |   value |   p_up |   p_down |   expected |    q10 |    q90 |
|:----------------|:------------------|--------:|-------:|---------:|-----------:|-------:|-------:|
| Field Mouse     | mega fly ride     | 108.000 |  0.612 |    0.016 |      0.198 | -0.016 |  0.382 |
| Field Mouse     | default no potion |   5.750 |  0.618 |    0.014 |      0.189 | -0.011 |  0.303 |
| Rose Dragon     | default no potion |   3.350 |  0.779 |    0.015 |      0.187 | -0.011 |  0.310 |
| Cupid Dragon    | neon fly ride     |  39.000 |  0.789 |    0.028 |      0.184 | -0.032 |  0.326 |
| Cupid Dragon    | default no potion |   9.000 |  0.757 |    0.026 |      0.181 | -0.013 |  0.325 |
| Snowball Pug    | default no potion |   0.200 |  0.419 |    0.041 |      0.172 | -0.023 |  0.143 |
| Cabbit          | mega fly ride     | 344.000 |  0.640 |    0.073 |      0.164 | -0.042 |  0.251 |
| Rose Dragon     | neon fly ride     |  16.500 |  0.735 |    0.019 |      0.163 | -0.016 |  0.282 |
| Rose Dragon     | mega fly ride     |  68.000 |  0.758 |    0.018 |      0.160 | -0.016 |  0.337 |
| Field Mouse     | neon fly ride     |  26.000 |  0.559 |    0.016 |      0.157 | -0.016 |  0.287 |
| Cabbit          | neon fly ride     |  86.000 |  0.658 |    0.050 |      0.156 | -0.026 |  0.209 |
| Cupid Dragon    | mega fly ride     | 158.000 |  0.769 |    0.030 |      0.156 | -0.016 |  0.302 |
| Copycat         | mega fly ride     | 170.000 |  0.557 |    0.276 |      0.156 | -0.306 |  0.384 |
| Border Collie   | mega fly ride     | 224.000 |  0.750 |    0.020 |      0.153 | -0.016 |  0.294 |
| Sea Slug        | neon fly ride     |  51.000 |  0.518 |    0.027 |      0.153 | -0.016 |  0.131 |
| Thunderfisher   | neon fly ride     |   1.900 |  0.004 |    0.895 |     -0.321 | -0.567 | -0.008 |
| Tió De Nadal    | neon fly ride     | 102.000 |  0.012 |    0.944 |     -0.338 | -0.226 |  0.026 |
| Tió De Nadal    | default no potion |  25.500 |  0.015 |    0.922 |     -0.343 | -0.227 |  0.025 |
| Tió De Nadal    | mega fly ride     | 412.000 |  0.020 |    0.933 |     -0.359 | -0.259 |  0.026 |
| Electric Hornet | neon fly ride     |   3.550 |  0.002 |    0.949 |     -0.372 | -0.509 | -0.008 |
| Thunderfisher   | mega fly ride     |   8.000 |  0.005 |    0.894 |     -0.424 | -0.610 | -0.008 |
| Electric Hornet | default no potion |   0.550 |  0.002 |    0.933 |     -0.443 | -0.584 | -0.008 |
| Electric Hornet | mega fly ride     |  15.200 |  0.002 |    0.933 |     -0.469 | -0.583 | -0.008 |
| Flash Weasel    | neon fly ride     |  90.000 |  0.079 |    0.836 |     -0.494 | -0.580 |  0.055 |
| Flash Weasel    | default no potion |  20.000 |  0.045 |    0.864 |     -0.507 | -0.580 | -0.000 |
| Flash Weasel    | mega fly ride     | 390.000 |  0.119 |    0.812 |     -0.536 | -0.678 |  0.058 |
| Haetyphoon      | neon fly ride     | 110.000 |  0.029 |    0.946 |     -0.587 | -0.632 |  0.001 |
| Haetyphoon      | default no potion |  25.000 |  0.019 |    0.955 |     -0.604 | -0.648 | -0.000 |
| Haetyphoon      | mega fly ride     | 470.000 |  0.045 |    0.930 |     -0.624 | -0.694 |  0.001 |
| Thunderfisher   | default no potion |   0.230 |  0.005 |    0.898 |     -0.639 | -0.681 | -0.008 |