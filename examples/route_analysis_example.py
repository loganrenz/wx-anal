#!/usr/bin/env python
"""
Example: Offshore Route Analysis

This script demonstrates how to use wx-anal to analyze departure windows
for offshore sailing routes, similar to professional weather routing briefings.

Based on the real-world scenario of analyzing departure windows from 
Hampton Roads to Bermuda/Antigua with consideration of cut-off lows,
Gulf Stream routing, and vessel speed differences.
"""

from datetime import datetime, timedelta
from wx_anal import Config, WeatherDownloader, WeatherAnalyzer
from wx_anal.routes import Route, Vessel, GulfStream


def main():
    """Run example route analysis."""
    
    print("="*70)
    print("WX-ANAL: OFFSHORE ROUTE ANALYSIS EXAMPLE")
    print("="*70)
    print()
    
    # Setup
    config = Config(data_dir="./data")
    downloader = WeatherDownloader(config)
    analyzer = WeatherAnalyzer(config)
    
    # Define scenario
    print("📍 SCENARIO:")
    print("  Route: Hampton Roads → Bermuda → Antigua")
    print("  Question: Friday 10/31 afternoon departure vs Wednesday 11/5?")
    print("  Concern: Cut-off low over Louisiana on Sunday 11/2")
    print()
    
    # Create vessel profiles
    print("🚤 VESSEL PROFILES:")
    print()
    
    slow_boat = Vessel.slow_boat("Slow Cruiser")
    typical_boat = Vessel.typical_boat("Typical Cruiser")
    fast_boat = Vessel.fast_boat("Fast Cruiser")
    
    vessels = [slow_boat, typical_boat, fast_boat]
    
    for v in vessels:
        print(f"  {v.name:20s}: {v.avg_speed_knots:.1f} kt, {v.nm_per_day:.0f} nm/day")
    print()
    
    # Analyze routes for each vessel
    print("📊 ROUTE ANALYSIS:")
    print()
    
    departure_date = datetime(2025, 10, 31, 18, 0)
    
    for vessel in vessels:
        # Hampton to Bermuda
        route_hb = Route("hampton-bermuda", vessel=vessel)
        arrival_hb = route_hb.estimate_arrival_time(departure_date)
        duration_hb = arrival_hb - departure_date
        
        # Bermuda to Antigua
        route_ba = Route("bermuda-antigua", vessel=vessel)
        arrival_ba = route_ba.estimate_arrival_time(arrival_hb)
        
        print(f"  {vessel.name}:")
        print(f"    Hampton → Bermuda:  {duration_hb.days}d {duration_hb.seconds//3600}h ({route_hb._calculate_total_distance():.0f} nm)")
        print(f"    Arrival at Bermuda: {arrival_hb.strftime('%a %b %d, %H:%M UTC')}")
        
        # Total to Antigua
        total_duration = arrival_ba - departure_date
        print(f"    Total to Antigua:   {total_duration.days}d {total_duration.seconds//3600}h")
        print()
    
    # Gulf Stream considerations
    print("🌊 GULF STREAM CONSIDERATIONS:")
    print()
    
    gs_rec = GulfStream.get_crossing_recommendation(
        "hampton",
        {"wind_speed": 30}  # Assuming strong winds
    )
    
    print(f"  Recommended crossing: {gs_rec['recommended_crossing_lat']:.1f}°N")
    print(f"  Recommended exit:     {gs_rec['recommended_exit_lat']:.1f}°N")
    
    if gs_rec["avoid_before"]:
        print(f"  ⚠️  Avoid before:      {gs_rec['avoid_before']}")
    
    print()
    print("  Rationale:")
    for item in gs_rec["rationale"]:
        print(f"    • {item}")
    print()
    
    # Key decision points
    print("🎯 KEY DECISION POINTS:")
    print()
    print("  1. Friday 10/31 Afternoon Departure:")
    print("     + Can depart as early as conditions allow")
    print("     + Enter Gulf Stream Saturday morning")
    print("     - High uncertainty about cut-off low evolution")
    print("     - Possible 30-40 kt winds Monday-Wednesday if low reattaches")
    print()
    print("  2. Wednesday 11/5 Departure:")
    print("     + Higher forecast confidence")
    print("     + Past the uncertain weather period")
    print("     - 5-day delay (crew, provisions, etc.)")
    print()
    
    # Weather data download (demonstration)
    print("📡 WEATHER DATA:")
    print()
    print("  Attempting to download NOAA model data...")
    print("  (Note: This requires internet and valid forecast date)")
    print()
    
    try:
        data = downloader.download_offshore_route_data(
            route_name="hampton-bermuda",
            run_date=departure_date,
            forecast_days=10,
        )
        
        if data.get("gfs"):
            print("  ✓ GFS data downloaded")
            
            # Try to detect cut-off low
            cutoff = analyzer.detect_cutoff_low(
                data["gfs"],
                bbox={"lat_min": 25.0, "lat_max": 34.0, "lon_min": -96.0, "lon_max": -88.0}
            )
            
            if cutoff["detected"]:
                print(f"  ⚠️  Cut-off low detected: {len(cutoff['times'])} timesteps")
            else:
                print("  ✓ No significant cut-off low detected")
        
        if data.get("ww3"):
            print("  ✓ WW3 wave data downloaded")
        
        if data.get("gefs"):
            print("  ✓ GEFS ensemble data downloaded")
            
    except Exception as e:
        print(f"  ⚠️  Data download failed: {str(e)[:60]}...")
        print("  This is expected if the forecast date doesn't exist yet.")
    
    print()
    print("="*70)
    print("💡 SUMMARY:")
    print()
    print("This example demonstrates the wx-anal framework for analyzing")
    print("offshore departure windows. In production use:")
    print()
    print("  • Download real NOAA model data (GFS, GEFS, WW3)")
    print("  • Detect meteorological features (cut-off lows, etc.)")
    print("  • Analyze route-specific wind and wave conditions")
    print("  • Generate risk scores and recommendations")
    print("  • Compare different departure times and vessel speeds")
    print()
    print("Run 'wx-anal --help' for CLI usage or see the Jupyter notebook")
    print("in notebooks/offshore_route_analysis.ipynb for interactive analysis.")
    print("="*70)


if __name__ == "__main__":
    main()
