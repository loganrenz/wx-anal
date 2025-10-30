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
- **Wave Conditions**: Analyze significant wave heights from WW3
- **Thresholds**: Configurable wind (30 kt default) and wave (3m default) limits
- **Timeline**: Hour-by-hour conditions along the route

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

Risk levels: LOW (<30), MODERATE (30-60), HIGH (>60)

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