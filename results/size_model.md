# Elve size model (offers + news): expected % change over 7 days, with a 10-90% range

_Window 2023-10-01 to 2026-11-11, 1,504,574 rows (offer months only). Flat = move under 2%. Class shares down/flat/up: 3.4%, 93.4%, 3.3%._

Walk-forward by month (19 test months), averages. pp = percentage points of value change.

| model                    |   MAE (pp) |   MAE on movers (pp) |   direction right on movers |   rank IC |   top-20 mean 7d change |
|:-------------------------|-----------:|---------------------:|----------------------------:|----------:|------------------------:|
| no change                |      1.290 |               12.683 |                       0.000 |   nan     |                 nan     |
| repeat last change (30d) |      3.248 |               11.434 |                       0.556 |     0.283 |                   0.028 |
| direct regression        |      1.901 |               11.174 |                       0.797 |     0.268 |                   0.054 |
| two-part (expected)      |      1.674 |               11.247 |                       0.805 |     0.275 |                   0.064 |
| median (q50)             |      1.285 |               12.512 |                       0.771 |     0.290 |                   0.038 |


## Top-20 picks: how solid is the gain

Mean 7-day change of the picks. *new picks every 7d* counts each bet once (daily picks are held 7 days and overlap); *value >= 0.25* leaves out penny pets, where one step of the list is a huge % move.

| model                    |   top-20 mean 7d change |   top-20 median |   top-20, new picks every 7d |   top-20, value >= 0.25 |   top-20, default only |   top-20, neon only |   top-20, mega only |   universe mean change |
|:-------------------------|------------------------:|----------------:|-----------------------------:|------------------------:|-----------------------:|--------------------:|--------------------:|-----------------------:|
| no change                |                 nan     |         nan     |                      nan     |                 nan     |                nan     |             nan     |             nan     |                 -0.000 |
| repeat last change (30d) |                   0.028 |           0.000 |                        0.024 |                   0.028 |                  0.033 |               0.021 |               0.017 |                 -0.000 |
| direct regression        |                   0.054 |           0.011 |                        0.052 |                   0.059 |                  0.045 |               0.044 |               0.040 |                 -0.000 |
| two-part (expected)      |                   0.064 |           0.019 |                        0.059 |                   0.068 |                  0.049 |               0.044 |               0.040 |                 -0.000 |
| median (q50)             |                   0.038 |           0.016 |                        0.037 |                   0.037 |                  0.039 |               0.031 |               0.028 |                 -0.000 |


### Range over months (90%, months resampled 2,000 times)

| model                    | picks                      |   months |   mean |    5% |   95% |   months beating all pets |
|:-------------------------|:---------------------------|---------:|-------:|------:|------:|--------------------------:|
| repeat last change (30d) | top-20 mean 7d change      |       19 |  0.028 | 0.018 | 0.039 |                     1.000 |
| repeat last change (30d) | top-20, new picks every 7d |       19 |  0.024 | 0.012 | 0.037 |                     0.842 |
| direct regression        | top-20 mean 7d change      |       19 |  0.054 | 0.035 | 0.076 |                     0.947 |
| direct regression        | top-20, new picks every 7d |       19 |  0.052 | 0.028 | 0.076 |                     0.895 |
| two-part (expected)      | top-20 mean 7d change      |       19 |  0.064 | 0.045 | 0.086 |                     1.000 |
| two-part (expected)      | top-20, new picks every 7d |       19 |  0.059 | 0.041 | 0.078 |                     0.947 |
| median (q50)             | top-20 mean 7d change      |       19 |  0.038 | 0.022 | 0.054 |                     0.947 |
| median (q50)             | top-20, new picks every 7d |       19 |  0.037 | 0.025 | 0.049 |                     0.947 |


## Range (10%-90% quantiles)

Coverage should be about 0.80. A zero-width range means the model expects no change at all.

|                            |   10-90% range |
|:---------------------------|---------------:|
| coverage                   |          0.901 |
| coverage on movers         |          0.096 |
| mean width (pp)            |          0.506 |
| share of zero-width ranges |          0.504 |


## Per month: rank IC

| month   |   direct regression |   median (q50) |   no change |   repeat last change (30d) |   two-part (expected) |
|:--------|--------------------:|---------------:|------------:|---------------------------:|----------------------:|
| 2025-05 |               0.191 |          0.205 |         nan |                      0.236 |                 0.213 |
| 2025-06 |               0.164 |          0.214 |         nan |                      0.164 |                 0.171 |
| 2025-07 |               0.254 |          0.270 |         nan |                      0.225 |                 0.249 |
| 2025-08 |               0.196 |          0.276 |         nan |                      0.244 |                 0.195 |
| 2025-09 |               0.193 |          0.320 |         nan |                      0.363 |                 0.199 |
| 2025-10 |               0.268 |          0.314 |         nan |                      0.359 |                 0.263 |
| 2025-11 |               0.227 |          0.268 |         nan |                      0.267 |                 0.239 |
| 2025-12 |               0.261 |          0.268 |         nan |                      0.273 |                 0.271 |
| 2026-01 |               0.270 |          0.278 |         nan |                      0.257 |                 0.268 |
| 2026-02 |               0.251 |          0.254 |         nan |                      0.277 |                 0.258 |
| 2026-03 |               0.327 |          0.325 |         nan |                      0.336 |                 0.336 |
| 2026-04 |               0.328 |          0.318 |         nan |                      0.262 |                 0.333 |
| 2026-05 |               0.306 |          0.329 |         nan |                      0.215 |                 0.352 |
| 2026-06 |               0.355 |          0.372 |         nan |                      0.361 |                 0.361 |
| 2026-07 |               0.337 |          0.370 |         nan |                      0.357 |                 0.351 |
| 2026-08 |               0.335 |          0.337 |         nan |                      0.334 |                 0.337 |
| 2026-09 |               0.261 |          0.281 |         nan |                      0.268 |                 0.250 |
| 2026-10 |               0.305 |          0.314 |         nan |                      0.355 |                 0.330 |
| 2026-11 |               0.261 |          0.189 |         nan |                      0.229 |                 0.256 |


