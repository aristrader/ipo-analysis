"""Unit tests for scrapers/corp_actions.py text->ratio_factor parsing.

corp_actions.csv is the ONLY input that tells the price pipeline a split/bonus
happened; ratio_factor feeds adj_factor_after in step 07, which adjusts every
historical price. A wrong factor silently corrupts all adjusted prices for that
security, so the text parsers are pinned here against real NSE subject strings.

Regression cases:
  HINDZINC  — "Bonus - 1:1 And Face Value Split From Rs. 10 To Rs. 2"
               Bonus dash separator was not captured; bf was None -> silently 1.0 -> factor 5.0 (WRONG).
               Correct: bf=2.0, sf=5.0, factor=10.0.
  SHARONBIO — "Bonus 1:1 / Face Value Split From 10/- To Face Value 2/-"
               Split had no Rs/Re prefix; sf was None -> silently 1.0 -> factor 2.0 (WRONG).
               Correct: bf=2.0, sf=5.0, factor=10.0.
"""


# ----------------------------------------------------------------- classify
def test_classify_distinguishes_kinds(corp_actions_mod):
    c = corp_actions_mod.classify
    assert c("Face Value Split From Rs.10 To Rs.2") == "split"
    assert c("Bonus 4:1") == "bonus"
    assert c("Bonus 1:1 And Face Value Split From Rs.10 To Re.1") == "bonus+split"
    assert c("Dividend Rs 5 Per Share") is None
    assert c("") is None
    assert c(None) is None


# ----------------------------------------------------------- parse_split_factor
def test_parse_split_factor_reads_two_face_values(corp_actions_mod):
    f = corp_actions_mod.parse_split_factor
    assert f("Face Value Split From Rs.10 To Rs.2") == 5.0
    assert f("From Rs 10 To Re 1") == 10.0          # Re. variant + spacing
    assert f("Face Value Change From Rs.10 To Rs.5") == 2.0


def test_parse_split_factor_bare_integer_face_values(corp_actions_mod):
    """SHARONBIO regression: '10/- To ... 2/-' has no Rs/Re prefix."""
    f = corp_actions_mod.parse_split_factor
    # SHARONBIO real subject: "Bonus 1:1 / Face Value Split From 10/- To Face Value 2/-"
    assert f("Face Value Split From 10/- To Face Value 2/-") == 5.0
    assert f("From 5/- To 1/-") == 5.0


def test_parse_split_factor_guards(corp_actions_mod):
    f = corp_actions_mod.parse_split_factor
    assert f("Stock Split") is None                 # no face values
    assert f("From Rs 10") is None                  # only one value
    assert f("") is None
    assert f(None) is None


# ----------------------------------------------------------- parse_bonus_factor
def test_parse_bonus_factor_ratio_math(corp_actions_mod):
    f = corp_actions_mod.parse_bonus_factor
    assert f("Bonus 4:1") == 5.0          # 4 new per 1 held -> (4+1)/1
    assert f("Bonus 1:1") == 2.0
    assert f("Bonus 1: 1") == 2.0         # tolerates the space
    assert f("Bonus 3:2") == 2.5


def test_parse_bonus_factor_dash_separator(corp_actions_mod):
    """HINDZINC regression: 'Bonus - 1:1' — optional dash between 'Bonus' and ratio."""
    f = corp_actions_mod.parse_bonus_factor
    assert f("Bonus - 1:1") == 2.0        # HINDZINC real pattern
    assert f("Bonus – 1:1") == 2.0        # en-dash variant


def test_parse_bonus_factor_non_ratio_returns_none(corp_actions_mod):
    f = corp_actions_mod.parse_bonus_factor
    assert f("Bonus Debentures Scheme Of Arrangement") is None
    assert f("") is None
    assert f(None) is None


# ----------------------------------------------------------------- iso_date
def test_iso_date_reformats_and_guards(corp_actions_mod):
    d = corp_actions_mod.iso_date
    assert d("21-Sep-2021") == "2021-09-21"
    assert d("1-Jan-2006") == "2006-01-01"
    assert d("") == ""
    assert d("2021-09-21") == ""          # wrong format -> empty
    assert d("21-Xyz-2021") == ""         # bad month


# ----------------------------------------------------------------- parse_row
def test_parse_row_split(corp_actions_mod):
    row = {"isin": "INE001A01036", "symbol": "ACME",
           "subject": "Face Value Split From Rs.10 To Rs.2", "exDate": "21-Sep-2021"}
    rec = corp_actions_mod.parse_row(row)
    assert rec["action_type"] == "split"
    assert rec["ratio_factor"] == 5.0
    assert rec["ex_date"] == "2021-09-21"
    assert rec["isin"] == "INE001A01036"


def test_parse_row_bonus_plus_split_is_product(corp_actions_mod):
    row = {"isin": "", "symbol": "XYZ",
           "subject": "Bonus 1:1 And Face Value Split From Rs.10 To Re.1",
           "exDate": "01-Jan-2020"}
    rec = corp_actions_mod.parse_row(row)
    assert rec["action_type"] == "bonus+split"
    # bonus (1+1)/1 = 2.0 ; split 10/1 = 10.0 ; product = 20.0
    assert rec["ratio_factor"] == 20.0


def test_parse_row_hindzinc_regression(corp_actions_mod):
    """HINDZINC: 'Bonus - 1:1 And Face Value Split From Rs. 10 To Rs. 2' must give 10.0 not 5.0."""
    row = {"isin": "INE267A01017", "symbol": "HINDZINC",
           "subject": "Bonus - 1:1 And Face Value Split From Rs. 10 To Rs. 2",
           "exDate": "07-Mar-2011"}
    rec = corp_actions_mod.parse_row(row)
    assert rec is not None, "should not be a parse-fail"
    assert rec["action_type"] == "bonus+split"
    # bonus: (1+1)/1 = 2.0; split: 10/2 = 5.0; product = 10.0
    assert rec["ratio_factor"] == 10.0


def test_parse_row_sharonbio_regression(corp_actions_mod):
    """SHARONBIO: '...From 10/- To Face Value 2/-' must give 10.0 not 2.0."""
    row = {"isin": "INE028B01011", "symbol": "SHARONBIO",
           "subject": "Bonus 1:1 / Face Value Split From 10/- To Face Value 2/-",
           "exDate": "20-Feb-2014"}
    rec = corp_actions_mod.parse_row(row)
    assert rec is not None, "should not be a parse-fail"
    assert rec["action_type"] == "bonus+split"
    # bonus: (1+1)/1 = 2.0; split: 10/2 = 5.0; product = 10.0
    assert rec["ratio_factor"] == 10.0


def test_parse_row_bonus_plus_split_none_propagation(corp_actions_mod):
    """If EITHER leg cannot parse, the combined factor must be None (not silent 1.0 multiply)."""
    # A subject that classifies as bonus+split but bonus can't parse -> must return None, not half-factor
    row = {"isin": "", "symbol": "TEST",
           "subject": "Bonus Debentures And Face Value Split From Rs. 10 To Rs. 2",
           "exDate": "01-Jan-2020"}
    # classify sees both keywords -> bonus+split; parse_bonus_factor returns None; must propagate
    rec = corp_actions_mod.parse_row(row)
    assert rec is None, "unparseable bonus leg must not silently substitute 1.0"


def test_parse_row_returns_none_for_non_action(corp_actions_mod):
    assert corp_actions_mod.parse_row({"subject": "Dividend Rs 5", "exDate": "01-Jan-2020"}) is None
