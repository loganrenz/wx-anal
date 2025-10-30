#!/usr/bin/env python
"""
Demonstrate enhanced weather analysis with new features.

This script shows the new forecast confidence, sea state analysis,
and route variant capabilities with mock data.
"""

import sys
from datetime import datetime, timedelta
from wx_anal import (
    Config, WeatherDownloader, WeatherAnalyzer,
    SeaStateAnalyzer, ForecastConfidence, RouteVariant
)
from wx_anal.routes import Route, Vessel
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def generate_demo_report():
    """Generate demonstration report with enhanced features."""
    
    print("\n" + "="*70)
    print("ENHANCED MARINE WEATHER ANALYSIS DEMONSTRATION")
    print("="*70)
    print()
    
    # Initialize
    config = Config(data_dir="./data")
    downloader = WeatherDownloader(config)
    analyzer = WeatherAnalyzer(config)
    sea_state = SeaStateAnalyzer()
    forecast_conf = ForecastConfidence()
    
    # Setup scenario
    departure_date = datetime(2025, 10, 31, 18, 0)
    print(f"Scenario: Hampton Roads to Bermuda departure on {departure_date.strftime('%Y-%m-%d %H:%M UTC')}")
    print()
    
    # =====================================================================
    # PART 1: FORECAST CONFIDENCE ANALYSIS
    # =====================================================================
    print("="*70)
    print("PART 1: FORECAST CONFIDENCE ANALYSIS")
    print("="*70)
    print()
    print("Analyzing consistency across 10 recent GFS model runs...")
    print()
    
    # Simulate multi-run results (in real use, this comes from generate_multi_run_report.py)
    multi_run_results = [
        {"success": True, "cutoff_detected": True},   # Run 1 (latest)
        {"success": True, "cutoff_detected": True},   # Run 2
        {"success": True, "cutoff_detected": False},  # Run 3
        {"success": True, "cutoff_detected": True},   # Run 4
        {"success": True, "cutoff_detected": True},   # Run 5
        {"success": True, "cutoff_detected": False},  # Run 6
        {"success": True, "cutoff_detected": True},   # Run 7
        {"success": True, "cutoff_detected": True},   # Run 8
        {"success": True, "cutoff_detected": True},   # Run 9
        {"success": True, "cutoff_detected": True},   # Run 10 (oldest)
    ]
    
    confidence = forecast_conf.analyze_cutoff_consistency(multi_run_results)
    
    print("FORECAST CONFIDENCE RESULTS:")
    print("-" * 70)
    print(f"  Runs Analyzed:        {confidence['runs_analyzed']}")
    print(f"  Runs with Cut-off:    {confidence['runs_with_cutoff']} ({confidence['detection_rate']:.0%})")
    print(f"  Flip-flops:           {confidence['flip_flops']}")
    print(f"  Recent Trend:         {confidence['recent_trend']}")
    print(f"  Confidence Level:     {confidence['confidence_level']}")
    print(f"  Confidence Score:     {confidence['confidence_score']:.0f}/100")
    print()
    
    conf_message = forecast_conf.get_confidence_message(confidence)
    print("INTERPRETATION:")
    print(f"  {conf_message}")
    print()
    
    # =====================================================================
    # PART 2: SEA STATE ANALYSIS (Heading-Relative)
    # =====================================================================
    print("="*70)
    print("PART 2: SEA STATE ANALYSIS (Heading-Relative)")
    print("="*70)
    print()
    print("Analyzing wind and wave conditions relative to vessel heading...")
    print()
    
    # Example scenario: vessel heading 090° (east), conditions from various angles
    scenarios = [
        {
            "name": "Head Winds & Seas",
            "wind_speed": 15.0,      # m/s (30 kt)
            "wind_direction": 90.0,   # FROM east
            "wave_height": 3.0,       # meters
            "wave_direction": 90.0,
            "wave_period": 7.0,       # seconds
            "vessel_heading": 90.0,   # TO east
            "in_gulf_stream": True,
        },
        {
            "name": "Beam Winds & Seas",
            "wind_speed": 15.0,
            "wind_direction": 0.0,    # FROM north
            "wave_height": 3.0,
            "wave_direction": 0.0,
            "wave_period": 9.0,
            "vessel_heading": 90.0,   # TO east
            "in_gulf_stream": False,
        },
        {
            "name": "Following Winds & Seas",
            "wind_speed": 15.0,
            "wind_direction": 270.0,  # FROM west
            "wave_height": 3.0,
            "wave_direction": 270.0,
            "wave_period": 11.0,
            "vessel_heading": 90.0,   # TO east
            "in_gulf_stream": False,
        },
    ]
    
    for scenario in scenarios:
        print(f"Scenario: {scenario['name']}")
        print("-" * 70)
        
        wind_analysis = sea_state.analyze_heading_relative_wind(
            wind_speed=scenario['wind_speed'],
            wind_direction=scenario['wind_direction'],
            vessel_heading=scenario['vessel_heading'],
            vessel_speed=6.0,
        )
        
        wave_analysis = sea_state.analyze_heading_relative_waves(
            wave_height=scenario['wave_height'],
            wave_direction=scenario['wave_direction'],
            wave_period=scenario['wave_period'],
            vessel_heading=scenario['vessel_heading'],
            in_gulf_stream=scenario['in_gulf_stream'],
            current_speed=2.0 if scenario['in_gulf_stream'] else 0.0,
            current_direction=90.0 if scenario['in_gulf_stream'] else 0.0,
        )
        
        discomfort = sea_state.calculate_combined_discomfort(wind_analysis, wave_analysis)
        
        print(f"  Wind: {wind_analysis['assessment']}")
        print(f"    Position: {wind_analysis['wind_position']}, Comfort: {wind_analysis['comfort_factor']:.0f}/100")
        print(f"  Waves: {wave_analysis['assessment']}")
        print(f"    Position: {wave_analysis['wave_position']}, Steepness: {wave_analysis['steepness_category']}")
        if scenario['in_gulf_stream']:
            print(f"    Gulf Stream Amplification: {wave_analysis['gulf_stream_amplification']:.2f}x")
        print(f"  Combined Discomfort: {discomfort['combined_discomfort']:.0f}/100 - {discomfort['category']}")
        print(f"    {discomfort['description']}")
        print()
    
    # =====================================================================
    # PART 3: ROUTE VARIANTS
    # =====================================================================
    print("="*70)
    print("PART 3: ROUTE VARIANTS (Tactical Options)")
    print("="*70)
    print()
    print("Generating route alternatives for Hampton to Bermuda...")
    print()
    
    vessel = Vessel.typical_boat()
    variants = RouteVariant.create_variants("hampton-bermuda", vessel)
    
    print(f"Available Variants: {len(variants)}")
    print("-" * 70)
    for variant in variants:
        print(f"  {variant.variant_name.upper()}")
        print(f"    Waypoints: {len(variant.waypoints)}")
        print(f"    Distance:  {variant.get_distance():.0f} nm")
        print(f"    First waypoint: {variant.waypoints[0]}")
        if len(variant.waypoints) > 2:
            print(f"    Via: {variant.waypoints[1:-1]}")
        print(f"    Last waypoint:  {variant.waypoints[-1]}")
        print()
    
    # =====================================================================
    # PART 4: ENHANCED RISK SCORING
    # =====================================================================
    print("="*70)
    print("PART 4: ENHANCED RISK SCORING (All Vessel Classes)")
    print("="*70)
    print()
    print("Calculating risk with mock route data...")
    print()
    
    # Use mock data for demonstration
    data = downloader.download_offshore_route_data(
        route_name="hampton-bermuda",
        run_date=departure_date,
        forecast_days=7,
        use_mock_data=True,
    )
    
    route = Route("hampton-bermuda", vessel=vessel)
    route_points = route.interpolate_waypoints(num_points=20)
    
    # Basic analysis
    wind_results = analyzer.analyze_route_winds(data["gfs"], route_points)
    wave_results = analyzer.analyze_route_waves(data["ww3"], route_points)
    cutoff_results = analyzer.detect_cutoff_low(
        data["gfs"],
        bbox={"lat_min": 25.0, "lat_max": 34.0, "lon_min": -96.0, "lon_max": -88.0}
    )
    
    # Compare across vessel types
    vessel_types = [
        ("slow", Vessel.slow_boat()),
        ("typical", Vessel.typical_boat()),
        ("fast", Vessel.fast_boat()),
    ]
    
    print("Risk Assessment by Vessel Class:")
    print("-" * 70)
    
    risks = {}
    for vessel_name, vessel_obj in vessel_types:
        enhanced_risk = analyzer.score_route_risk_enhanced(
            wind_results=wind_results,
            wave_results=wave_results,
            cutoff_results=cutoff_results,
            confidence_results=confidence,
            vessel_name=vessel_name,
        )
        risks[vessel_name] = enhanced_risk
        
        print(f"\n{vessel_name.upper()} BOATS ({vessel_obj.avg_speed_knots:.1f} kt avg)")
        print(f"  Base Risk:          {enhanced_risk['base_risk']:.0f}/100")
        print(f"  Adjusted Risk:      {enhanced_risk['risk_score']:.0f}/100")
        print(f"  Risk Level:         {enhanced_risk['risk_level']}")
        print(f"  Risk Factors:")
        for factor in enhanced_risk['risk_factors']:
            print(f"    - {factor}")
        print(f"  Recommendation:")
        # Wrap long recommendations
        rec_lines = enhanced_risk['recommendation'].split('. ')
        for line in rec_lines:
            if line:
                print(f"    {line.strip()}.")
    
    print()
    
    # =====================================================================
    # PART 5: VESSEL COMPARISON SUMMARY
    # =====================================================================
    print("="*70)
    print("PART 5: VESSEL-SPECIFIC GUIDANCE SUMMARY")
    print("="*70)
    print()
    
    vessel_recs = forecast_conf.compare_vessel_risks(
        slow_risk=risks['slow'],
        typical_risk=risks['typical'],
        fast_risk=risks['fast'],
    )
    
    print("Comparative Analysis:")
    print("-" * 70)
    print(f"\nSummary: {vessel_recs['summary']}")
    print()
    for vessel_type in ['slow', 'typical', 'fast']:
        print(f"{vessel_type.upper()}: {vessel_recs[vessel_type]}")
        print()
    
    # =====================================================================
    # SUMMARY
    # =====================================================================
    print("="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print()
    print("Key Takeaways:")
    print(f"  - Forecast confidence: {confidence['confidence_level']} ({confidence['confidence_score']:.0f}/100)")
    print(f"  - Cut-off low detection rate: {confidence['detection_rate']:.0%}")
    print(f"  - Model flip-flops: {confidence['flip_flops']}")
    print(f"  - Risk varies by vessel: Slow={risks['slow']['risk_score']:.0f}, Typical={risks['typical']['risk_score']:.0f}, Fast={risks['fast']['risk_score']:.0f}")
    print(f"  - Route variants available: {len(variants)} tactical options")
    print()
    print("This demonstrates the enhanced capabilities:")
    print("  ✓ Forecast confidence assessment")
    print("  ✓ Heading-relative wind/wave comfort")
    print("  ✓ Wave steepness and Gulf Stream effects")
    print("  ✓ Tactical route alternatives")
    print("  ✓ Vessel-specific recommendations")
    print()
    
    # Save JSON output for web viewer
    output_data = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "scenario": {
            "route": "hampton-bermuda",
            "departure": departure_date.isoformat() + "Z",
        },
        "forecast_confidence": confidence,
        "sea_state_scenarios": [
            {
                "name": s["name"],
                "wind": sea_state.analyze_heading_relative_wind(
                    s['wind_speed'], s['wind_direction'], s['vessel_heading'], 6.0
                ),
                "wave": sea_state.analyze_heading_relative_waves(
                    s['wave_height'], s['wave_direction'], s['wave_period'],
                    s['vessel_heading'], s['in_gulf_stream'], 
                    2.0 if s['in_gulf_stream'] else 0.0, 90.0
                ),
            }
            for s in scenarios
        ],
        "route_variants": [
            {
                "name": v.variant_name,
                "waypoints": v.waypoints,
                "distance_nm": v.get_distance(),
            }
            for v in variants
        ],
        "risk_by_vessel": risks,
        "vessel_recommendations": vessel_recs,
    }
    
    with open("demo_analysis_output.json", "w") as f:
        json.dump(output_data, f, indent=2, default=str)
    
    print("Output saved to: demo_analysis_output.json")
    print()


if __name__ == "__main__":
    try:
        generate_demo_report()
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
