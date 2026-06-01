"""F · The flip trap — the hotter the IPO, the LESS of its pop you can actually capture.

"Apply to the oversubscribed IPO, flip the big listing pop." But the pop and the retail allotment
odds are mechanically INVERSE (allotment ≈ 1/oversubscription): the hottest names show the biggest
pops AND the smallest allotment, so expected capture PER APPLICATION is flat-to-declining across
subscription buckets. The visible pop is a selection illusion you can't size into. Boom-only
(subscription is single-regime), but the arithmetic is regime-independent.
"""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding


def compute(df):
    tables, charts, caveats = [], [], []
    rows = []
    for seg in config.SEGMENTS:
        sub = spine.segment(df, segment=seg, cohort="boom")     # subscription is boom-only
        ac = spine.allotment_capture(sub)
        for b in ac["buckets"]:
            if b.get("insufficient"):
                continue
            rows.append({"segment": seg, **b})
    tables.append(("Flip economics by oversubscription bucket (BOOM cohort, retail allotment ≈ 1/oversubscription). "
                   "The median pop RISES with demand but the median allotment odds COLLAPSE — so 'E_capture_per_"
                   "application' (allotment × pop, what you actually pocket per rupee applied) stays flat-to-tiny "
                   "(~0.2–0.6%) and is often LOWEST for the hottest >50x names despite their ~100% pop-positive rate.",
                   pd.DataFrame(rows)))
    caveats += [
        "BOOM-ONLY: per-symbol subscription doesn't exist in the longterm cohort, so this can't be cross-regime "
        "validated — but the mechanism is an arithmetic identity (allotment ≈ 1/oversubscription), not a regime effect.",
        "Allotment modelled as min(1, 1/oversubscription) — the retail-category reality; actual lottery allotment "
        "for very hot SME issues is even harsher. Excludes `unreliable_coverage` listing rows.",
        "This is the realistic complement to the headline flip number: the raw pop looks great, but adverse "
        "selection (hot = low allotment) means you can't size into it. There is no free flip.",
    ]
    narrative = ("The most popular IPO myth: apply to the heavily oversubscribed issue and flip the pop. The catch "
                 "is arithmetic — the more oversubscribed an IPO, the bigger its pop BUT the smaller your allotment, "
                 "and the two cancel. What a flipper captures per rupee applied is flat-to-declining across demand "
                 "buckets, often worst for the hottest names. The pop is real; it's just not investable.")
    return Finding(id="f_flip", title="F · The flip trap (hot IPO = big pop, tiny allotment)",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)
