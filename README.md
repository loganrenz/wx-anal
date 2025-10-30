# wx-anal

Weather models downloader and weather feature analyzer for offshore route planning.

## Overview

`wx-anal` is a Python package for downloading NOAA weather model data (GFS, GEFS, WW3) and analyzing weather features relevant to offshore sailing and marine route planning. It provides tools for:

- **Data Download**: Fetch weather model data from NOAA NOMADS via OPeNDAP
- **Feature Detection**: Identify cut-off lows, jet streams, and other meteorological features
- **Route Analysis**: Analyze wind and wave conditions along specific routes
- **Risk Assessment**: Calculate risk scores for departure windows
- **Vessel Planning**: Account for different vessel speeds and capabilities
- **Gulf Stream**: Optimize Gulf Stream crossing strategies

## Installation

```bash
# Clone repository
git clone https://github.com/loganrenz/wx-anal.git
cd wx-anal

# Install package
pip install -e .

# Install with development dependencies
pip install -e .[dev]

# Install with notebook support
pip install -e .[notebook]
```

## Quick Start

### Command Line Interface

```bash
# Analyze Hampton to Bermuda route
wx-anal --route hampton-bermuda --start 2025-10-31 --speed typical

# Analyze for a fast boat
wx-anal --route hampton-antigua --start 2025-11-05 --speed fast

# Custom route
wx-anal --route custom --from hampton --to bermuda --speed slow
```

### Python API

```python
from datetime import datetime
from wx_anal import WeatherDownloader, WeatherAnalyzer, Config
from wx_anal.routes import Route, Vessel

# Setup
config = Config.from_env()
downloader = WeatherDownloader(config)
analyzer = WeatherAnalyzer(config)

# Create route
vessel = Vessel.typical_boat()
route = Route("hampton-bermuda", vessel=vessel)

# Download weather data
departure_date = datetime(2025, 10, 31, 18, 0)
data = downloader.download_offshore_route_data(
    route_name="hampton-bermuda",
    run_date=departure_date,
    forecast_days=10,
)

# Detect cut-off low
cutoff_results = analyzer.detect_cutoff_low(
    data["gfs"],
    bbox={"lat_min": 25.0, "lat_max": 34.0, "lon_min": -96.0, "lon_max": -88.0}
)

# Analyze route conditions
route_points = route.interpolate_waypoints(num_points=20)
wind_results = analyzer.analyze_route_winds(data["gfs"], route_points)
wave_results = analyzer.analyze_route_waves(data["ww3"], route_points)

# Risk assessment
risk = analyzer.score_route_risk(wind_results, wave_results, cutoff_results)
print(f"Risk Level: {risk['risk_level']} ({risk['risk_score']:.0f}/100)")
print(f"Recommendation: {risk['recommendation']}")
```

### Advanced Analysis

```python
from wx_anal import SeaStateAnalyzer, ForecastConfidence, RouteVariant

# Heading-relative analysis
sea_state = SeaStateAnalyzer()

# Analyze wind relative to vessel heading
wind_analysis = sea_state.analyze_heading_relative_wind(
    wind_speed=15.0,  # m/s
    wind_direction=45.0,  # degrees FROM
    vessel_heading=90.0,  # degrees TO
    vessel_speed=6.0,  # knots
)
print(f"Wind: {wind_analysis['assessment']}")
print(f"Position: {wind_analysis['wind_position']}")  # HEAD, BEAM, or STERN

# Analyze waves with Gulf Stream effects
wave_analysis = sea_state.analyze_heading_relative_waves(
    wave_height=3.0,  # meters
    wave_direction=45.0,
    wave_period=7.0,  # seconds
    vessel_heading=90.0,
    in_gulf_stream=True,
    current_speed=2.0,  # knots
    current_direction=90.0,
)
print(f"Waves: {wave_analysis['assessment']}")
print(f"Steepness: {wave_analysis['steepness_category']}")
print(f"Gulf Stream amplification: {wave_analysis['gulf_stream_amplification']:.2f}x")

# Combined discomfort assessment
discomfort = sea_state.calculate_combined_discomfort(wind_analysis, wave_analysis)
print(f"Comfort: {discomfort['category']} - {discomfort['description']}")

# Forecast confidence from multiple runs
forecast_conf = ForecastConfidence()

# Analyze consistency across model runs (from multi-run analysis)
multi_run_results = [
    {"success": True, "cutoff_detected": True},
    {"success": True, "cutoff_detected": True},
    {"success": True, "cutoff_detected": False},
    # ... more runs
]
confidence = forecast_conf.analyze_cutoff_consistency(multi_run_results)
print(f"Confidence: {confidence['confidence_level']}")
print(f"Detection rate: {confidence['detection_rate']:.0%}")
print(f"Flip-flops: {confidence['flip_flops']}")

# Adjust risk for confidence
adjusted = forecast_conf.adjust_risk_for_confidence(
    base_risk_score=50.0,
    confidence_results=confidence
)
print(f"Adjusted risk: {adjusted['adjusted_risk']:.0f}/100")
print(f"Explanation: {adjusted['explanation']}")

# Create route variants
vessel = Vessel.typical_boat()
variants = RouteVariant.create_variants("hampton-bermuda", vessel)

print(f"\nAvailable variants: {[v.variant_name for v in variants]}")
for variant in variants:
    print(f"- {variant.variant_name}: {len(variant.waypoints)} waypoints")
    print(f"  Distance: {variant.get_distance():.0f} nm")

# Enhanced risk scoring with all features
enhanced_risk = analyzer.score_route_risk_enhanced(
    wind_results=wind_results,
    wave_results=wave_results,
    cutoff_results=cutoff_results,
    confidence_results=confidence,
    vessel_name="typical",
)
print(f"\nEnhanced Risk: {enhanced_risk['risk_level']} ({enhanced_risk['risk_score']:.0f}/100)")
print(f"Recommendation: {enhanced_risk['recommendation']}")
```

