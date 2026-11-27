# Model by value tier: 30-day up/flat/down (gradient boosting + offers + events, the site's model)

_Window 2023-10-01 to 2026-11-25, 17 test months (2025-06 to 2026-10), 1,234,898 test rows. Tier = Elvebredd value on the forecast day. Flat = move under 5% in every tier._

## Calls, pooled over all test rows

*median size of a move* = median |change| of rows that moved more than the flat band. *up recall* = share of real rises the model called. *repeat-last* = repeat the last change's direction (the baseline).

| tier        |   pet variants (newest day) |   test rows |   share up |   share down |   median size of a move |   up calls |   up precision |   up recall |   down precision |   down recall |   up avg precision |   repeat-last: up precision |   repeat-last: down precision |
|:------------|----------------------------:|------------:|-----------:|-------------:|------------------------:|-----------:|---------------:|------------:|-----------------:|--------------:|-------------------:|----------------------------:|------------------------------:|
| <= 1        |                     726.000 |  359066.000 |      0.088 |        0.086 |                   0.167 |  10301.000 |          0.199 |       0.065 |            0.382 |         0.153 |              0.125 |                       0.216 |                         0.293 |
| 1-10        |                    1073.000 |  531982.000 |      0.079 |        0.114 |                   0.143 |  12490.000 |          0.377 |       0.111 |            0.398 |         0.165 |              0.201 |                       0.186 |                         0.336 |
| 10-60       |                     399.000 |  238957.000 |      0.110 |        0.191 |                   0.125 |  12429.000 |          0.477 |       0.226 |            0.488 |         0.219 |              0.355 |                       0.325 |                         0.412 |
| 60-100      |                      55.000 |   31101.000 |      0.201 |        0.194 |                   0.122 |   3187.000 |          0.493 |       0.251 |            0.517 |         0.285 |              0.426 |                       0.380 |                         0.386 |
| > 100       |                     156.000 |   73792.000 |      0.247 |        0.157 |                   0.137 |  13501.000 |          0.521 |       0.386 |            0.517 |         0.316 |              0.486 |                       0.431 |                         0.363 |
| <= 10 (all) |                    1799.000 |  891048.000 |      0.083 |        0.103 |                   0.147 |  22791.000 |          0.296 |       0.092 |            0.393 |         0.161 |              0.162 |                       0.196 |                         0.319 |
| all pets    |                    2409.000 | 1234898.000 |      0.101 |        0.126 |                   0.143 |  51908.000 |          0.410 |       0.171 |            0.440 |         0.195 |              0.261 |                       0.276 |                         0.354 |


## Picks inside each tier: mean 30-day change

Top 5 per day inside a tier (top 20 for *all pets* and *<= 10 (all)*), averaged over months. *tier mean* = the average pet of that tier.

| tier        |   model top-k |   model top-k, new picks every 30d |   repeat-last top-k |   tier mean |
|:------------|--------------:|-----------------------------------:|--------------------:|------------:|
| <= 1        |         0.132 |                              0.097 |               0.073 |       0.011 |
| 1-10        |         0.143 |                              0.160 |               0.052 |      -0.004 |
| 10-60       |         0.145 |                              0.186 |               0.062 |      -0.008 |
| 60-100      |         0.118 |                              0.126 |               0.088 |       0.018 |
| > 100       |         0.111 |                              0.135 |               0.071 |       0.017 |
| <= 10 (all) |         0.122 |                              0.128 |               0.056 |       0.003 |
| all pets    |         0.118 |                              0.143 |               0.056 |       0.001 |


### Range over months (90%, months resampled 2,000 times)

| model       | picks                            |   months |   mean |    5% |   95% |   months beating all pets |
|:------------|:---------------------------------|---------:|-------:|------:|------:|--------------------------:|
| <= 1        | model top-k                      |       17 |  0.132 | 0.078 | 0.192 |                     0.941 |
| <= 1        | model top-k, new picks every 30d |       17 |  0.097 | 0.059 | 0.138 |                     0.882 |
| 1-10        | model top-k                      |       17 |  0.143 | 0.096 | 0.199 |                     1.000 |
| 1-10        | model top-k, new picks every 30d |       17 |  0.160 | 0.105 | 0.222 |                     1.000 |
| 10-60       | model top-k                      |       17 |  0.145 | 0.110 | 0.185 |                     1.000 |
| 10-60       | model top-k, new picks every 30d |       17 |  0.186 | 0.136 | 0.238 |                     1.000 |
| 60-100      | model top-k                      |       17 |  0.118 | 0.092 | 0.147 |                     1.000 |
| 60-100      | model top-k, new picks every 30d |       17 |  0.126 | 0.089 | 0.162 |                     1.000 |
| > 100       | model top-k                      |       17 |  0.111 | 0.074 | 0.148 |                     0.941 |
| > 100       | model top-k, new picks every 30d |       17 |  0.135 | 0.071 | 0.204 |                     0.941 |
| <= 10 (all) | model top-k                      |       17 |  0.122 | 0.087 | 0.163 |                     1.000 |
| <= 10 (all) | model top-k, new picks every 30d |       17 |  0.128 | 0.092 | 0.169 |                     1.000 |
| all pets    | model top-k                      |       17 |  0.118 | 0.090 | 0.148 |                     1.000 |
| all pets    | model top-k, new picks every 30d |       17 |  0.143 | 0.104 | 0.183 |                     1.000 |


## Where the overall top 20 comes from

| tier   |   share_of_picks |   mean_change |
|:-------|-----------------:|--------------:|
| <= 1   |            0.179 |         0.081 |
| 1-10   |            0.195 |         0.131 |
| 10-60  |            0.229 |         0.137 |
| 60-100 |            0.058 |         0.162 |
| > 100  |            0.339 |         0.113 |