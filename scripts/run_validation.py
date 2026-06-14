"""Cross-regime sign-validation report (promotion gate reported -> validated).

Run: PYTHONPATH=. python run_validation.py
"""
from layer3 import spine, validate


def main():
    df = spine.load_substrate()
    t = validate.validate(df)
    print("=" * 100)
    print("CROSS-REGIME VALIDATION — does each rule's directional claim hold SIGN in boom AND longterm?")
    print("(values are the signed signal × 100; a sign flip = a regime effect, not a robust truth)")
    print("=" * 100)
    print(t.to_string(index=False))
    print("\nVALIDATED rules can be promoted reported->validated in rules/index.md. MIXED/insufficient stay 'reported'.")


if __name__ == "__main__":
    main()
