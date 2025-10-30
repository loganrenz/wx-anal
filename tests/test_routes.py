"""Tests for route planning module."""

import pytest
from datetime import datetime, timedelta

from wx_anal.routes import Route, Vessel, VesselSpeed, GulfStream


def test_vessel_slow_boat():
    """Test slow boat vessel profile."""
    vessel = Vessel.slow_boat("TestBoat")
    
    assert vessel.name == "TestBoat"
    assert vessel.speed_category == VesselSpeed.SLOW
    assert 5.0 <= vessel.avg_speed_knots <= 5.5
    assert 120 <= vessel.nm_per_day <= 132


def test_vessel_typical_boat():
    """Test typical boat vessel profile."""
    vessel = Vessel.typical_boat()
    
    assert vessel.speed_category == VesselSpeed.TYPICAL
    assert 6.0 <= vessel.avg_speed_knots <= 6.5
    assert 140 <= vessel.nm_per_day <= 165


def test_vessel_fast_boat():
    """Test fast boat vessel profile."""
    vessel = Vessel.fast_boat()
    
    assert vessel.speed_category == VesselSpeed.FAST
    assert 7.0 <= vessel.avg_speed_knots <= 8.5
    assert 168 <= vessel.nm_per_day <= 204


def test_route_predefined():
    """Test creating a predefined route."""
    route = Route("hampton-bermuda")
    
    assert route.name == "hampton-bermuda"
    assert len(route.waypoints) >= 2
    assert hasattr(route, 'distance_nm')


def test_route_custom_waypoints():
    """Test creating a route with custom waypoints."""
    waypoints = [
        (37.0, -76.3),  # Hampton
        (32.3, -64.8),  # Bermuda
    ]
    
    route = Route("custom", waypoints=waypoints)
    
    assert route.name == "custom"
    assert route.waypoints == waypoints


def test_route_unknown():
    """Test error handling for unknown route."""
    with pytest.raises(ValueError, match="Unknown route"):
        Route("nonexistent-route")


def test_route_distance_calculation():
    """Test route distance calculation."""
    waypoints = [
        (37.0, -76.0),
        (32.0, -65.0),
    ]
    
    route = Route("test", waypoints=waypoints)
    distance = route._calculate_total_distance()
    
    # Approximate distance Hampton to Bermuda
    assert 600 < distance < 700


def test_route_interpolate_waypoints():
    """Test waypoint interpolation."""
    waypoints = [
        (37.0, -76.0),
        (32.0, -65.0),
    ]
    
    route = Route("test", waypoints=waypoints)
    interpolated = route.interpolate_waypoints(num_points=10)
    
    assert len(interpolated) == 10
    assert interpolated[0] == waypoints[0]
    assert interpolated[-1] == waypoints[-1]


def test_route_estimate_arrival():
    """Test arrival time estimation."""
    vessel = Vessel.typical_boat()
    route = Route("hampton-bermuda", vessel=vessel)
    
    departure = datetime(2025, 10, 31, 18, 0)
    arrival = route.estimate_arrival_time(departure)
    
    # Should take roughly 4-5 days for typical boat
    duration = arrival - departure
    assert 3 <= duration.days <= 6


def test_route_waypoints_by_time():
    """Test time-based waypoint generation."""
    vessel = Vessel.fast_boat()
    route = Route("hampton-bermuda", vessel=vessel)
    
    departure = datetime(2025, 10, 31, 18, 0)
    timed_wps = route.get_waypoints_by_time(departure, time_step_hours=24)
    
    assert len(timed_wps) > 0
    assert timed_wps[0]["time"] == departure
    assert all("lat" in wp for wp in timed_wps)
    assert all("lon" in wp for wp in timed_wps)
    assert all("distance_nm" in wp for wp in timed_wps)


def test_haversine_distance():
    """Test haversine distance calculation."""
    # Hampton to Bermuda approximately
    lat1, lon1 = 37.0, -76.3
    lat2, lon2 = 32.3, -64.8
    
    distance = Route._haversine_distance(lat1, lon1, lat2, lon2)
    
    # Should be around 640 nm
    assert 600 < distance < 700


def test_gulfstream_crossing_recommendation():
    """Test Gulf Stream crossing recommendations."""
    rec = GulfStream.get_crossing_recommendation(
        "hampton",
        {"wind_speed": 30}  # Strong winds
    )
    
    assert rec["recommended_crossing_lat"] is not None
    assert rec["recommended_exit_lat"] is not None
    assert len(rec["rationale"]) > 0


def test_gulfstream_current_benefit():
    """Test Gulf Stream current benefit estimation."""
    # Route crossing Gulf Stream
    route_points = [
        (37.0, -76.0),
        (36.0, -73.0),  # In Gulf Stream
        (35.0, -70.0),
    ]
    
    benefit = GulfStream.estimate_current_benefit(route_points)
    
    # Should have some positive benefit
    assert benefit > 0


def test_vessel_speed_properties():
    """Test vessel speed calculations."""
    vessel = Vessel(
        name="Test",
        speed_category=VesselSpeed.TYPICAL,
        avg_speed_knots=6.5,
    )
    
    assert vessel.nm_per_day == 6.5 * 24
    assert vessel.nm_per_day == 156
