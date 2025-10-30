"""
Command-line interface for wx-anal route forecasting.

This module provides a CLI for analyzing offshore weather windows.
"""

import argparse
import logging
from datetime import datetime, timedelta
from typing import Optional
import sys

from .config import Config
from .downloader import WeatherDownloader
from .analyzer import WeatherAnalyzer
from .routes import Route, Vessel, VesselSpeed, create_route_from_ports, GulfStream


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_date(date_str: str) -> datetime:
    """Parse date string in various formats."""
    for fmt in ["%Y-%m-%d", "%Y%m%d", "%m/%d/%Y"]:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Could not parse date: {date_str}")


def analyze_route(
    route_name: str,
    start_date: Optional[str] = None,
    vessel_speed: str = "typical",
    forecast_days: int = 16,
    departure_port: Optional[str] = None,
    destination_port: Optional[str] = None,
) -> None:
    """
    Analyze weather conditions for a route.
    
    Args:
        route_name: Route identifier or "custom"
        start_date: Departure date (YYYY-MM-DD)
        vessel_speed: Vessel speed category (slow, typical, fast)
        forecast_days: Number of forecast days (default 16 for full GFS range)
        departure_port: Departure port (for custom routes)
        destination_port: Destination port (for custom routes)
    """
    # Initialize
    config = Config.from_env()
    downloader = WeatherDownloader(config)
    analyzer = WeatherAnalyzer(config)
    
    # Parse departure date
    if start_date:
        departure_time = parse_date(start_date)
    else:
        departure_time = datetime.utcnow()
        logger.info(f"No start date provided, using current time: {departure_time}")
    
    # Create vessel
    if vessel_speed == "slow":
        vessel = Vessel.slow_boat()
    elif vessel_speed == "fast":
        vessel = Vessel.fast_boat()
    else:
        vessel = Vessel.typical_boat()
    
    logger.info(f"Vessel: {vessel.name}, Speed: {vessel.avg_speed_knots:.1f} kt, {vessel.nm_per_day:.0f} nm/day")
    
    # Create route
    if route_name == "custom" and departure_port and destination_port:
        route = create_route_from_ports(departure_port, destination_port, vessel)
    else:
        route = Route(route_name, vessel=vessel)
    
    logger.info(f"Route: {route.name}")
    logger.info(f"Distance: {route._calculate_total_distance():.0f} nm")
    
    # Estimate arrival
    arrival_time = route.estimate_arrival_time(departure_time)
    duration = arrival_time - departure_time
    logger.info(f"Estimated duration: {duration.days} days, {duration.seconds // 3600} hours")
    logger.info(f"Estimated arrival: {arrival_time.strftime('%Y-%m-%d %H:%M UTC')}")
    
    # Download weather data
    print("\n" + "="*60)
    print("DOWNLOADING WEATHER DATA")
    print("="*60)
    
    try:
        data = downloader.download_offshore_route_data(
            route_name=route.name,
            run_date=departure_time,
            forecast_days=forecast_days,
        )
    except Exception as e:
        logger.error(f"Error downloading data: {e}")
        logger.error("Cannot proceed without weather data. Please check your internet connection and try again.")
        sys.exit(1)
    
    # Analyze features
    print("\n" + "="*60)
    print("WEATHER FEATURE ANALYSIS")
    print("="*60)
    
    cutoff_results = None
    if data.get("gfs"):
        try:
            # Detect cut-off low over Louisiana
            cutoff_results = analyzer.detect_cutoff_low(
                data["gfs"],
                bbox={"lat_min": 25.0, "lat_max": 34.0, "lon_min": -96.0, "lon_max": -88.0}
            )
            
            if cutoff_results["detected"]:
                print("\n⚠️  CUT-OFF LOW DETECTED over Louisiana region")
                print(f"   Times detected: {len(cutoff_results['times'])}")
                if cutoff_results["centroids"]:
                    first = cutoff_results["centroids"][0]
                    last = cutoff_results["centroids"][-1]
                    print(f"   Initial position: {first['lat']:.1f}°N, {first['lon']:.1f}°W")
                    print(f"   Final position: {last['lat']:.1f}°N, {last['lon']:.1f}°W")
                
                # Track reattachment
                reattach = analyzer.track_cutoff_reattachment(data["gfs"], cutoff_results)
                print(f"\n   Eastward motion: {reattach['eastward_motion']:.1f}°")
                if reattach["reattachment_detected"]:
                    print("   ⚠️  REATTACHMENT TO JET STREAM LIKELY")
                    print("   → Expect deteriorating conditions as system moves offshore")
                else:
                    print("   ✓  Low likely to remain over land")
                    print("   → Offshore conditions may remain favorable")
            else:
                print("\n✓  No significant cut-off low detected")
        except Exception as e:
            logger.error(f"Error in feature detection: {e}")
    
    # Analyze route conditions
    print("\n" + "="*60)
    print("ROUTE CONDITIONS ANALYSIS")
    print("="*60)
    
    route_points = route.interpolate_waypoints(num_points=20)
    
    # Wind analysis
    wind_results = {"max_wind": 0.0, "mean_wind": 0.0, "percent_above_threshold": 0.0}
    if data.get("gfs"):
        try:
            wind_results = analyzer.analyze_route_winds(
                data["gfs"],
                route_points,
                wind_threshold=15.0,  # 30 kt
            )
            
            print(f"\nWind Analysis:")
            print(f"  Max wind: {wind_results['max_wind']:.1f} m/s ({wind_results['max_wind'] * 1.944:.0f} kt)")
            print(f"  Mean wind: {wind_results['mean_wind']:.1f} m/s ({wind_results['mean_wind'] * 1.944:.0f} kt)")
            print(f"  Time above 30 kt: {wind_results['percent_above_threshold']:.1f}%")
        except Exception as e:
            logger.error(f"Error in wind analysis: {e}")
    
    # Wave analysis
    wave_results = {"max_wave_height": 0.0, "mean_wave_height": 0.0, "percent_above_threshold": 0.0}
    if data.get("ww3"):
        try:
            wave_results = analyzer.analyze_route_waves(
                data["ww3"],
                route_points,
                wave_threshold=3.0,  # 3m
            )
            
            print(f"\nWave Analysis:")
            print(f"  Max wave height: {wave_results['max_wave_height']:.1f} m ({wave_results['max_wave_height'] * 3.281:.0f} ft)")
            print(f"  Mean wave height: {wave_results['mean_wave_height']:.1f} m ({wave_results['mean_wave_height'] * 3.281:.0f} ft)")
            print(f"  Time above 3m: {wave_results['percent_above_threshold']:.1f}%")
        except Exception as e:
            logger.error(f"Error in wave analysis: {e}")
    
    # Risk assessment
    print("\n" + "="*60)
    print("RISK ASSESSMENT")
    print("="*60)
    
    risk = analyzer.score_route_risk(wind_results, wave_results, cutoff_results)
    
    print(f"\nRisk Score: {risk['risk_score']:.0f}/100")
    print(f"Risk Level: {risk['risk_level']}")
    print(f"\nComponents:")
    print(f"  Wind risk: {risk['wind_component']:.0f}/40")
    print(f"  Wave risk: {risk['wave_component']:.0f}/40")
    print(f"  Cut-off low risk: {risk['cutoff_component']:.0f}/20")
    
    if risk['risk_factors']:
        print(f"\nRisk Factors:")
        for factor in risk['risk_factors']:
            print(f"  • {factor}")
    
    print(f"\n💡 RECOMMENDATION:")
    print(f"   {risk['recommendation']}")
    
    # Gulf Stream recommendations
    if departure_port and departure_port.lower() in ["hampton", "beaufort", "chesapeake"]:
        print("\n" + "="*60)
        print("GULF STREAM CROSSING")
        print("="*60)
        
        gs_rec = GulfStream.get_crossing_recommendation(
            departure_port,
            {"wind_speed": wind_results.get("max_wind", 0) * 1.944}  # Convert to kt
        )
        
        if gs_rec["recommended_crossing_lat"]:
            print(f"\nRecommended crossing latitude: {gs_rec['recommended_crossing_lat']:.1f}°N")
        if gs_rec["recommended_exit_lat"]:
            print(f"Recommended exit latitude: {gs_rec['recommended_exit_lat']:.1f}°N")
        if gs_rec["avoid_before"]:
            print(f"⚠️  Avoid crossing before: {gs_rec['avoid_before']}")
        
        if gs_rec["rationale"]:
            print(f"\nRationale:")
            for item in gs_rec["rationale"]:
                print(f"  • {item}")
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="wx-anal: Weather route analysis for offshore passages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze Hampton to Bermuda route
  wx-anal --route hampton-bermuda --start 2025-10-31 --speed typical
  
  # Analyze Hampton to Antigua for a fast boat
  wx-anal --route hampton-antigua --start 2025-11-05 --speed fast
  
  # Custom route
  wx-anal --route custom --from hampton --to bermuda --speed slow
  
