# Quick Start Guide

## Installation

```bash
pip install -e .
```

## 5-Minute Quick Start

### 1. Command Line Analysis

```bash
# Analyze a route
wx-anal --route hampton-bermuda --start 2025-10-31 --speed typical

# Try different vessel speeds
wx-anal --route hampton-antigua --speed fast

# Custom route
wx-anal --route custom --from hampton --to bermuda --speed slow
```

### 2. Python Script

```python
from datetime import datetime
from wx_anal import Config, WeatherDownloader, WeatherAnalyzer
from wx_anal.routes import Route, Vessel

# Create a typical cruising boat
vessel = Vessel.typical_boat()

# Define route
route = Route("hampton-bermuda", vessel=vessel)

# Estimate passage time
departure = datetime(2025, 10, 31, 18, 0)
arrival = route.estimate_arrival_time(departure)
print(f"Estimated arrival: {arrival}")

# Download weather data (requires internet)
config = Config()
downloader = WeatherDownloader(config)
data = downloader.download_offshore_route_data(
    route_name="hampton-bermuda",
    run_date=departure,
    forecast_days=10,
)

# Analyze conditions
analyzer = WeatherAnalyzer(config)
route_points = route.interpolate_waypoints(num_points=20)

wind_results = analyzer.analyze_route_winds(data["gfs"], route_points)
wave_results = analyzer.analyze_route_waves(data["ww3"], route_points)

# Risk assessment
risk = analyzer.score_route_risk(wind_results, wave_results)
print(f"Risk: {risk['risk_level']} ({risk['risk_score']}/100)")
```

### 3. Jupyter Notebook

```bash
jupyter notebook notebooks/offshore_route_analysis.ipynb
```

## Common Use Cases

### Departure Window Analysis

Compare multiple departure dates:

```python
from wx_anal.routes import Route, Vessel

vessel = Vessel.typical_boat()
route = Route("hampton-bermuda", vessel=vessel)

# Friday departure
friday = datetime(2025, 10, 31, 18, 0)
friday_arrival = route.estimate_arrival_time(friday)

# Wednesday departure  
wednesday = datetime(2025, 11, 5, 12, 0)
wednesday_arrival = route.estimate_arrival_time(wednesday)

print(f"Friday:    {(friday_arrival - friday).days} days")
print(f"Wednesday: {(wednesday_arrival - wednesday).days} days")
```

### Vessel Speed Comparison

```python
from wx_anal.routes import Route, Vessel

vessels = [
    Vessel.slow_boat(),
    Vessel.typical_boat(),
    Vessel.fast_boat(),
]

for vessel in vessels:
    route = Route("hampton-bermuda", vessel=vessel)
    arrival = route.estimate_arrival_time(departure)
    duration = arrival - departure
    print(f"{vessel.name}: {duration.days}d {duration.seconds//3600}h")
```

### Cut-off Low Detection

```python
from wx_anal import WeatherAnalyzer

analyzer = WeatherAnalyzer()

# Detect cut-off low over Louisiana
cutoff = analyzer.detect_cutoff_low(
    gfs_data,
    bbox={"lat_min": 25.0, "lat_max": 34.0, "lon_min": -96.0, "lon_max": -88.0}
)

if cutoff["detected"]:
    print(f"⚠️  Cut-off low detected at {len(cutoff['times'])} timesteps")
    
    # Track reattachment to jet stream
    reattach = analyzer.track_cutoff_reattachment(gfs_data, cutoff)
    if reattach["reattachment_detected"]:
        print("⚠️  Reattachment likely - conditions may deteriorate offshore")
```

### Gulf Stream Routing

```python
from wx_anal.routes import GulfStream

rec = GulfStream.get_crossing_recommendation(
    "hampton",
    {"wind_speed": 30}  # knots
)

print(f"Cross at: {rec['recommended_crossing_lat']}°N")
print(f"Exit at:  {rec['recommended_exit_lat']}°N")
print(f"Rationale: {rec['rationale']}")
```

## Pre-defined Routes

- `hampton-bermuda` - Hampton Roads to Bermuda (640 nm)
- `hampton-antigua` - Hampton Roads to Antigua (1500 nm)
- `bermuda-antigua` - Bermuda to Antigua (850 nm)
- `beaufort-bermuda` - Beaufort, NC to Bermuda (580 nm)

## Vessel Speed Categories

| Category | Speed | NM/Day | Description |
|----------|-------|--------|-------------|
| Slow | 5-5.5 kt | 120-130 | Heavy cruising boats |
| Typical | 6-6.5 kt | 140-160 | Average cruising boats |
| Fast | 7-8.5 kt | 170-200 | Performance cruisers |

## Configuration

### Environment Variables

```bash
export WX_ANAL_DATA_DIR=/path/to/data
export WX_ANAL_CACHE_SIZE=1000  # MB
export WX_ANAL_TIMEOUT=30       # seconds
```

### Python Configuration

```python
from wx_anal import Config

# From environment
config = Config.from_env()

# Manual
config = Config(
    data_dir="data",
    cache_size=1000,
    timeout=30,
)
```

## Troubleshooting

### Cannot Download Data

**Problem**: `NetCDF: I/O failure` errors

**Solution**: 
- Check internet connection
- Verify forecast date exists (not too far in future)
- Ensure netCDF4 and cfgrib are installed
- Try with a current date instead of future date

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'wx_anal'`

**Solution**:
```bash
pip install -e .
```

### Missing Dependencies

**Problem**: `ImportError: cannot import name 'X'`

**Solution**:
```bash
pip install -e .[dev]
```

## Next Steps

- Read the full [README.md](README.md)
- Explore the [Jupyter notebook](notebooks/offshore_route_analysis.ipynb)
- Check the [examples](examples/) directory
- Run tests: `pytest tests/`

## Getting Help

- Open an issue on GitHub
- Check the documentation
- Review examples in `examples/` directory
