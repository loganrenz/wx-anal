# Network Access and Data Download

## Overview

`wx-anal` is designed to download weather model data from NOAA NOMADS servers via OPeNDAP. However, network access requirements and restrictions can affect data availability.

## Real Data Download

### Requirements

To download real NOAA weather model data, you need:

1. **Internet connectivity** to nomads.ncep.noaa.gov
2. **Python packages**: netCDF4, cfgrib, xarray
3. **Valid forecast dates** (NOAA typically keeps 5-7 days of archived data)
4. **No network restrictions** blocking access to NOAA servers

### Testing Real Data Access

```python
from datetime import datetime
from wx_anal import Config, WeatherDownloader

# Initialize
config = Config()
downloader = WeatherDownloader(config)

# Get latest available run
latest = downloader.get_latest_run('gfs')
print(f"Latest GFS run: {latest}")

# Attempt download (use a recent date)
try:
    data = downloader.download_gfs(
        run_date=latest,
        forecast_hours=[0, 6, 12],  # Just first 3 time steps
        levels=[500],  # Just 500 hPa
        bbox={
            "lat_min": 30,
            "lat_max": 40,
            "lon_min": -80,
            "lon_max": -70,
        }
    )
    print("✓ Successfully downloaded GFS data")
    print(f"  Variables: {list(data.variables)}")
except Exception as e:
    print(f"✗ Download failed: {e}")
```

### Common Issues

#### DNS Resolution Failure

**Error**: `Failed to resolve 'nomads.ncep.noaa.gov'`

**Causes**:
- No internet connection
- Network firewall blocking NOAA domains
- Sandboxed/restricted environment
- VPN or proxy issues

**Solutions**:
1. Check internet connectivity
2. Verify firewall settings
3. Use mock data for development/testing
4. Try from a different network

#### NetCDF I/O Failure

**Error**: `NetCDF: I/O failure`

**Causes**:
- Forecast date doesn't exist (too far in future/past)
- NOAA server temporarily unavailable
- OPeNDAP service down
- Authentication required (rare)

**Solutions**:
1. Use current or recent dates only
2. Check NOAA NOMADS status: https://nomads.ncep.noaa.gov/
3. Try again later
4. Use mock data as fallback

#### Date Not Available

**Error**: Data exists but returns empty

**Causes**:
- Requested date is in the future
- Requested date has been archived/removed
- Model run hasn't completed yet

**Solutions**:
1. Use dates within last 5-7 days
2. Check model run times (0Z, 6Z, 12Z, 18Z UTC)
3. Allow 6-8 hours delay for model completion

## Mock Data (Demonstration Mode)

For development, testing, and demonstration purposes, `wx-anal` includes a synthetic data generator.

### Using Mock Data

#### Command Line

```bash
# Add --mock flag
wx-anal --route hampton-bermuda --start 2025-10-29 --mock
```

#### Python API

```python
from wx_anal import WeatherDownloader

downloader = WeatherDownloader()

# Use mock data
data = downloader.download_offshore_route_data(
    route_name="hampton-bermuda",
    forecast_days=10,
    use_mock_data=True  # Enable mock data
)
```

### Mock Data Features

The synthetic data generator creates realistic:

- **GFS data**: 
  - Multiple pressure levels (1000, 850, 700, 500, 300 hPa)
  - Geopotential height, vorticity, winds, pressure
  - Cut-off low signature over Louisiana
  - Jet stream at 300 hPa
  - Realistic spatial and temporal patterns

- **WW3 data**:
  - Significant wave height
  - Wave period
  - Gulf Stream wave enhancement
  - Realistic offshore wave patterns

### Mock Data Limitations

Mock data is **NOT** suitable for:
- ❌ Actual route planning decisions
- ❌ Real-world safety assessments
- ❌ Navigation or voyage planning
- ❌ Professional weather routing

Mock data **IS** suitable for:
- ✓ Software development and testing
- ✓ Algorithm validation
- ✓ User interface development
- ✓ Training and education
- ✓ Demonstrating capabilities
- ✓ Offline development

## Automatic Fallback

The CLI automatically falls back to mock data if real data download fails:

```bash
# This will try real data first, then mock if it fails
wx-anal --route hampton-bermuda --start 2025-10-29
```

Output will indicate which data source was used:
```
INFO - Using mock data for demonstration
```

## Production Deployment

For production use with real weather data:

### 1. Verify Network Access

```bash
# Test DNS resolution
nslookup nomads.ncep.noaa.gov

# Test HTTP connectivity
curl -I https://nomads.ncep.noaa.gov/

# Test OPeNDAP access
curl -I https://nomads.ncep.noaa.gov/dods/
```

### 2. Configure Firewall

Ensure outbound HTTPS (port 443) access to:
- nomads.ncep.noaa.gov
- *.ncep.noaa.gov

### 3. Monitor Data Availability

NOAA model runs follow a schedule:
- **GFS**: 0Z, 6Z, 12Z, 18Z daily (6-hour updates)
- **GEFS**: 0Z, 6Z, 12Z, 18Z daily
- **WW3**: Multiple times daily

Allow 4-8 hours after model time for data availability.

### 4. Handle Failures Gracefully

```python
from wx_anal import WeatherDownloader

downloader = WeatherDownloader()

try:
    # Try real data
    data = downloader.download_offshore_route_data(
        route_name="hampton-bermuda",
        use_mock_data=False
    )
    if data.get("gfs"):
        print("Using real NOAA data")
    else:
        print("Partial data - some models unavailable")
except Exception as e:
    print(f"Real data unavailable: {e}")
    print("Falling back to mock data")
    data = downloader.download_offshore_route_data(
        route_name="hampton-bermuda",
        use_mock_data=True
    )
```

### 5. Caching

Cache downloaded data to reduce load and handle intermittent connectivity:

```python
from wx_anal import Config, WeatherDownloader

config = Config(data_dir="./cache")
downloader = WeatherDownloader(config)

# Download and cache
data = downloader.download_gfs()
cache_file = downloader.save_to_cache(data, "gfs_latest.nc")

# Load from cache later
cached_data = downloader.load_from_cache("gfs_latest.nc")
```

## Alternative Data Sources

If NOAA NOMADS access is consistently unavailable, consider:

1. **AWS Open Data**: NOAA data on AWS S3
2. **UCAR RDA**: Research Data Archive
3. **Local model runs**: Run WRF/GFS locally
4. **Commercial providers**: Weather API services
5. **European data**: ECMWF Copernicus

## Support

If you encounter persistent data access issues:

1. Check [NOAA NOMADS status](https://nomads.ncep.noaa.gov/)
2. Review [OPeNDAP documentation](https://www.opendap.org/)
3. Open an issue with connection details
4. Use mock data for development

## Disclaimer

**IMPORTANT**: Mock/synthetic data is for demonstration only. Always use real, current weather data for actual navigation, safety, and planning decisions. Consult professional weather routing services for offshore passages.
