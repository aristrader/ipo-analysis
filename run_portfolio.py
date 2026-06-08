"""Paper-portfolio sim CLI — ₹1L into every APPLY call vs ₹1L into Nifty.
Usage: PYTHONPATH=. python run_portfolio.py [--stock INE...]
  (no args)      portfolio summary split by mode + lens
  --stock ISIN   per-stock growth-of-₹1L (3 series) head/tail
"""
import argparse
from layer3 import portfolio as P


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stock", default=None, help="per-stock growth-of-1L for an ISIN")
    a = ap.parse_args()
    if a.stock:
        g = P.growth_of_1l(a.stock)
        if g is None or g.empty:
            print(f"no usable price/issue data for {a.stock}")
            return
        end = g.sort_values("date").groupby("series").tail(1)
        print(f"growth of ₹1L in {a.stock} (to latest):")
        for _, r in end.iterrows():
            print(f"  {r['series']:24s} ₹{r['value']:,.0f}")
        return
    pos = P.simulate()
    s = P.summary(pos)
    print(f"APPLY positions: {len(pos)}\n")
    print(f"{'segment':28s} {'n':>4} {'mult':>7} {'nifty':>7} {'win':>5}")
    for k, v in sorted(s.items()):
        nif = f"{v['nifty_mult']:.2f}x" if v['nifty_mult'] else "  -"
        print(f"  {k:26s} {v['n']:>4} {v['mult']:>6.2f}x {nif:>7} {100*v['win_rate']:>4.0f}%")
    print("\nallottee lens carries the 3.5% allotment haircut (most capital sits in cash — "
          "realistic for the retail lottery); secondary lens = pick quality if you could deploy.")


if __name__ == "__main__":
    main()
