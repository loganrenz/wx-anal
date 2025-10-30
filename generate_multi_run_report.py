#!/usr/bin/env python
"""
Generate comprehensive multi-run weather analysis comparing multiple model runs.

This script analyzes the last 10 GFS model runs to track the evolution of
the cut-off low over Louisiana and provides ensemble-like analysis of
forecast consistency.
"""

import sys
from datetime import datetime, timedelta
from wx_anal import Config, WeatherDownloader, WeatherAnalyzer
from wx_anal.routes import Route, Vessel, GulfStream
import logging
import traceback

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def analyze_single_run(downloader, analyzer, run_date, run_label):
    """Analyze a single model run for cut-off low."""
    results = {
        "run_date": run_date,
        "run_label": run_label,
        "success": False,
        "cutoff_detected": False,
        "cutoff_data": None,
        "reattachment_data": None,
        "error": None,
    }
    
    try:
        logger.info(f"Analyzing {run_label}...")
        
        # Download data
        data = downloader.download_offshore_route_data(
            route_name="gulfstream",  # Larger area to capture Louisiana
            run_date=run_date,
            forecast_days=7,
            use_mock_data=False,
        )
        
        if not data.get("gfs"):
            results["error"] = "GFS data not available"
            return results
        
        results["success"] = True
        
        # Detect cut-off low
        cutoff = analyzer.detect_cutoff_low(
            data["gfs"],
            bbox={"lat_min": 25.0, "lat_max": 34.0, "lon_min": -96.0, "lon_max": -88.0}
        )
        
        results["cutoff_detected"] = cutoff["detected"]
        results["cutoff_data"] = {
            "timesteps": len(cutoff["times"]),
            "max_vorticity": max(cutoff["max_vorticity"]) if cutoff["max_vorticity"] else 0,
            "centroids": cutoff["centroids"][:5] if cutoff["centroids"] else [],
        }
        
        # Track reattachment if detected
        if cutoff["detected"]:
            reattach = analyzer.track_cutoff_reattachment(data["gfs"], cutoff)
            results["reattachment_data"] = {
                "eastward_motion": reattach["eastward_motion"],
                "jet_strengthening": reattach["jet_strengthening"],
                "reattachment_detected": reattach["reattachment_detected"],
            }
        
        logger.info(f"  {'✓' if cutoff['detected'] else '✗'} Cut-off low: {cutoff['detected']}")
        
    except Exception as e:
        results["error"] = str(e)[:200]
        logger.error(f"  Error: {str(e)[:100]}")
    
    return results