## Forecast from 2026-11-11: top 15 expected rises and drops (full list in forecast.csv)

| name                         | label             |   value |   p_up |   p_down |   expected |    q10 |   q90 |
|:-----------------------------|:------------------|--------:|-------:|---------:|-----------:|-------:|------:|
| Silverback Gorilla           | default no potion |  10.000 |  0.826 |    0.069 |      0.210 | -0.098 | 0.217 |
| Silverback Gorilla           | neon fly ride     |  44.000 |  0.787 |    0.109 |      0.169 | -0.103 | 0.192 |
| Silverback Gorilla           | mega fly ride     | 180.000 |  0.802 |    0.113 |      0.163 | -0.099 | 0.185 |
| Field Mouse                  | default no potion |   5.750 |  0.647 |    0.010 |      0.133 | -0.000 | 0.001 |
| Emperor Gorilla              | mega fly ride     | 186.000 |  0.353 |    0.119 |      0.132 | -0.066 | 0.000 |
| Field Mouse                  | mega fly ride     | 108.000 |  0.715 |    0.010 |      0.129 | -0.000 | 0.006 |
| Field Mouse                  | neon fly ride     |  26.000 |  0.689 |    0.016 |      0.120 | -0.000 | 0.006 |
| Sakura Spirit                | default no potion |   9.750 |  0.761 |    0.035 |      0.097 | -0.000 | 0.194 |
| Border Collie                | neon fly ride     |  57.000 |  0.787 |    0.026 |      0.087 | -0.000 | 0.187 |
| Border Collie                | default no potion |  14.500 |  0.783 |    0.027 |      0.086 | -0.000 | 0.190 |
| Sakura Spirit                | mega fly ride     | 174.000 |  0.736 |    0.043 |      0.085 | -0.000 | 0.184 |
| Sakura Spirit                | neon fly ride     |  43.000 |  0.739 |    0.047 |      0.082 | -0.000 | 0.195 |
| Pirate Ghost Capuchin Monkey | mega fly ride     | 170.000 |  0.223 |    0.200 |      0.081 | -0.081 | 0.000 |
| Border Collie                | mega fly ride     | 224.000 |  0.732 |    0.042 |      0.077 | -0.000 | 0.178 |
| Mermicorn                    | mega fly ride     | 360.000 |  0.613 |    0.035 |      0.067 | -0.000 | 0.131 |
| Latte Kitsune                | neon fly ride     |  20.000 |  0.035 |    0.834 |     -0.167 | -0.224 | 0.004 |
| Latte Kitsune                | mega fly ride     |  84.000 |  0.033 |    0.852 |     -0.167 | -0.224 | 0.010 |
| Royal Mistletroll            | neon fly ride     | 130.000 |  0.023 |    0.865 |     -0.167 | -0.167 | 0.007 |
| Latte Kitsune                | default no potion |   4.250 |  0.058 |    0.792 |     -0.177 | -0.218 | 0.004 |
| Flash Weasel                 | mega fly ride     | 390.000 |  0.043 |    0.848 |     -0.188 | -0.274 | 0.000 |
| Haetyphoon                   | neon fly ride     | 110.000 |  0.025 |    0.887 |     -0.190 | -0.368 | 0.000 |
| Haetyphoon                   | default no potion |  25.000 |  0.022 |    0.900 |     -0.218 | -0.402 | 0.000 |
| Haetyphoon                   | mega fly ride     | 470.000 |  0.035 |    0.871 |     -0.219 | -0.374 | 0.000 |
| Thunderfisher                | neon fly ride     |   1.900 |  0.002 |    0.869 |     -0.248 | -0.381 | 0.000 |
| Thunderfisher                | mega fly ride     |   8.000 |  0.003 |    0.888 |     -0.350 | -0.414 | 0.000 |
| Flash Weasel                 | default no potion |  20.000 |  0.021 |    0.885 |     -0.351 | -0.361 | 0.000 |
| Electric Hornet              | mega fly ride     |  15.200 |  0.002 |    0.868 |     -0.358 | -0.333 | 0.000 |
| Electric Hornet              | neon fly ride     |   3.550 |  0.002 |    0.883 |     -0.392 | -0.293 | 0.000 |
| Electric Hornet              | default no potion |   0.550 |  0.002 |    0.875 |     -0.465 | -0.325 | 0.000 |
| Thunderfisher                | default no potion |   0.230 |  0.002 |    0.901 |     -0.500 | -0.449 | 0.000 |