# Forward test — the post-freeze 2026 cohort (TRUE out-of-sample)

**EARLY READ — cohort is 0-5 months old; listing-pop/1m/3m only, NO 1y/3y verdicts possible yet**

Cohort: **82** never-seen IPOs, **82** scored (features at IPO time, analog pool = pre-refresh snapshot only).

## Score buckets vs realized early outcomes

| bucket | n | median score | median pop % | median 1m % (n) | median 3m % (n) |
|---|---|---|---|---|---|
| B1 (higher=better) | 28 | 33.1 | 0.0 | -7.7 (20) | -11.3 (12) |
| B2 (higher=better) | 27 | 43.1 | 0.0 | 2.9 (23) | 5.8 (16) |
| B3 (higher=better) | 27 | 57.7 | 0.3 | 6.7 (22) | 8.4 (14) |

## Wipeout red-flags vs early outcomes

- flagged (≥1 flag): n=38, median pop 0.0%, median 1m -7.7%
- clean (0 flags):   n=44, median pop 0.0%, median 1m 2.9%

## GMP → listing pop (the short-horizon signal)

- n=56, Spearman 0.241; median pop when GMP≥20%: None% vs GMP<20%: 0.0%

_Cells below the min-N floor print None — insufficient sample, by design. Re-run `run_forward_test.py` as the cohort ages._
