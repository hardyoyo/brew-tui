"""Unit tests for brew-tui calculation engine."""

import pytest
from brew_tui.engine import (
    _to_float,
    calculate_og,
    calculate_mcu,
    calculate_srm_from_mcu,
    calculate_srm,
    calculate_ibu,
    DEFAULT_BASE_MALT_PPG,
)

# ── _to_float guards ──────────────────────────────────────────────


class TestToFloat:
    def test_numeric_string(self):
        assert _to_float("5.0") == 5.0
        assert _to_float("0") == 1.0  # zero → fallback

    def test_none_and_empty(self):
        assert _to_float(None) == 1.0
        assert _to_float("") == 1.0
        assert _to_float("  ") == 1.0

    def test_non_numeric(self):
        assert _to_float("abc") == 1.0
        assert _to_float([1, 2]) == 1.0

    def test_zero_returns_fallback(self):
        assert _to_float(0) == 1.0
        assert _to_float(0.0) == 1.0

    def test_custom_fallback(self):
        assert _to_float(None, fallback=42.0) == 42.0
        assert _to_float("", fallback=0.0) == 0.0
        assert _to_float(0, fallback=0.0) == 0.0

    def test_valid_positive_values(self):
        assert _to_float(20) == 20.0
        assert _to_float("20.5") == 20.5


# ── OG ────────────────────────────────────────────────────────────


class TestCalculateOG:
    def test_single_base_malt(self):
        """5 kg base malt (37 PPG) in 20 L at 75% efficiency."""
        og = calculate_og([5.0], 20.0)
        # gravity points = 5 * 2.20462 * 37 * 0.75 / (20 * 0.264172)
        #               = 5 * 2.20462 * 37 * 0.75 / 5.28344
        #               = 305.89 / 5.28344 = 57.90
        # OG = 1 + 57.90/1000 = 1.0579
        assert og == pytest.approx(1.0579, abs=0.001)

    def test_two_malts(self):
        """4 kg base + 1 kg specialty in 20 L."""
        og = calculate_og(
            [4.0, 1.0],
            20.0,
            potentials_ppg=[DEFAULT_BASE_MALT_PPG, 34.0],
        )
        # base:  4 * 2.20462 * 37 * 0.75 / 5.28344 = 46.32
        # spec:  1 * 2.20462 * 34 * 0.75 / 5.28344 = 10.64
        # total: 56.96 → OG = 1.0570
        assert og == pytest.approx(1.0570, abs=0.001)

    def test_zero_batch_size_guard(self):
        """Batch size of 0 should use fallback 1.0, not crash."""
        og = calculate_og([5.0], 0.0)
        assert isinstance(og, float) and og > 0.0

    def test_empty_string_batch_size(self):
        """Empty batch size string should not crash."""
        og = calculate_og([5.0], "")
        assert og > 1.0

    def test_no_malt(self):
        """No malt should return ~1.000."""
        og = calculate_og([], 20.0)
        assert og == pytest.approx(1.0, abs=0.001)

    def test_100_percent_efficiency(self):
        """100 % efficiency should give higher OG."""
        og = calculate_og([5.0], 20.0, efficiency=1.0)
        # 5 * 2.20462 * 37 * 1.0 / 5.28344 = 77.20 → 1.0772
        assert og == pytest.approx(1.0772, abs=0.001)

    def test_malt_weight_exactly_one_kg(self):
        """1.0 kg malt should not be zeroed by fallback check."""
        og = calculate_og([1.0], 20.0)
        assert og == pytest.approx(1.0116, abs=0.001)


# ── MCU & SRM ─────────────────────────────────────────────────────


class TestCalculateMCU:
    def test_single_malt(self):
        """5 kg malt at 10 L in 20 L batch."""
        mcu = calculate_mcu([5.0], [10.0], 20.0)
        # MCU = (5 * 2.20462 * 10) / (20 * 0.264172)
        #     = 110.231 / 5.28344 = 20.86
        assert mcu == pytest.approx(20.86, abs=0.05)

    def test_zero_malt(self):
        assert calculate_mcu([0.0], [10.0], 20.0) == 0.0

    def test_zero_volume_guard(self):
        """Zero batch volume should use fallback 1.0, not crash."""
        mcu = calculate_mcu([5.0], [10.0], 0.0)
        assert isinstance(mcu, float) and mcu >= 0.0


class TestCalculateSRMFromMCU:
    def test_known_values(self):
        # MCU=1   → SRM ≈ 1.49
        assert calculate_srm_from_mcu(1.0) == pytest.approx(1.49, abs=0.01)
        # MCU=10  → SRM ≈ 7.24
        assert calculate_srm_from_mcu(10.0) == pytest.approx(7.24, abs=0.05)
        # MCU=40  → SRM ≈ 18.74
        assert calculate_srm_from_mcu(40.0) == pytest.approx(18.74, abs=0.1)

    def test_zero_mcu_returns_zero(self):
        assert calculate_srm_from_mcu(0.0) == 0.0
        assert calculate_srm_from_mcu(-1.0) == 0.0
        assert calculate_srm_from_mcu(None) == 0.0

    def test_very_small_mcu(self):
        """MCU very close to zero should still work."""
        assert calculate_srm_from_mcu(0.001) > 0.0


class TestCalculateSRM:
    def test_integration(self):
        """5 kg malt at 10 L in 20 L batch → MCU≈20.86 → SRM≈11.99"""
        srm = calculate_srm([5.0], [10.0], 20.0)
        assert srm == pytest.approx(11.99, abs=0.3)

    def test_empty_ingredients(self):
        assert calculate_srm([], [], 20.0) == 0.0


# ── IBU ───────────────────────────────────────────────────────────


class TestCalculateIBU:
    def test_standard(self):
        """30 g @ 5 % AA, 20 L batch, 24 % utilization → 18 IBU."""
        ibu = calculate_ibu(30.0, 5.0, 20.0)
        # 30 * 0.05 * 0.24 * 1000 / 20 = 18.0
        assert ibu == pytest.approx(18.0, abs=0.1)

    def test_no_hops(self):
        assert calculate_ibu(0.0, 5.0, 20.0) == 0.0

    def test_zero_alpha_acid(self):
        assert calculate_ibu(30.0, 0.0, 20.0) == 0.0

    def test_zero_batch_size_guard(self):
        """Zero batch should not crash."""
        ibu = calculate_ibu(30.0, 5.0, 0.0)
        assert isinstance(ibu, float)
        assert ibu >= 0.0

    def test_empty_string_hop_weight(self):
        ibu = calculate_ibu("", 5.0, 20.0)
        assert ibu == 0.0

    def test_custom_utilization(self):
        """50 % utilization should double IBU."""
        ibu = calculate_ibu(30.0, 5.0, 20.0, utilization=0.50)
        assert ibu == pytest.approx(37.5, abs=0.1)
