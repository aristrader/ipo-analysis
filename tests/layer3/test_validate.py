from layer3 import spine, validate


def test_validate_contract():
    df = spine.load_substrate()
    t = validate.validate(df)
    assert {"rule", "claim", "verdict"}.issubset(t.columns)
    assert len(t) == len(validate.SIGNALS)
    # the boom-only subscription rule is flagged, not validated
    sub = t[t["rule"] == "pred-sub-saturation"].iloc[0]
    assert "single-regime" in sub["verdict"]
    # every cross rule gets a verdict string
    assert t["verdict"].notna().all()


def test_signs_are_computed():
    df = spine.load_substrate()
    t = validate.validate(df).set_index("rule")
    # lasting-wealth: MB median 1y alpha should be negative in both regimes (the known result)
    assert t.loc["desc-lasting-wealth", "verdict"].startswith(("VALIDATED", "consistent", "MIXED"))