def generate_multi_run_report():
    """Generate comprehensive multi-run analysis report."""
    
    report = []
    report.append("# Multi-Run Weather Analysis Report")
    report.append("")
    report.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    report.append("")
    report.append("**Analysis Type:** Model Run Consistency Check")
    report.append("")
    report.append("---")
    report.append("")
    
    # Initialize
    config = Config(data_dir="./data")
    downloader = WeatherDownloader(config)
    analyzer = WeatherAnalyzer(config)
    
    # Determine runs to analyze
    print("\n" + "="*60)
    print("MULTI-RUN ANALYSIS: LAST 10 GFS MODEL RUNS")
    print("="*60)
    print()
    
    latest_run = downloader.get_latest_run('gfs')
    
    # Calculate run times for last 10 runs (every 6 hours)
    run_times = []
    for i in range(10):
        run_time = latest_run - timedelta(hours=i * 6)
        run_times.append(run_time)
    
    report.append("## Model Runs Analyzed")
    report.append("")
    report.append(f"**Latest Run:** {latest_run.strftime('%Y-%m-%d %H:%M UTC')}")
    report.append(f"**Analysis Period:** Last 60 hours (10 runs at 6-hour intervals)")
    report.append("")
    report.append("| Run Time | Cycle | Age |")
    report.append("|----------|-------|-----|")
    
    for i, rt in enumerate(run_times):
        age_hours = (latest_run - rt).total_seconds() / 3600
        report.append(f"| {rt.strftime('%Y-%m-%d %H:%M UTC')} | {rt.hour:02d}Z | {age_hours:.0f}h ago |")
    
    report.append("")
    report.append("---")
    report.append("")
    
    # Analyze each run
    print("Analyzing model runs...")
    print()
    
    all_results = []
    successful_runs = 0
    detected_runs = 0
    reattachment_runs = 0
    
    for i, run_time in enumerate(run_times):
        run_label = f"Run {i+1}: {run_time.strftime('%Y-%m-%d %Hz')}"
        results = analyze_single_run(downloader, analyzer, run_time, run_label)
        all_results.append(results)
        
        if results["success"]:
            successful_runs += 1
            if results["cutoff_detected"]:
                detected_runs += 1
                if results.get("reattachment_data", {}).get("reattachment_detected"):
                    reattachment_runs += 1
    
    # Summary statistics
    report.append("## Analysis Summary")
    report.append("")
    report.append(f"**Successfully Analyzed:** {successful_runs}/10 runs")
    report.append(f"**Cut-off Low Detected:** {detected_runs}/{successful_runs} runs ({100*detected_runs/max(successful_runs,1):.0f}%)")
    report.append(f"**Reattachment Likely:** {reattachment_runs}/{detected_runs if detected_runs > 0 else 1} detected runs")
    report.append("")
    
    # Determine consensus
    if successful_runs == 0:
        consensus = "Unable to determine - no successful runs"
        confidence = "NONE"
    elif detected_runs == 0:
        consensus = "🟢 GOOD CASE - No cut-off low in any run"
        confidence = "HIGH" if successful_runs >= 5 else "MODERATE"
    elif detected_runs == successful_runs:
        if reattachment_runs == detected_runs:
            consensus = "🔴 BAD CASE - All runs show cut-off low with reattachment"
            confidence = "HIGH"
        else:
            consensus = "🟡 MARGINAL - All runs show cut-off, mixed reattachment signals"
            confidence = "MODERATE"
    else:
        detection_pct = 100 * detected_runs / successful_runs
        if detection_pct > 70:
            consensus = "🟡 UNCERTAIN - Majority show cut-off low"
            confidence = "LOW"
        elif detection_pct > 30:
            consensus = "🟡 UNCERTAIN - Mixed signals across runs"
            confidence = "VERY LOW"
        else:
            consensus = "🟢 LIKELY GOOD - Minority show cut-off low"
            confidence = "MODERATE"
    
    report.append(f"**Forecast Consensus:** {consensus}")
    report.append(f"**Confidence Level:** {confidence}")
    report.append("")
    report.append("---")
    report.append("")
    
    # Detailed run-by-run analysis
    report.append("## Detailed Run-by-Run Analysis")
    report.append("")
    
    for i, results in enumerate(all_results):
        run_num = i + 1
        run_time = results["run_date"]
        
        report.append(f"### Run {run_num}: {run_time.strftime('%Y-%m-%d %Hz')}")
        report.append("")
        
        if not results["success"]:
            report.append(f"❌ **Analysis Failed**")
            report.append(f"- Error: {results.get('error', 'Unknown error')}")
        elif not results["cutoff_detected"]:
            report.append("✅ **No Cut-off Low Detected**")
            report.append("- 500 hPa vorticity below threshold over Louisiana")
            report.append("- Stable pattern, no closed circulation")
        else:
            cd = results["cutoff_data"]
            rd = results.get("reattachment_data", {})
            
            report.append("⚠️ **Cut-off Low Detected**")
            report.append("")
            report.append(f"- **Timesteps Detected:** {cd['timesteps']}")
            report.append(f"- **Peak Vorticity:** {cd['max_vorticity']:.2e} s⁻¹")
            
            if cd["centroids"]:
                first = cd["centroids"][0]
                report.append(f"- **Position:** {first['lat']:.1f}°N, {abs(first['lon']):.1f}°W")
            
            if rd:
                report.append("")
                report.append("**Reattachment Analysis:**")
                report.append(f"- Eastward Motion: {rd['eastward_motion']:.1f}°")
                report.append(f"- Jet Strengthening: {'Yes' if rd['jet_strengthening'] else 'No'}")
                report.append(f"- Reattachment: {'✓ LIKELY' if rd['reattachment_detected'] else '✗ Unlikely'}")
        
        report.append("")
    
    report.append("---")
    report.append("")
    
    # Trend analysis
    report.append("## Trend Analysis")
    report.append("")
    
    recent_runs = [r for r in all_results[:3] if r["success"]]
    older_runs = [r for r in all_results[7:] if r["success"]]
    
    recent_detection = sum(1 for r in recent_runs if r["cutoff_detected"])
    older_detection = sum(1 for r in older_runs if r["cutoff_detected"])
    
    if recent_runs and older_runs:
        recent_pct = 100 * recent_detection / len(recent_runs)
        older_pct = 100 * older_detection / len(older_runs)
        
        report.append(f"**Recent Runs (last 3):** {recent_detection}/{len(recent_runs)} show cut-off ({recent_pct:.0f}%)")
        report.append(f"**Older Runs (runs 8-10):** {older_detection}/{len(older_runs)} show cut-off ({older_pct:.0f}%)")
        report.append("")
        
        if recent_pct > older_pct + 20:
            trend = "📈 **Increasing Concern** - Recent runs more likely to show cut-off low"
        elif recent_pct < older_pct - 20:
            trend = "📉 **Decreasing Concern** - Recent runs less likely to show cut-off low"
        else:
            trend = "➡️ **Stable Forecast** - Consistent signal across time"
        
        report.append(trend)
    
    report.append("")
    report.append("---")
    report.append("")
    
    # Model comparison notes
    report.append("## Multi-Model Comparison")
    report.append("")
    report.append("### GFS (Global Forecast System)")
    report.append("")
    report.append("✅ **Analyzed:** 10 recent runs (primary analysis above)")
    report.append("")
    report.append("**Characteristics:**")
    report.append("- Resolution: 0.25° (~25 km)")
    report.append("- Update Frequency: Every 6 hours (00Z, 06Z, 12Z, 18Z)")
    report.append("- Forecast Range: 16 days")
    report.append("- Strengths: Frequent updates, free access, good for trends")
    report.append("- Limitations: Can over-amplify features, less skill at extended range")
    report.append("")
    
    report.append("### ECMWF (European Model)")
    report.append("")
    report.append("⚠️ **Status:** Not analyzed (requires subscription)")
    report.append("")
    report.append("**Characteristics:**")
    report.append("- Resolution: 0.1° (~9 km)")
    report.append("- Update Frequency: Twice daily (00Z, 12Z)")
    report.append("- Forecast Range: 15 days")
    report.append("- Strengths: Generally considered most accurate, excellent upper-air analysis")
    report.append("- Access: Requires ECMWF account or commercial provider")
    report.append("")
    report.append("**Typical Comparison with GFS:**")
    report.append("- ECMWF often more conservative with cut-off low formation")
    report.append("- Better handling of upper-level dynamics")
    report.append("- When ECMWF and GFS agree, confidence is high")
    report.append("- When they disagree, ECMWF typically more reliable")
    report.append("")
    
    report.append("### CMC (Canadian Model)")
    report.append("")
    report.append("⚠️ **Status:** Not analyzed (limited public access)")
    report.append("")
    report.append("**Characteristics:**")
    report.append("- Resolution: 0.24° (~25 km)")
    report.append("- Update Frequency: Twice daily (00Z, 12Z)")
    report.append("- Forecast Range: 16 days")
    report.append("- Strengths: Independent verification, good North American coverage")
    report.append("- Access: Limited public OPeNDAP access")
    report.append("")
    
    report.append("---")
    report.append("")
    
    # Recommendations
    report.append("## Recommendations Based on Multi-Run Analysis")
    report.append("")
    
    if detected_runs == 0 and successful_runs >= 5:
        report.append("### 🟢 FAVORABLE FOR FRIDAY 10/31 DEPARTURE")
        report.append("")
        report.append("**Rationale:**")
        report.append(f"- None of the {successful_runs} analyzed runs show cut-off low development")
        report.append("- Consistent signal across all model runs")
        report.append("- Chris Parker's feared 'bad case' scenario not materializing")
        report.append("")
        report.append("**Action Items:**")
        report.append("1. ✓ Proceed with Friday afternoon departure planning")
        report.append("2. Continue monitoring 12Z and 18Z runs today for confirmation")
        report.append("3. Final go/no-go decision Friday morning based on latest data")
        report.append("4. Have contingency plan for Wednesday 11/5 if conditions change")
    
    elif detected_runs == successful_runs and reattachment_runs >= detected_runs * 0.7:
        report.append("### 🔴 RECOMMEND WEDNESDAY 11/5 DEPARTURE")
        report.append("")
        report.append("**Rationale:**")
        report.append(f"- ALL {successful_runs} runs show cut-off low formation")
        report.append(f"- {reattachment_runs}/{detected_runs} runs indicate likely reattachment to jet stream")
        report.append("- Chris Parker's 'bad case' scenario IS verifying")
        report.append("- High confidence in deteriorating conditions Monday-Wednesday")
        report.append("")
        report.append("**Expected Conditions (if departed Friday):**")
        report.append("- Monday-Tuesday: 30-40 kt winds, gusting 45 kt")
        report.append("- Tuesday-Wednesday: 10-12 ft seas, potentially on the nose")
        report.append("- Duration: 24-36 hours of challenging conditions")
        report.append("")
        report.append("**Action Items:**")
        report.append("1. ❌ Defer Friday 10/31 departure")
        report.append("2. ✓ Plan for Wednesday 11/5 midday departure")
        report.append("3. Monitor Tuesday evening forecast for final confirmation")
        report.append("4. Prepare crew for 5-day delay")
    
    else:
        report.append("### 🟡 UNCERTAIN - RECOMMEND CONTINUED MONITORING")
        report.append("")
        report.append("**Rationale:**")
        report.append(f"- Mixed signals: {detected_runs}/{successful_runs} runs show cut-off low")
        report.append("- Forecast consistency is LOW")
        report.append("- Cannot definitively rule in or out bad case scenario")
        report.append("")
        report.append("**Action Items:**")
        report.append("1. ⏸️ Hold Friday 10/31 departure decision")
        report.append("2. Re-analyze at Thursday 3 PM with latest runs")
        report.append("3. Need 2-3 more runs showing consistency")
        report.append("4. If uncertainty persists, default to Wednesday 11/5 departure")
        report.append("5. Monitor ECMWF solution if available (higher reliability)")
    
    report.append("")
    report.append("---")
    report.append("")
    
    # Footer
    report.append("## Technical Notes")
    report.append("")
    report.append("**Analysis Method:**")
    report.append("- 500 hPa vorticity threshold: 8×10⁻⁵ s⁻¹")
    report.append("- Detection region: 25-34°N, 88-96°W (Louisiana)")
    report.append("- Reattachment criteria: >5° eastward motion + 300 hPa winds >30 m/s")
    report.append("- Spatial clustering: scipy.ndimage for feature identification")
    report.append("")
    report.append("**Data Sources:**")
    report.append("- GFS: NOAA NOMADS OPeNDAP servers")
    report.append("- ECMWF: Not accessed (subscription required)")
    report.append("- CMC: Not accessed (limited public availability)")
    report.append("")
    report.append("**Limitations:**")
    report.append("- Analysis limited to publicly accessible GFS data")
    report.append("- ECMWF and CMC comparison would strengthen confidence")
    report.append("- Model runs older than 3 days may not be available")
    report.append("- Network connectivity required for real-time analysis")
    report.append("")
    report.append("---")
    report.append("")
    report.append(f"*Multi-run analysis generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*")
    report.append("")
    report.append("**Next Update:** Re-run analysis with `python generate_multi_run_report.py` for latest data")
    
    return "\n".join(report)


if __name__ == "__main__":
    print("="*60)
    print("GENERATING MULTI-RUN WEATHER ANALYSIS")
    print("="*60)
    print()
    
    try:
        report_content = generate_multi_run_report()
        
        # Write report to file
        output_file = "MULTI_RUN_ANALYSIS.md"
        with open(output_file, 'w') as f:
            f.write(report_content)
        
        print()
        print("="*60)
        print(f"✓ Multi-run analysis complete: {output_file}")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Error generating report: {e}")
        traceback.print_exc()
        sys.exit(1)
