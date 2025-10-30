"""Tests for route variants functionality."""

import pytest
from wx_anal.routes import Route, RouteVariant, Vessel


def test_create_variants_hampton_bermuda():
    """Test creating route variants for Hampton-Bermuda."""
    vessel = Vessel.typical_boat()
    variants = RouteVariant.create_variants("hampton-bermuda", vessel)
    
    assert len(variants) >= 3  # direct, northern, southern
    
    variant_names = [v.variant_name for v in variants]
    assert "direct" in variant_names
    assert "northern" in variant_names
    assert "southern" in variant_names
    
    # Check that each variant has waypoints
    for variant in variants:
        assert len(variant.waypoints) >= 2
        assert variant.vessel == vessel


def test_create_variants_hampton_antigua():
    """Test creating route variants for Hampton-Antigua."""
    vessel = Vessel.fast_boat()
    variants = RouteVariant.create_variants("hampton-antigua", vessel)
    
    assert len(variants) >= 2  # direct, via_bermuda
    
    variant_names = [v.variant_name for v in variants]
    assert "direct" in variant_names
    assert "via_bermuda" in variant_names


def test_variant_waypoints_differ():
    """Test that variants have different waypoints."""
    variants = RouteVariant.create_variants("hampton-bermuda")
    
    direct = next(v for v in variants if v.variant_name == "direct")
    northern = next(v for v in variants if v.variant_name == "northern")
    southern = next(v for v in variants if v.variant_name == "southern")
    
    # Northern and southern should have more waypoints than direct
    assert len(northern.waypoints) >= len(direct.waypoints)
    assert len(southern.waypoints) >= len(direct.waypoints)
    
    # Waypoints should differ
    assert northern.waypoints != direct.waypoints
    assert southern.waypoints != direct.waypoints


def test_northern_variant_goes_north():
    """Test that northern variant actually goes north."""
    variants = RouteVariant.create_variants("hampton-bermuda")
    
    direct = next(v for v in variants if v.variant_name == "direct")
    northern = next(v for v in variants if v.variant_name == "northern")
    
    # Northern variant should have a waypoint with higher latitude
    max_lat_direct = max(wp[0] for wp in direct.waypoints)
    max_lat_northern = max(wp[0] for wp in northern.waypoints)
    
    assert max_lat_northern >= max_lat_direct


def test_southern_variant_goes_south():
    """Test that southern variant actually goes south initially."""
    variants = RouteVariant.create_variants("hampton-bermuda")
    
    direct = next(v for v in variants if v.variant_name == "direct")
    southern = next(v for v in variants if v.variant_name == "southern")
    
    # Get start points
    start_lat_direct = direct.waypoints[0][0]
    
    # Southern variant should have an intermediate waypoint south of start
    if len(southern.waypoints) >= 2:
        intermediate_lat = southern.waypoints[1][0]
        assert intermediate_lat < start_lat_direct


def test_via_bermuda_includes_bermuda():
    """Test that via_bermuda variant includes Bermuda waypoint."""
    variants = RouteVariant.create_variants("hampton-antigua")
    
    via_bermuda = next((v for v in variants if v.variant_name == "via_bermuda"), None)
    
    if via_bermuda:
        # Check that Bermuda coordinates are in waypoints (roughly)
        bermuda_lat, bermuda_lon = 32.3, -64.8
        
        has_bermuda = any(
            abs(wp[0] - bermuda_lat) < 1.0 and abs(wp[1] - bermuda_lon) < 1.0
            for wp in via_bermuda.waypoints
        )
        
        assert has_bermuda


def test_recommend_best_variant():
    """Test variant recommendation (placeholder)."""
    variants = RouteVariant.create_variants("hampton-bermuda")
    
    # Dummy forecast data
    wind_forecasts = {}
    wave_forecasts = {}
    
    recommendation = RouteVariant.recommend_best_variant(
        variants, wind_forecasts, wave_forecasts
    )
    
    assert "recommended_variant" in recommendation
    assert "rationale" in recommendation
    assert "alternatives" in recommendation


def test_create_variants_unknown_route():
    """Test error handling for unknown route."""
    with pytest.raises(ValueError, match="Unknown route"):
        RouteVariant.create_variants("unknown-route")


def test_variant_has_vessel():
    """Test that variants inherit vessel from parameter."""
    vessel = Vessel.slow_boat("TestBoat")
    variants = RouteVariant.create_variants("hampton-bermuda", vessel)
    
    for variant in variants:
        assert variant.vessel == vessel
        assert variant.vessel.name == "TestBoat"


def test_variant_can_calculate_distance():
    """Test that variants can calculate their distance."""
    variants = RouteVariant.create_variants("hampton-bermuda")
    
    for variant in variants:
        distance = variant.get_distance()
        assert distance > 0
        assert distance < 2000  # Reasonable for this route