Vessel Speed Categories:
  slow    : 5-5.5 kt, 120-130 nm/day
  typical : 6-6.5 kt, 140-160 nm/day  (default)
  fast    : 7-8.5 kt, 170-200 nm/day
        """
    )
    
    parser.add_argument(
        "--route",
        type=str,
        default="hampton-bermuda",
        help="Route name or 'custom' (default: hampton-bermuda)"
    )
    parser.add_argument(
        "--start",
        type=str,
        help="Departure date (YYYY-MM-DD, default: today)"
    )
    parser.add_argument(
        "--speed",
        type=str,
        choices=["slow", "typical", "fast"],
        default="typical",
        help="Vessel speed category (default: typical)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=16,
        help="Forecast days to analyze (default: 16, full GFS range)"
    )
    parser.add_argument(
        "--from",
        dest="departure_port",
        type=str,
        help="Departure port (for custom routes)"
    )
    parser.add_argument(
        "--to",
        dest="destination_port",
        type=str,
        help="Destination port (for custom routes)"
    )
    
    args = parser.parse_args()
    
    try:
        analyze_route(
            route_name=args.route,
            start_date=args.start,
            vessel_speed=args.speed,
            forecast_days=args.days,
            departure_port=args.departure_port,
            destination_port=args.destination_port,
        )
    except Exception as e:
        logger.error(f"Error in route analysis: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
