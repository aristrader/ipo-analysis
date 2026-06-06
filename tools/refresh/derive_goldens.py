"""Re-derive the golden headline numbers and overwrite the accepted JSON,
printing OLD -> NEW for every changed key. Called by run_refresh.py --apply;
also runnable standalone after any deliberate substrate change.

    PYTHONPATH=. .venv/bin/python tools/refresh/derive_goldens.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from layer3 import goldens


def main():
    new = goldens.compute()
    try:
        old = goldens.load_accepted()
    except Exception:
        old = {}
    changed = 0
    for k, v in new.items():
        o = old.get(k)
        if o is None or (isinstance(v, float) and abs(v - o) > 1e-12) or (isinstance(v, int) and v != o):
            print(f"  {k:34s} {o!s:>12} -> {v}")
            changed += 1
    goldens.save_accepted(new)
    print(f"goldens: {changed} value(s) changed; accepted file rewritten.")


if __name__ == "__main__":
    main()
