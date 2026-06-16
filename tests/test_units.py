"""Unit tests for brew_tui.units — conversion functions and UnitSystem."""

import pytest
from brew_tui.units import (
    LB_PER_KG,
    OZ_PER_G,
    GAL_PER_L,
    KG_PER_LB,
    G_PER_OZ,
    L_PER_GAL,
    UnitSystem,
    kg_to_lb,
    lb_to_kg,
    g_to_oz,
    oz_to_g,
    l_to_gal,
    gal_to_l,
)


class TestUnitSystem:
    def test_members(self):
        assert UnitSystem.IMPERIAL.value == "imperial"
        assert UnitSystem.METRIC.value == "metric"

    def test_from_string(self):
        assert UnitSystem("imperial") == UnitSystem.IMPERIAL
        assert UnitSystem("metric") == UnitSystem.METRIC

    def test_invalid_string(self):
        with pytest.raises(ValueError):
            UnitSystem("invalid")


class TestConstantsSelfConsistent:
    def assert_reciprocal(self, a: float, b: float) -> None:
        assert a == pytest.approx(1.0 / b, rel=1e-9)

    def test_kg_lb_reciprocal(self):
        self.assert_reciprocal(LB_PER_KG, KG_PER_LB)

    def test_oz_g_reciprocal(self):
        self.assert_reciprocal(OZ_PER_G, G_PER_OZ)

    def test_gal_l_reciprocal(self):
        self.assert_reciprocal(GAL_PER_L, L_PER_GAL)


class TestKgLb:
    @pytest.mark.parametrize(
        ("kg", "expected_lb"),
        [
            (0.0, 0.0),
            (1.0, 2.20462),
            (5.0, 11.0231),
            (10.0, 22.0462),
            (0.453592, 1.0),
        ],
    )
    def test_kg_to_lb(self, kg, expected_lb):
        assert kg_to_lb(kg) == pytest.approx(expected_lb, rel=1e-4)

    @pytest.mark.parametrize(
        ("lb", "expected_kg"),
        [
            (0.0, 0.0),
            (1.0, 0.453592),
            (5.0, 2.26796),
            (11.0, 4.98951),
            (2.20462, 1.0),
        ],
    )
    def test_lb_to_kg(self, lb, expected_kg):
        assert lb_to_kg(lb) == pytest.approx(expected_kg, rel=1e-4)

    def test_round_trip(self):
        for kg in (0.1, 1.0, 5.0, 23.5, 100.0):
            assert kg_to_lb(lb_to_kg(kg_to_lb(kg))) == pytest.approx(
                kg_to_lb(kg), rel=1e-9
            )

    def test_negative(self):
        assert kg_to_lb(-5.0) == pytest.approx(-11.0231, rel=1e-4)
        assert lb_to_kg(-11.0) == pytest.approx(-4.98951, rel=1e-4)


class TestOzG:
    @pytest.mark.parametrize(
        ("g", "expected_oz"),
        [
            (0.0, 0.0),
            (1.0, 0.035274),
            (28.3495, 1.0),
            (100.0, 3.5274),
            (500.0, 17.637),
        ],
    )
    def test_g_to_oz(self, g, expected_oz):
        assert g_to_oz(g) == pytest.approx(expected_oz, rel=1e-4)

    @pytest.mark.parametrize(
        ("oz", "expected_g"),
        [
            (0.0, 0.0),
            (1.0, 28.3495),
            (4.0, 113.398),
            (16.0, 453.592),
        ],
    )
    def test_oz_to_g(self, oz, expected_g):
        assert oz_to_g(oz) == pytest.approx(expected_g, rel=1e-4)

    def test_round_trip(self):
        for g in (0.5, 10.0, 50.0, 1000.0, 5000.0):
            assert g_to_oz(oz_to_g(g_to_oz(g))) == pytest.approx(g_to_oz(g), rel=1e-9)

    def test_negative(self):
        assert g_to_oz(-100.0) == pytest.approx(-3.5274, rel=1e-4)
        assert oz_to_g(-4.0) == pytest.approx(-113.398, rel=1e-3)


class TestGalL:
    @pytest.mark.parametrize(
        ("liters", "expected_gal"),
        [
            (0.0, 0.0),
            (1.0, 0.264172),
            (5.0, 1.32086),
            (18.9271, 5.0),
            (50.0, 13.2086),
        ],
    )
    def test_l_to_gal(self, liters, expected_gal):
        assert l_to_gal(liters) == pytest.approx(expected_gal, rel=1e-4)

    @pytest.mark.parametrize(
        ("gal", "expected_l"),
        [
            (0.0, 0.0),
            (1.0, 3.78541),
            (5.0, 18.9271),
            (15.5, 58.6738),
        ],
    )
    def test_gal_to_l(self, gal, expected_l):
        assert gal_to_l(gal) == pytest.approx(expected_l, rel=1e-4)

    def test_round_trip(self):
        for liters in (0.5, 10.0, 25.4, 100.0, 200.0):
            assert l_to_gal(gal_to_l(l_to_gal(liters))) == pytest.approx(
                l_to_gal(liters), rel=1e-9
            )

    def test_negative(self):
        assert l_to_gal(-10.0) == pytest.approx(-2.64172, rel=1e-4)
        assert gal_to_l(-5.0) == pytest.approx(-18.9271, rel=1e-4)


class TestCrossConversion:
    """Verify that imperial defaults produce sensible metric values."""

    def test_5_gal_in_liters(self):
        assert gal_to_l(5.0) == pytest.approx(18.927, rel=1e-3)

    def test_11_lb_in_kg(self):
        assert lb_to_kg(11.0) == pytest.approx(4.9895, rel=1e-4)

    def test_1_oz_in_g(self):
        assert oz_to_g(1.0) == pytest.approx(28.3495, rel=1e-4)