### Jupyter Notebook

See `notebooks/offshore_route_analysis.ipynb` for a comprehensive example analyzing departure windows for Hampton to Bermuda/Antigua routes.

```bash
# Start Jupyter
jupyter notebook notebooks/offshore_route_analysis.ipynb
```

## Features

### Weather Data Sources

- **GFS** (Global Forecast System): 0.25° resolution, 10-day forecasts
- **GEFS** (Global Ensemble Forecast System): Ensemble members for probability analysis
- **WW3** (WaveWatch III): Wave height and period forecasts
- **HYCOM** (planned): Ocean current analysis

### Meteorological Feature Detection

- **Cut-off Lows**: Detect isolated upper-level lows using 500 hPa vorticity
- **Jet Stream**: Track 300 hPa wind patterns and reattachment
- **Reattachment**: Identify when cut-off lows rejoin progressive flow

### Route-Specific Analysis

- **Wind Conditions**: Sample 10m winds along route, identify hazard periods
- **Wave Conditions**: Analyze significant wave heights and periods from WW3
- **Thresholds**: Configurable wind (30 kt default) and wave (3m default) limits
- **Timeline**: Hour-by-hour conditions along the route
- **Heading-Relative Analysis**: Wind/wave conditions relative to vessel heading (head/beam/stern)
- **Wave Steepness**: Calculate wave steepness and period for comfort assessment
- **Gulf Stream Effects**: Wave amplification in opposing currents

### Vessel Speed Categories

- **Slow Boats**: 5-5.5 kt average (120-130 nm/day)
- **Typical Boats**: 6-6.5 kt average (140-160 nm/day)
- **Fast Boats**: 7-8.5 kt average (170-200 nm/day)

### Pre-defined Routes

- `hampton-bermuda`: Hampton Roads to Bermuda (640 nm)
- `hampton-antigua`: Hampton Roads to Antigua (1500 nm)
- `bermuda-antigua`: Bermuda to Antigua (850 nm)
- `beaufort-bermuda`: Beaufort, NC to Bermuda (580 nm)

### Risk Assessment

Multi-factor risk scoring (0-100):
- **Wind Risk** (0-40 points): Based on % time above 30 kt
- **Wave Risk** (0-40 points): Based on % time above 3m
- **Cut-off Low Risk** (0-20 points): Presence of concerning features
- **Forecast Confidence**: Penalty for inconsistent model runs (0-20 points)
- **Heading-Relative Discomfort**: Additional risk for head seas and steep waves

Risk levels: LOW (<30), MODERATE (30-60), HIGH (>60)

### Forecast Confidence Analysis

- **Multi-Run Consistency**: Compare multiple GFS runs to detect forecast stability
- **Flip-Flop Detection**: Identify run-to-run changes in predicted features
- **Confidence Scoring**: HIGH/MODERATE/LOW based on model agreement
- **Uncertainty Adjustment**: Increase risk score when forecast is unreliable
- **Trend Analysis**: Track whether concern is increasing or decreasing

### Route Variants

- **Tactical Options**: Generate northern, southern, and direct route alternatives
- **Strategic Waypoints**: Different Gulf Stream crossing strategies
- **Bermuda Bailout**: Option to stop in Bermuda for slow boats
- **Comparative Analysis**: Evaluate multiple tracks for best conditions

## Configuration

### Environment Variables

```bash
# Data directory
export WX_ANAL_DATA_DIR=/path/to/data

# Cache size (MB)
export WX_ANAL_CACHE_SIZE=1000

# Request timeout (seconds)
export WX_ANAL_TIMEOUT=30

# API keys (if needed)
export WX_ANAL_API_KEY_SERVICE=your_key_here
```

### Configuration File

```python
from wx_anal import Config

# From environment
config = Config.from_env()

# Manual configuration
config = Config(
    data_dir="data",
    cache_size=1000,
    timeout=30,
    api_keys={"service": "key"}
)
```

## Use Case: Offshore Sailing Briefing

This package was designed to support the type of detailed weather briefings used by professional offshore routing services. It can help answer questions like:

- When is the best departure window for my route?
- Will a cut-off low over Louisiana affect offshore conditions?
- What are wind and wave conditions for the next 10 days?
- How do conditions differ for slow vs. fast boats?
- When should I cross the Gulf Stream?
- Should I stop in Bermuda or continue to the Caribbean?

## Development

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest

# Code formatting
black src/wx_anal

# Linting
flake8 src/wx_anal

# Type checking
mypy src/wx_anal
```

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure code passes linting and tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- NOAA NOMADS for providing open access to weather model data
- Marine forecasting community for domain expertise
- Contributors and testers

## Support

For questions, issues, or feature requests, please open an issue on GitHub.

## Roadmap

- [ ] Add Cartopy visualization for geographic plots
- [ ] Implement full GEFS ensemble probability analysis
- [ ] Add HYCOM current data integration
- [ ] Create automated briefing report generation
- [ ] Add historical verification against actual conditions
- [ ] Mobile-friendly web interface
- [ ] Real-time alerts for changing conditions