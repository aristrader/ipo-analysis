"""Unit tests for scrapers/delisting.py pure helpers.

Focus: the bse_fail_flags() helper that makes BSE-tier fetch failures
distinguishable from genuine BSE absences in source_flags.

Problem being fixed: when a BSE tier (Active/Suspended/Delisted) fails all retries,
the tier was silently skipped -> affected ISINs got empty source_flags and
status='unknown', indistinguishable from ISINs genuinely absent from BSE.

After the fix: fetch_bse_status() returns failed_tiers, and build() stamps
'bse_fetch_failed:<Tier>' into source_flags for ISINs with no BSE match AND
at least one failed tier.
"""
import importlib.util
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CACHE = {}


def _load(relpath, name):
    if name in _CACHE:
        return _CACHE[name]
    path = os.path.join(ROOT, relpath)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _CACHE[name] = mod
    return mod


@pytest.fixture(scope="session")
def delisting_mod():
    """scrapers/delisting.py — pure helpers."""
    return _load("scrapers/delisting.py", "scr_delisting")


# ── bse_fail_flags ────────────────────────────────────────────────────────────

class TestBseFailFlags:
    def test_empty_set_gives_no_flags(self, delisting_mod):
        assert delisting_mod.bse_fail_flags(set()) == []

    def test_single_failed_tier(self, delisting_mod):
        result = delisting_mod.bse_fail_flags({'Suspended'})
        assert result == ['bse_fetch_failed:Suspended']

    def test_multiple_failed_tiers_are_sorted(self, delisting_mod):
        """Flags must be sorted so source_flags strings are deterministic."""
        result = delisting_mod.bse_fail_flags({'Delisted', 'Active'})
        assert result == ['bse_fetch_failed:Active', 'bse_fetch_failed:Delisted']

    def test_all_three_tiers_failed(self, delisting_mod):
        result = delisting_mod.bse_fail_flags({'Active', 'Suspended', 'Delisted'})
        assert result == [
            'bse_fetch_failed:Active',
            'bse_fetch_failed:Delisted',
            'bse_fetch_failed:Suspended',
        ]

    def test_flags_are_strings(self, delisting_mod):
        for flag in delisting_mod.bse_fail_flags({'Active'}):
            assert isinstance(flag, str)


# ── bse_fail_flags integration with source_flags ─────────────────────────────

class TestBseFailFlagsInSourceFlags:
    """Simulate the build() flag-stamping logic: when bse_failed_tiers is non-empty
    and an ISIN has no BSE match, the fail flags must appear in source_flags."""

    def _run_flag_logic(self, isin_in_bse, bse_failed_tiers, delisting_mod):
        """Minimal simulation of the per-ISIN flag logic in build()."""
        flags = []
        bse_isin = {'INE_FOUND': 'active'} if isin_in_bse else {}
        isin = 'INE_FOUND' if isin_in_bse else 'INE_MISSING'
        code = ''

        # mirrors the build() BSE block
        if isin in bse_isin:
            flags.append('bse_isin:' + bse_isin[isin])
        elif code and code in {}:
            pass
        elif bse_failed_tiers:
            flags.extend(delisting_mod.bse_fail_flags(bse_failed_tiers))

        return flags

    def test_no_match_no_failure_gives_empty_flags(self, delisting_mod):
        flags = self._run_flag_logic(False, set(), delisting_mod)
        assert flags == []

    def test_no_match_with_failure_stamps_fail_flag(self, delisting_mod):
        flags = self._run_flag_logic(False, {'Suspended'}, delisting_mod)
        assert 'bse_fetch_failed:Suspended' in flags

    def test_found_in_bse_does_not_get_fail_flag(self, delisting_mod):
        """An ISIN that was actually found in BSE must NOT get the fail flag."""
        flags = self._run_flag_logic(True, {'Suspended'}, delisting_mod)
        assert all('bse_fetch_failed' not in f for f in flags)
        assert any('bse_isin' in f for f in flags)

    def test_fail_flag_is_distinguishable_from_genuine_absence(self, delisting_mod):
        """The whole point: a failed-tier ISIN and a genuinely-absent ISIN must differ."""
        flags_fail   = self._run_flag_logic(False, {'Delisted'}, delisting_mod)
        flags_absent = self._run_flag_logic(False, set(), delisting_mod)
        assert flags_fail != flags_absent
        assert any('bse_fetch_failed' in f for f in flags_fail)
        assert not any('bse_fetch_failed' in f for f in flags_absent)
