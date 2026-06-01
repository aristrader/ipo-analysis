"""Score a NEW IPO against historical analogs — Layer 3 Part B (CLI).

Examples:
  PYTHONPATH=. python predict_ipo.py --type MB --sector Finance --mcap mid \
      --ofs_pct 0.6 --sub_total_x 12 --pe 28 --profitable 1 --roe 18 --de 0.4 --issue_size 1200
  PYTHONPATH=. python predict_ipo.py --type SME --sector Manufacturing --mcap micro --profile conservative

The engine (layer3.predictor.predict.predict) is UI-agnostic — the deferred Streamlit app
(TODO) can call it directly with the same query dict.
"""
import argparse
from layer3.predictor.predict import predict, format_text


def build_query(a):
    q = {"type": a.type, "name": a.name}
    if a.sector: q["broad_sector"] = a.sector
    if a.mcap: q["market_cap_class"] = a.mcap
    for key, val in [("ofs_pct", a.ofs_pct), ("sub_total_x", a.sub_total_x), ("sub_qib_x", a.sub_qib_x),
                     ("gmp_pct", a.gmp_pct), ("pe_ratio", a.pe), ("issue_size_cr", a.issue_size),
                     ("pre_ipo_roe_pct", a.roe), ("pre_ipo_debt_equity", a.de),
                     ("pre_ipo_pat_margin_pct", a.margin), ("promoter_post_issue_pct", a.promoter_post),
                     ("pre_ipo_net_sales", a.revenue)]:
        if val is not None:
            q[key] = val
    if a.lead_manager:
        q["lead_manager"] = a.lead_manager
    if a.profitable is not None:
        q["pre_ipo_pat"] = 1.0 if a.profitable else -1.0   # sign is what quality() uses
    return q


def main():
    p = argparse.ArgumentParser(description="Score a new IPO vs historical analogs (Layer 3 Part B).")
    p.add_argument("--type", required=True, choices=["MB", "SME"])
    p.add_argument("--name", default="New IPO")
    p.add_argument("--sector"); p.add_argument("--mcap", choices=["micro", "small", "mid", "large"])
    p.add_argument("--ofs_pct", type=float); p.add_argument("--sub_total_x", type=float)
    p.add_argument("--sub_qib_x", type=float); p.add_argument("--gmp_pct", type=float)
    p.add_argument("--pe", type=float); p.add_argument("--issue_size", type=float, help="₹ cr")
    p.add_argument("--roe", type=float); p.add_argument("--de", type=float)
    p.add_argument("--margin", type=float); p.add_argument("--promoter_post", type=float)
    p.add_argument("--revenue", type=float, help="pre-IPO annual sales ₹cr (<25 = wipeout red flag)")
    p.add_argument("--lead_manager", help="lead manager name (obscure = wipeout red flag)")
    p.add_argument("--profitable", type=int, choices=[0, 1])
    p.add_argument("--profile", default="balanced",
                   choices=["balanced", "conservative", "aggressive", "data_informed"])
    a = p.parse_args()
    print(format_text(predict(build_query(a), profile=a.profile)))


if __name__ == "__main__":
    main()
