# Showdown P4 — Mutation Validation of the Test Suite

**28/28 mutants killed** · 0 survived · 0 bad patterns

Each row = a deliberate code break; KILLED means at least one test failed (the net works there). SURVIVED = vacuous coverage -> a test was added.

| mutation | result | test scope |
|---|---|---|
| spine.combined_exit peak-first->TP | KILLED | `tests/layer3/test_gap_math.py` |
| spine.basket top-slice | KILLED | `tests/layer3/test_gap_math.py` |
| spine.allotment capture=allot*pop | KILLED | `tests/layer3/test_gap_math.py` |
| spine.average_down blend | KILLED | `tests/layer3/test_gap_math.py` |
| spine.partial_exit blend | KILLED | `tests/layer3/test_gap_math.py` |
| spine.lifecycle 90d window | KILLED | `tests/layer3/test_gap_math.py` |
| spine.outcome_profile 2x threshold | KILLED | `tests/layer3/test_gap_math.py` |
| spine.bootstrap median->mean | KILLED | `tests/layer3/test_gap_math.py` |
| scorecard.multibagger scale | KILLED | `tests/layer3/test_gap_math.py` |
| scorecard.tradeable scale | KILLED | `tests/layer3/test_gap_math.py` |
| scorecard.downside weights | KILLED | `tests/layer3/test_gap_math.py` |
| scorecard.return_potential squash | KILLED | `tests/layer3/test_gap_math.py` |
| scorecard.wipeout_safety unknown!=unsafe | KILLED | `tests/layer3/test_gap_math.py` |
| 07.terminal wipeout=0 | KILLED | `tests/pipeline/test_compute_synthetic.py` |
| 07.horizon rfi formula | KILLED | `tests/pipeline/test_compute_synthetic.py` |
| 07.mfe coverage gate | KILLED | `tests/pipeline/test_compute_synthetic.py` |
| 07.mfe clamp direction | KILLED | `tests/pipeline/test_compute_synthetic.py` |
| 07.adj_factor strict-gt | KILLED | `tests/pipeline/test_returns_math.py` |
| remediation factor band | KILLED | `tests/pipeline/test_listing_remediation.py` |
| remediation wipeout threshold | KILLED | `tests/pipeline/test_listing_remediation.py` |
| remediation coverage gap 30d | KILLED | `tests/pipeline/test_listing_remediation.py` |
| merge mfe/mae swap | KILLED | `tests/pipeline/test_merge_math.py` |
| lib fiscal April boundary | KILLED | `tests/pipeline/test_lib.py` |
| lib fnum comma strip | KILLED | `tests/pipeline/test_lib.py` |
| bhavcopy first-wins guard | KILLED | `tests/scrapers/test_bhavcopy_parse.py` |
| corp_actions bonus math | KILLED | `tests/scrapers/test_corp_actions_parse.py` |
| analogs alias lookup | KILLED | `tests/layer3/test_gap_math.py` |
| engine measure mapping | KILLED | `tests/layer3/test_gap_math.py` |
