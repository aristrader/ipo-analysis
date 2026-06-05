"""Session-scoped fixtures for the data-integrity suite.

All frames are read with dtype=str (no pandas type inference surprises); tests
coerce per-column via pd.to_numeric. NOTE: the substrate has a column literally
named `isin`, which shadows DataFrame.isin — always use df["isin"], never df.isin.
"""
import os

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _read(rel):
    return pd.read_csv(os.path.join(ROOT, rel), dtype=str)


@pytest.fixture(scope="session")
def ipo():
    return _read("data/master/ipo_analysis.csv")


@pytest.fixture(scope="session")
def universe():
    return _read("data/master/universe.csv")


@pytest.fixture(scope="session")
def returns_summary():
    return _read("data/master/returns_summary.csv")


def num(df, col):
    return pd.to_numeric(df[col], errors="coerce")


def offenders(df, mask, k=5):
    """First k offending isins, for failure messages."""
    return df.loc[mask, "isin"].head(k).tolist()
