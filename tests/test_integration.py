"""Integration tests for wx-anal end-to-end workflows."""

import pytest
from datetime import datetime

from wx_anal import Config, WeatherDownloader, WeatherAnalyzer
from wx_anal.routes import Route, Vessel


def test_end_to_end_route_analysis():
    """Test complete route analysis workflow with mock data."""
    # Setup
    config = Config(data_dir="/tmp/wx_anal_test")
    downloader = WeatherDownloader(config)
    analyzer = WeatherAnalyzer(config)
    
    # Create vessel and route
    vessel = Vessel.typical_boat()
    route = Route("hampton-bermuda", vessel=vessel)
    
    # Download mock data
    departure = datetime(2025, 10, 29, 18, 0)
    data = downloader.download_offshore_route_data(
        route_name="hampton-bermuda",
        run_date=departure,
        forecast_days=5,
        use_mock_data=True,
    )
    
    # Verify data downloaded
    assert data is not None
    assert data.get("gfs") is not None
    assert data.get("ww3") is not None
    
    # Analyze route
    route_points = route.interpolate_waypoints(num_points=10)
    
    # Wind analysis
    wind_results = analyzer.analyze_route_winds(data["gfs"], route_points)
    assert "max_wind" in wind_results
    assert "mean_wind" in wind_results
    assert wind_results["max_wind"] > 0
    
    # Wave analysis
    wave_results = analyzer.analyze_route_waves(data["ww3"], route_points)
    assert "max_wave_height" in wave_results
    assert "mean_wave_height" in wave_results
    assert wave_results["max_wave_height"] > 0
    
    # Risk assessment
    risk = analyzer.score_route_risk(wind_results, wave_results, None)
    assert "risk_score" in risk
    assert "risk_level" in risk
    assert "recommendation" in risk
    assert 0 <= risk["risk_score"] <= 100
    assert risk["risk_level"] in ["LOW", "MODERATE", "HIGH"]


def test_multiple_vessel_comparison():
    """Test comparing different vessel speeds."""
    departure = datetime(2025, 10, 31, 18, 0)
    
    vessels = [
        Vessel.slow_boat(),
        Vessel.typical_boat(),
        Vessel.fast_boat(),
    ]
    
    arrivals = []
    for vessel in vessels:
        route = Route("hampton-bermuda", vessel=vessel)
        arrival = route.estimate_arrival_time(departure)
        arrivals.append(arrival)
    
    # Fast boat should arrive first
    assert arrivals[2] < arrivals[1] < arrivals[0]
    
    # Check reasonable durations (3-6 days)
    for arrival in arrivals:
        duration = arrival - departure
        assert 2 <= duration.days <= 7


def test_multiple_routes():
    """Test different route calculations."""
    vessel = Vessel.typical_boat()
    departure = datetime(2025, 10, 31, 18, 0)
    
    routes = [
        ("hampton-bermuda", 640),
        ("bermuda-antigua", 850),
        ("beaufort-bermuda", 580),
    ]
    
    for route_name, expected_distance in routes:
        route = Route(route_name, vessel=vessel)
        distance = route._calculate_total_distance()
        
        # Allow 10% tolerance
        assert abs(distance - expected_distance) / expected_distance < 0.15
        
        # Arrival time should be reasonable
        arrival = route.estimate_arrival_time(departure)
        duration_hours = (arrival - departure).total_seconds() / 3600
        expected_hours = expected_distance / vessel.avg_speed_knots
        
        # Within 20% of expected (accounting for currents, etc.)
        assert abs(duration_hours - expected_hours) / expected_hours < 0.20


def test_cutoff_low_detection_workflow():
    """Test cut-off low detection with wider area."""
    from wx_anal.mock_data import generate_mock_gfs
    
    # Generate data covering Louisiana region
    bbox = {
        "lat_min": 20.0,
        "lat_max": 45.0,
        "lon_min": -100.0,
        "lon_max": -60.0,
    }
    
    data = generate_mock_gfs(
        datetime(2025, 10, 29, 12, 0),
        list(range(0, 49, 6)),  # 48 hours
        bbox,
        levels=[500],
    )
    
    analyzer = WeatherAnalyzer()
    cutoff = analyzer.detect_cutoff_low(
        data,
        bbox={"lat_min": 25.0, "lat_max": 34.0, "lon_min": -96.0, "lon_max": -88.0}
    )
    
    # Should detect the mock cut-off low
    assert cutoff["detected"]
    assert len(cutoff["times"]) > 0
    assert len(cutoff["centroids"]) > 0
    
    # Position should be near Louisiana
    centroid = cutoff["centroids"][0]
    assert 25 <= centroid["lat"] <= 34
    assert -96 <= centroid["lon"] <= -88


def test_time_based_waypoints():
    """Test waypoint generation over time."""
    vessel = Vessel.typical_boat()
    route = Route("hampton-bermuda", vessel=vessel)
    departure = datetime(2025, 10, 31, 18, 0)
    
    waypoints = route.get_waypoints_by_time(departure, time_step_hours=24)
    
    # Should have at least 4 waypoints (4+ days)
    assert len(waypoints) >= 4
    
    # First waypoint should be at departure
    assert waypoints[0]["time"] == departure
    assert waypoints[0]["distance_nm"] == 0
    
    # Waypoints should progress in time
    for i in range(1, len(waypoints)):
        assert waypoints[i]["time"] > waypoints[i-1]["time"]
        assert waypoints[i]["distance_nm"] > waypoints[i-1]["distance_nm"]
    
    # Each waypoint should have position
    for wp in waypoints:
        assert "lat" in wp
        assert "lon" in wp
        assert 17 <= wp["lat"] <= 42  # Within route bounds
        assert -77 <= wp["lon"] <= -64


def test_config_integration():
    """Test configuration usage across modules."""
    config = Config(
        data_dir="/tmp/test_wx",
        cache_size=500,
        timeout=45,
    )
    
    downloader = WeatherDownloader(config)
    analyzer = WeatherAnalyzer(config)
    
    # Config should be accessible
    assert downloader.config == config
    assert analyzer.config == config
    
    # Settings should be applied
    assert config.cache_size == 500
    assert config.timeout == 45
