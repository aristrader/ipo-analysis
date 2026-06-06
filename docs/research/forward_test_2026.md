# Forward test — the post-freeze 2026 cohort (TRUE out-of-sample)

**EARLY READ — cohort is 0-5 months old; listing-pop/1m/3m only, NO 1y/3y verdicts possible yet**

Cohort: **82** never-seen IPOs, **82** scored (features at IPO time, analog pool = pre-refresh snapshot only).

## Score buckets vs realized early outcomes

| bucket | n | median score | median pop % | median 1m % (n) | median 3m % (n) |
|---|---|---|---|---|---|
| B1 (higher=better) | 28 | 33.1 | None | None (1) | None (0) |
| B2 (higher=better) | 27 | 43.1 | None | None (0) | None (0) |
| B3 (higher=better) | 27 | 57.7 | None | None (0) | None (0) |

## Wipeout red-flags vs early outcomes

- flagged (≥1 flag): n=38, median pop 0.0%, median 1m None%
- clean (0 flags):   n=44, median pop None%, median 1m None%

## GMP → listing pop (the short-horizon signal)

- n=12, Spearman 0.525; median pop when GMP≥20%: None% vs GMP<20%: 12.7%

_Cells below the min-N floor print None — insufficient sample, by design. Re-run `run_forward_test.py` as the cohort ages._
