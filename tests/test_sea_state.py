"""Tests for sea state analysis."""

import pytest
from wx_anal.sea_state import SeaStateAnalyzer


def test_heading_relative_wind_head():
    """Test wind analysis with head winds."""
    analyzer = SeaStateAnalyzer()
    
    # Wind from 0° (north), vessel heading 0° (north)
    result = analyzer.analyze_heading_relative_wind(
        wind_speed=15.0,  # m/s (~30 kt)
        wind_direction=0.0,
        vessel_heading=0.0,
        vessel_speed=6.0,
    )
    
    assert result["wind_position"] == "HEAD"
    assert result["relative_angle"] == 0.0
    assert result["comfort_factor"] < 60  # Head winds are uncomfortable


def test_heading_relative_wind_beam():
    """Test wind analysis with beam winds."""
    analyzer = SeaStateAnalyzer()
    
    # Wind from 90° (east), vessel heading 0° (north)
    result = analyzer.analyze_heading_relative_wind(
        wind_speed=15.0,
        wind_direction=90.0,
        vessel_heading=0.0,
        vessel_speed=6.0,
    )
    
    assert result["wind_position"] == "BEAM"
    assert 45 <= result["relative_angle"] <= 135


def test_heading_relative_wind_stern():
    """Test wind analysis with following winds."""
    analyzer = SeaStateAnalyzer()
    
    # Wind from 180° (south), vessel heading 0° (north)
    result = analyzer.analyze_heading_relative_wind(
        wind_speed=15.0,
        wind_direction=180.0,
        vessel_heading=0.0,
        vessel_speed=6.0,
    )
    
    assert result["wind_position"] == "STERN"
    assert result["relative_angle"] == 180.0  # Directly astern (180° off bow)
    # Following winds are more comfortable than head winds, but 30 kt is still notable
    assert result["comfort_factor"] >= 40


def test_heading_relative_waves_basic():
    """Test basic wave analysis."""
    analyzer = SeaStateAnalyzer()
    
    result = analyzer.analyze_heading_relative_waves(
        wave_height=3.0,  # meters
        wave_direction=0.0,
        wave_period=8.0,  # seconds
        vessel_heading=0.0,
        in_gulf_stream=False,
    )
    
    assert result["wave_position"] == "HEAD"
    assert result["wave_height_m"] == 3.0
    assert result["wave_period_s"] == 8.0
    assert "steepness_category" in result


def test_wave_steepness_calculation():
    """Test wave steepness calculation."""
    analyzer = SeaStateAnalyzer()
    
    # Short period steep waves
    steep_result = analyzer.analyze_heading_relative_waves(
        wave_height=3.0,
        wave_direction=0.0,
        wave_period=6.0,  # Short period
        vessel_heading=0.0,
    )
    
    # Long period gentle waves
    gentle_result = analyzer.analyze_heading_relative_waves(
        wave_height=3.0,
        wave_direction=0.0,
        wave_period=12.0,  # Long period
        vessel_heading=0.0,
    )
    
    assert steep_result["steepness"] > gentle_result["steepness"]


def test_gulf_stream_amplification():
    """Test wave amplification in Gulf Stream."""
    analyzer = SeaStateAnalyzer()
    
    # Waves opposing current (wave from east, current to east = opposing)
    result = analyzer.analyze_heading_relative_waves(
        wave_height=3.0,
        wave_direction=90.0,  # Waves FROM east
        wave_period=7.0,
        vessel_heading=0.0,
        in_gulf_stream=True,
        current_speed=2.0,  # 2 kt current
        current_direction=90.0,  # Current TO east (opposing waves FROM east)
    )
    
    # With opposing current, waves should be amplified
    assert result["effective_height_m"] >= result["wave_height_m"]
    assert result["gulf_stream_amplification"] >= 1.0


def test_combined_discomfort_head_seas():
    """Test combined discomfort with head winds and waves."""
    analyzer = SeaStateAnalyzer()
    
    wind_analysis = analyzer.analyze_heading_relative_wind(
        wind_speed=20.0,  # Strong wind
        wind_direction=0.0,
        vessel_heading=0.0,
    )
    
    wave_analysis = analyzer.analyze_heading_relative_waves(
        wave_height=4.0,  # Large waves
        wave_direction=0.0,
        wave_period=6.0,  # Short period
        vessel_heading=0.0,
    )
    
    combined = analyzer.calculate_combined_discomfort(wind_analysis, wave_analysis)
    
    assert combined["combined_discomfort"] > 50
    assert combined["category"] in ["UNCOMFORTABLE", "MISERABLE"]


def test_combined_discomfort_following_seas():
    """Test combined discomfort with following conditions."""
    analyzer = SeaStateAnalyzer()
    
    wind_analysis = analyzer.analyze_heading_relative_wind(
        wind_speed=10.0,  # Moderate wind
        wind_direction=180.0,  # From astern
        vessel_heading=0.0,
    )
    
    wave_analysis = analyzer.analyze_heading_relative_waves(
        wave_height=2.0,  # Moderate waves
        wave_direction=180.0,  # From astern
        wave_period=10.0,  # Long period
        vessel_heading=0.0,
    )
    
    combined = analyzer.calculate_combined_discomfort(wind_analysis, wave_analysis)
    
    # Following seas are more comfortable than head seas, but still some discomfort
    assert combined["combined_discomfort"] < 80  # Less than head seas
    assert combined["category"] in ["COMFORTABLE", "ACCEPTABLE", "UNCOMFORTABLE"]


def test_relative_angle_calculation():
    """Test relative angle calculation."""
    analyzer = SeaStateAnalyzer()
    
    # Test various angles
    # (wind_from, vessel_heading, expected_relative)
    angles = [
        (0.0, 0.0, 0.0),      # Wind from north, heading north = head wind (0°)
        (180.0, 0.0, 180.0),  # Wind from south, heading north = stern wind (180°)
        (90.0, 0.0, 90.0),    # Wind from east, heading north = beam (90°)
        (0.0, 90.0, 90.0),    # Wind from north, heading east = beam (90°)
        (0.0, 180.0, 180.0),  # Wind from north, heading south = stern wind (180°)
    ]
    
    for wind_dir, vessel_hdg, expected_relative in angles:
        result = analyzer._calculate_relative_angle(wind_dir, vessel_hdg)
        assert abs(result - expected_relative) < 1.0, \
            f"Failed for wind={wind_dir}, hdg={vessel_hdg}, got {result}"


def test_wind_assessment_strings():
    """Test that assessment strings are generated."""
    analyzer = SeaStateAnalyzer()
    
    result = analyzer.analyze_heading_relative_wind(
        wind_speed=15.0,
        wind_direction=0.0,
        vessel_heading=0.0,
    )
    
    assert "assessment" in result
    assert len(result["assessment"]) > 0
    assert "kt" in result["assessment"]


def test_wave_assessment_strings():
    """Test that wave assessment strings are generated."""
    analyzer = SeaStateAnalyzer()
    
    result = analyzer.analyze_heading_relative_waves(
        wave_height=3.0,
        wave_direction=0.0,
        wave_period=8.0,
        vessel_heading=0.0,
    )
    
    assert "assessment" in result
    assert len(result["assessment"]) > 0
    assert "ft" in result["assessment"]
