#!/usr/bin/env python
"""
Generate comprehensive weather analysis report using real NOAA data.

This script downloads the latest available GFS, GEFS, and WW3 data and
generates a detailed markdown report for offshore route planning.
"""

import sys
from datetime import datetime, timedelta
from wx_anal import Config, WeatherDownloader, WeatherAnalyzer
from wx_anal.routes import Route, Vessel, GulfStream
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def generate_report():
    """Generate comprehensive weather report."""
    
    report = []
    report.append("# Offshore Weather Analysis Report")
    report.append("")
    report.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    report.append("")
    report.append("---")
    report.append("")
    
    # Initialize
    config = Config(data_dir="./data")
    downloader = WeatherDownloader(config)
    analyzer = WeatherAnalyzer(config)
    
    # Determine latest available data
    report.append("## Data Sources")
    report.append("")
    
    latest_run = downloader.get_latest_run('gfs')
    report.append(f"**Latest GFS Run:** {latest_run.strftime('%Y-%m-%d %H:%M UTC')}")
    
    # Try to download real data with fallback
    print("\n" + "="*60)
    print("DOWNLOADING WEATHER DATA FROM NOAA")
    print("="*60)
    
    # Test different run times (NOAA has delays)
    test_times = [
        latest_run - timedelta(hours=6),
        latest_run - timedelta(hours=12),
        latest_run - timedelta(hours=18),
    ]
    
    data = None
    run_date = None
    
    for test_time in test_times:
        try:
            logger.info(f"Attempting to download data from {test_time}")
            data = downloader.download_offshore_route_data(
                route_name="hampton-bermuda",
                run_date=test_time,
                forecast_days=7,
                use_mock_data=False,
            )
            
            if data.get("gfs") is not None:
                run_date = test_time
                logger.info(f"✓ Successfully downloaded data from {test_time}")
                break
                
        except Exception as e:
            logger.warning(f"Failed to download from {test_time}: {str(e)[:100]}")
            continue
    
    if data is None or data.get("gfs") is None:
        logger.warning("Could not download real data, using mock data for demonstration")
        run_date = latest_run
        data = downloader.download_offshore_route_data(
            route_name="hampton-bermuda",
            run_date=run_date,
            forecast_days=7,
            use_mock_data=True,
        )
        report.append("")
        report.append("⚠️ **Note:** Using synthetic data for demonstration (real data unavailable)")
    else:
        report.append("")
        report.append("✓ **Status:** Using real NOAA model data")
    
    report.append("")
    report.append(f"**Model Run:** {run_date.strftime('%Y-%m-%d %H:%M UTC')}")
    report.append(f"**Forecast Period:** 7 days")
    report.append("")
    
    if data.get("gfs"):
        gfs = data["gfs"]
        report.append(f"- **GFS Data:** {len(gfs.time)} time steps, {len(gfs.lev)} pressure levels")
    if data.get("ww3"):
        ww3 = data["ww3"]
        report.append(f"- **WW3 Data:** {len(ww3.time)} time steps")
    
    report.append("")
    report.append("---")
    report.append("")
    
    # Analyze multiple scenarios
    print("\n" + "="*60)
    print("ANALYZING ROUTES AND CONDITIONS")
    print("="*60)
    
    # Scenario 1: Hampton to Bermuda
    report.append("## Route Analysis: Hampton Roads → Bermuda")
    report.append("")
    
    vessels = [
        ("Slow Cruiser", Vessel.slow_boat()),
        ("Typical Cruiser", Vessel.typical_boat()),
        ("Fast Cruiser", Vessel.fast_boat()),
    ]
    
    departure_date = run_date + timedelta(hours=6)  # 6 hours after model run
    
    report.append(f"**Departure:** {departure_date.strftime('%A, %B %d, %Y at %H:%M UTC')}")
    report.append("")
    
    for vessel_name, vessel in vessels:
        route = Route("hampton-bermuda", vessel=vessel)
        arrival = route.estimate_arrival_time(departure_date)
        duration = arrival - departure_date
        
        report.append(f"### {vessel_name}")
        report.append("")
        report.append(f"- **Speed:** {vessel.avg_speed_knots:.1f} kt ({vessel.nm_per_day:.0f} nm/day)")
        report.append(f"- **Distance:** {route._calculate_total_distance():.0f} nm")
        report.append(f"- **Duration:** {duration.days}d {duration.seconds // 3600}h")
        report.append(f"- **Arrival:** {arrival.strftime('%A, %B %d at %H:%M UTC')}")
        report.append("")
    
    report.append("---")
    report.append("")
    
    # Weather Feature Detection
    report.append("## Weather Feature Detection")
    report.append("")
    
    report.append("### Chris Parker's Forecast Scenario Analysis")
    report.append("")
    report.append("**Reference:** Marine weather briefing for Hampton → Bermuda/Antigua departures")
    report.append("")
    report.append("**Key Forecast Question:**")
    report.append(">  *Will an upper-level low get cut off from the main flow over Louisiana on Sunday 11/2,*")
    report.append(">  *and if so, will it reattach to the progressive upper-level flow and shift off the US East Coast,*")
    report.append(">  *creating nasty weather throughout the southwest North Atlantic around Tuesday-Wednesday (11/3-11/5)?*")
    report.append("")
    report.append("---")
    report.append("")
    
    if data.get("gfs"):
        print("\nDetecting cut-off lows...")
        cutoff = analyzer.detect_cutoff_low(
            data["gfs"],
            bbox={"lat_min": 25.0, "lat_max": 34.0, "lon_min": -96.0, "lon_max": -88.0}
        )
        
        report.append("### Cut-off Low Analysis (Louisiana Region)")
        report.append("")
        report.append("**Target Area:** 25-34°N, 88-96°W (Louisiana and vicinity)")
        report.append("")
        report.append(f"**Analysis Date:** {run_date.strftime('%Y-%m-%d %H:%M UTC')}")
        report.append("")
        
        if cutoff["detected"]:
            report.append("🔴 **CUT-OFF LOW DETECTED - BAD CASE SCENARIO DEVELOPING**")
            report.append("")
            report.append(f"- **Detection Count:** {len(cutoff['times'])} time steps")
            report.append(f"- **Max Vorticity:** {max(cutoff['max_vorticity']):.2e} s⁻¹ (threshold: 8×10⁻⁵ s⁻¹)")
            report.append(f"- **Detection Times:** {len(cutoff['times'])} timesteps over forecast period")
            
            if cutoff['centroids']:
                first_centroid = cutoff['centroids'][0]
                last_centroid = cutoff['centroids'][-1]
                report.append(f"- **Initial Position:** {first_centroid['lat']:.1f}°N, {abs(first_centroid['lon']):.1f}°W")
                report.append(f"- **Final Position:** {last_centroid['lat']:.1f}°N, {abs(last_centroid['lon']):.1f}°W")
                
                # Calculate evolution
                lon_change = last_centroid['lon'] - first_centroid['lon']
                report.append(f"- **Movement:** {abs(lon_change):.1f}° {'eastward' if lon_change > 0 else 'westward'}")
            
            # Track reattachment
            print("Tracking reattachment...")
            reattach = analyzer.track_cutoff_reattachment(data["gfs"], cutoff)
            
            report.append("")
            report.append("### Reattachment Analysis")
            report.append("")
            report.append(f"**Eastward Motion:** {reattach['eastward_motion']:.1f}° longitude")
            report.append(f"**300 hPa Jet Strengthening:** {'✓ Yes' if reattach['jet_strengthening'] else '✗ No'}")
            report.append("")
            
            if reattach["reattachment_detected"]:
                report.append("🔴 **CRITICAL: REATTACHMENT TO JET STREAM LIKELY**")
                report.append("")
                report.append("**⚠️  This matches Chris Parker's 'BAD CASE' scenario:**")
                report.append("")
                report.append("**Expected Evolution:**")
                report.append("1. Cut-off low forms over Louisiana on Sunday (11/2)")
                report.append("2. System moves eastward and reattaches to progressive upper-level flow")
                report.append("3. Low shifts off US East Coast Monday-Tuesday (11/3-11/4)")
                report.append("4. Creates nasty weather in southwest North Atlantic")
                report.append("")
                report.append("**Forecast Impacts (Tuesday-Wednesday, 11/3-11/5):**")
                report.append("- Winds: Likely 30-40 kt, gusting 45 kt in squalls")
                report.append("- Seas: 10-12 ft, potentially on the nose for 12 hours")
                report.append("- Duration: ~36 hours of challenging conditions")
                report.append("- Conditions settle late Wednesday (11/5)")
                report.append("")
                report.append("**Recommendation:**")
                report.append("> ⚠️  **STRONGLY CONSIDER WEDNESDAY 11/5 DEPARTURE** instead of Friday 10/31.")
                report.append("> The Friday departure window carries high uncertainty with potential for")
                report.append("> significant deterioration Monday-Wednesday. A Wednesday 11/5 departure")
                report.append("> provides higher forecast confidence and avoids the worst conditions.")
            else:
                report.append("🟡 **GOOD CASE: LOW LIKELY TO STAY OVER LAND**")
                report.append("")
                report.append("**Current forecast suggests:**")
                report.append("- Cut-off low detected but not showing strong reattachment signals")
                report.append("- System may weaken and dissipate over Louisiana")
                report.append("- Limited eastward progression")
                report.append("- Offshore waters may remain relatively favorable")
                report.append("")
                report.append("**Recommendation:**")
                report.append("> 🟡 **FRIDAY 10/31 DEPARTURE POSSIBLE** but monitor closely.")
                report.append("> Models showing cut-off low but without strong reattachment. However,")
                report.append("> this scenario is still evolving. Need 2-3 more consistent model runs")
                report.append("> to confirm. Re-evaluate at Thursday 3 PM for final go/no-go decision.")
        else:
            report.append("🟢 **NO CUT-OFF LOW DETECTED - GOOD CASE VERIFIED**")
            report.append("")
            report.append("**Analysis Results:**")
            report.append("- No significant vorticity maxima detected over Louisiana region")
            report.append("- 500 hPa vorticity remains below detection threshold (8×10⁻⁵ s⁻¹)")
            report.append("- Pattern does not match Chris Parker's 'bad case' scenario")
            report.append("- Conditions appear stable through forecast period")
            report.append("")
            report.append("**Recommendation:**")
            report.append("> 🟢 **FRIDAY 10/31 DEPARTURE LOOKS FAVORABLE** based on current analysis.")
            report.append("> The feared cut-off low scenario is NOT verifying in this model run.")
            report.append("> Conditions suggest a stable pattern with no major system development")
            report.append("> threatening the offshore waters Monday-Wednesday (11/3-11/5).")
            report.append("> ")
            report.append("> However, continue to monitor subsequent model runs. The absence of")
            report.append("> the cut-off low in this run is good news, but verify consistency")
            report.append("> across multiple runs before making final departure decision.")
    
    report.append("")
    report.append("---")
    report.append("")
    
    # Route Conditions Analysis
    report.append("## Route Conditions: Hampton → Bermuda")
    report.append("")
    
    # Analyze for typical boat
    vessel = Vessel.typical_boat()
    route = Route("hampton-bermuda", vessel=vessel)
    route_points = route.interpolate_waypoints(num_points=20)
    
    print("\nAnalyzing winds and waves...")
    
    wind_results = None
    wave_results = None
    
    if data.get("gfs"):
        wind_results = analyzer.analyze_route_winds(data["gfs"], route_points, wind_threshold=15.0)
        
        report.append("### Wind Conditions")
        report.append("")
        report.append(f"- **Maximum Wind:** {wind_results['max_wind']:.1f} m/s ({wind_results['max_wind']*1.944:.0f} kt)")
        report.append(f"- **Average Wind:** {wind_results['mean_wind']:.1f} m/s ({wind_results['mean_wind']*1.944:.0f} kt)")
        report.append(f"- **Time Above 30 kt:** {wind_results['percent_above_threshold']:.1f}%")
        report.append("")
    
    if data.get("ww3"):
        wave_results = analyzer.analyze_route_waves(data["ww3"], route_points, wave_threshold=3.0)
        
        report.append("### Wave Conditions")
        report.append("")
        report.append(f"- **Maximum Wave Height:** {wave_results['max_wave_height']:.1f} m ({wave_results['max_wave_height']*3.281:.0f} ft)")
        report.append(f"- **Average Wave Height:** {wave_results['mean_wave_height']:.1f} m ({wave_results['mean_wave_height']*3.281:.0f} ft)")
        report.append(f"- **Time Above 3m (10ft):** {wave_results['percent_above_threshold']:.1f}%")
        report.append("")
    
    report.append("---")
    report.append("")
    
    # Risk Assessment
    report.append("## Risk Assessment")
    report.append("")
    
    if wind_results and wave_results:
        print("\nCalculating risk score...")
        risk = analyzer.score_route_risk(wind_results, wave_results, cutoff if cutoff else None)
        
        report.append(f"### Overall Risk Score: {risk['risk_score']:.0f}/100")
        report.append("")
        report.append(f"**Risk Level:** {risk['risk_level']}")
        report.append("")
        report.append("**Component Breakdown:**")
        report.append("")
        report.append(f"- **Wind Risk:** {risk['wind_component']:.0f}/40")
        report.append(f"- **Wave Risk:** {risk['wave_component']:.0f}/40")
        report.append(f"- **Meteorological Features:** {risk['cutoff_component']:.0f}/20")
        report.append("")
        
        if risk['risk_factors']:
            report.append("**Risk Factors Identified:**")
            report.append("")
            for factor in risk['risk_factors']:
                report.append(f"- {factor}")
            report.append("")
        
        report.append("### Recommendation")
        report.append("")
        report.append(f"> {risk['recommendation']}")
    
    report.append("")
    report.append("---")
    report.append("")
    
    # Gulf Stream Considerations
    report.append("## Gulf Stream Crossing Strategy")
    report.append("")
    
    avg_wind = wind_results['mean_wind'] * 1.944 if wind_results else 20
    gs_rec = GulfStream.get_crossing_recommendation("hampton", {"wind_speed": avg_wind})
    
    if gs_rec["recommended_crossing_lat"]:
        report.append(f"**Recommended Crossing Latitude:** {gs_rec['recommended_crossing_lat']:.1f}°N")
    if gs_rec["recommended_exit_lat"]:
        report.append(f"**Recommended Exit Latitude:** {gs_rec['recommended_exit_lat']:.1f}°N")
    if gs_rec["avoid_before"]:
        report.append(f"**Timing:** Avoid crossing before {gs_rec['avoid_before']}")
    
    report.append("")
    report.append("**Rationale:**")
    report.append("")
    for item in gs_rec["rationale"]:
        report.append(f"- {item}")
    
    report.append("")
    report.append("**Additional Considerations:**")
    report.append("")
    report.append("- Monitor sea surface currents for eddy positions")
    report.append("- Stay south of counterclockwise eddies")
    report.append("- Stay north of clockwise eddies")
    report.append("- Potential 1-2 kt current benefit with optimal routing")
    
    report.append("")
    report.append("---")
    report.append("")
    
    # Summary
    report.append("## Summary")
    report.append("")
    report.append("### Key Points")
    report.append("")
    
    if cutoff and cutoff.get("detected"):
        report.append("1. ⚠️ **Cut-off low detected** in Louisiana region - monitor for offshore movement")
    else:
        report.append("1. ✓ **No significant cut-off low** detected at this time")
    
    if wind_results:
        if wind_results['percent_above_threshold'] > 20:
            report.append("2. ⚠️ **Elevated wind conditions** expected along route")
        else:
            report.append("2. ✓ **Moderate wind conditions** generally favorable")
    
    if wave_results:
        if wave_results['percent_above_threshold'] > 20:
            report.append("3. ⚠️ **Rough seas** anticipated at times")
        else:
            report.append("3. ✓ **Manageable wave conditions** expected")
    
    if wind_results and wave_results:
        risk = analyzer.score_route_risk(wind_results, wave_results, cutoff if cutoff else None)
        if risk['risk_level'] == 'LOW':
            report.append("4. ✓ **Overall risk assessment: FAVORABLE** for departure")
        elif risk['risk_level'] == 'MODERATE':
            report.append("4. ⚠️ **Overall risk assessment: MARGINAL** - prepare for challenging conditions")
        else:
            report.append("4. ⚠️ **Overall risk assessment: UNFAVORABLE** - consider delaying departure")
    
    report.append("")
    report.append("### Vessel-Specific Guidance")
    report.append("")
    report.append("**Slow Boats (5-5.5 kt):**")
    report.append("- Plan for 5+ day passage to Bermuda")
    report.append("- Consider stopping in Bermuda if continuing to Caribbean")
    report.append("- Most vulnerable to weather windows")
    report.append("")
    report.append("**Typical Boats (6-6.5 kt):**")
    report.append("- Plan for 4-5 day passage to Bermuda")
    report.append("- Can likely continue to Caribbean with favorable forecast")
    report.append("- Good balance of speed and comfort")
    report.append("")
    report.append("**Fast Boats (7-8.5 kt):**")
    report.append("- Plan for 3-4 day passage to Bermuda")
    report.append("- Maximum weather window flexibility")
    report.append("- Can outrun or avoid most systems")
    report.append("")
    
    report.append("---")
    report.append("")
    
    # Footer
    report.append("## About This Report")
    report.append("")
    report.append("This report was generated using the **wx-anal** weather analysis system.")
    report.append("")
    report.append("**Data Sources:**")
    report.append("- NOAA GFS (Global Forecast System)")
    report.append("- NOAA WW3 (WaveWatch III)")
    report.append("- Accessed via NOMADS OPeNDAP servers")
    report.append("")
    report.append("**Analysis Methods:**")
    report.append("- Cut-off low detection using 500 hPa vorticity fields")
    report.append("- Jet stream tracking at 300 hPa")
    report.append("- Route-specific wind and wave sampling")
    report.append("- Multi-factor risk assessment algorithm")
    report.append("")
    report.append("**Disclaimer:** This analysis is for planning purposes only. Always consult professional weather routing services for actual navigation decisions. Monitor forecasts continuously and be prepared to adjust plans based on evolving conditions.")
    report.append("")
    report.append("---")
    report.append("")
    report.append(f"*Report generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*")
    
    return "\n".join(report)


if __name__ == "__main__":
    print("="*60)
    print("GENERATING WEATHER ANALYSIS REPORT")
    print("="*60)
    print()
    
    try:
        report_content = generate_report()
        
        # Write report to file
        output_file = "WEATHER_REPORT.md"
        with open(output_file, 'w') as f:
            f.write(report_content)
        
        print()
        print("="*60)
        print(f"✓ Report generated successfully: {output_file}")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
