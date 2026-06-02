"""Unit tests for scrapers/corp_actions.py text->ratio_factor parsing.

corp_actions.csv is the ONLY input that tells the price pipeline a split/bonus
happened; ratio_factor feeds adj_factor_after in step 07, which adjusts every
historical price. A wrong factor silently corrupts all adjusted prices for that
security, so the text parsers are pinned here against real NSE subject strings.
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


def test_parse_row_returns_none_for_non_action(corp_actions_mod):
    assert corp_actions_mod.parse_row({"subject": "Dividend Rs 5", "exDate": "01-Jan-2020"}) is None
