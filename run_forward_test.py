"""Run the TRUE out-of-sample forward test on the newly-refreshed cohort (read-only).

    PYTHONPATH=. python run_forward_test.py

Scores every never-seen IPO against the PRE-REFRESH snapshot only, compares with
realized early outcomes, prints the tables, and writes
docs/research/forward_test_2026.md. Re-run any time — the read hardens as the
cohort ages. EVERY figure is an EARLY READ (no 1y/3y verdicts possible yet).
"""
import json
import sys

from layer3 import forward_test as ft


def main():
    old, new = ft.load_frames()
    cohort = ft.forward_cohort(old, new)
    print(f"forward cohort (never-seen, listed): {len(cohort)} IPOs "
          f"({(cohort['type'] == 'MB').sum()} MB / {(cohort['type'] == 'SME').sum()} SME)")
    if not len(cohort):
        print("nothing to test — run a refresh first")
        return
    print("scoring against the pre-refresh snapshot (as-if at IPO time)…")
    scored = ft.score_cohort(cohort, old)
    res = ft.analyze(scored)
    print(json.dumps(res, indent=1, default=str))

    lines = ["# Forward test — the post-freeze 2026 cohort (TRUE out-of-sample)", "",
             f"**{res['label']}**", "",
             f"Cohort: **{res['n_cohort']}** never-seen IPOs, **{res['n_scored']}** scored "
             "(features at IPO time, analog pool = pre-refresh snapshot only).", ""]
    if "score_buckets" in res:
        lines += ["## Score buckets vs realized early outcomes", "",
                  "| bucket | n | median score | median pop % | median 1m % (n) | median 3m % (n) |",
                  "|---|---|---|---|---|---|"]
        for b in res["score_buckets"]:
            lines.append(f"| {b['score_bucket']} | {b['n']} | {b['median_score']} | {b['median_pop_%']} | "
                         f"{b['median_1m_%']} ({b['n_1m']}) | {b['median_3m_%']} ({b['n_3m']}) |")
        lines.append("")
    wf = res["wipeout_flags"]
    lines += ["## Wipeout red-flags vs early outcomes", "",
              f"- flagged (≥1 flag): n={wf['flagged']['n']}, median pop {wf['flagged']['median_pop_%']}%, "
              f"median 1m {wf['flagged']['median_1m_%']}%",
              f"- clean (0 flags):   n={wf['clean']['n']}, median pop {wf['clean']['median_pop_%']}%, "
              f"median 1m {wf['clean']['median_1m_%']}%", ""]
    if "gmp_pop" in res:
        g = res["gmp_pop"]
        lines += ["## GMP → listing pop (the short-horizon signal)", "",
                  f"- n={g['n']}, Spearman {g['spearman']}; median pop when GMP≥20%: "
                  f"{g['median_pop_when_gmp_ge_20']}% vs GMP<20%: {g['median_pop_when_gmp_lt_20']}%", ""]
    lines += ["_Cells below the min-N floor print None — insufficient sample, by design. "
              "Re-run `run_forward_test.py` as the cohort ages._", ""]
    out = "docs/research/forward_test_2026.md"
    open(out, "w").write("\n".join(lines))
    print(f"\nwritten: {out}")


if __name__ == "__main__":
    main()
