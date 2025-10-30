# Integration Tests for Data Downloads

## Overview

This directory contains integration tests that verify real weather data downloads from NOAA servers. These tests ensure that:

1. **Data downloads work** - We can successfully connect to NOAA NOMADS servers
2. **Data is valid** - Downloaded data contains expected variables and realistic values
3. **16-day forecast available** - GFS provides the full 384-hour forecast range
4. **Data quality** - Timestamps are consistent, spatial coverage is adequate, no data corruption

## Mock Data Policy

**IMPORTANT:** Mock/synthetic data is **ONLY** allowed in unit tests in the `tests/` directory. Production code must **NEVER** use mock data to avoid accidentally using fake data for real analysis.

### Where Mock Data is Allowed
- ✅ Unit tests (`test_*.py` files excluding `test_*_integration.py`)
- ✅ Demo scripts when explicitly noted as demonstration

### Where Mock Data is FORBIDDEN
- ❌ CLI commands (`wx-anal` command)
- ❌ Main analysis scripts (`generate_weather_report.py`, `generate_multi_run_report.py`)
- ❌ Library code (`src/wx_anal/*.py`)
- ❌ Integration tests

## Running Integration Tests

Integration tests are marked with `@pytest.mark.integration` and are **skipped by default** because they:
- Require internet connection
- Access external NOAA servers
- May take several minutes to run
- Depend on server availability

### Run All Tests (Excluding Integration)

```bash
# Default: runs all tests except integration tests
pytest

# Or explicitly
pytest -m "not integration"
```

### Run Only Integration Tests

```bash
# Run integration tests only
pytest -m integration

# Run with verbose output
pytest -m integration -v

# Run specific integration test file
pytest tests/test_downloader_integration.py -v
```

### Run All Tests Including Integration

```bash
# Run everything
pytest -m ""

# Or
pytest --no-cov -m ""
```

## Integration Test Categories

### 1. GFS Download Tests (`TestGFSDownload`)
- **test_download_gfs_basic**: Basic GFS download with minimal parameters
- **test_download_gfs_16day_forecast**: Verify full 16-day (384 hour) forecast
- **test_gfs_has_required_variables**: Check for required variables (winds, vorticity, etc.)
- **test_gfs_data_values_realistic**: Validate data ranges are realistic

### 2. WaveWatch III Tests (`TestWW3Download`)
- **test_download_ww3_basic**: Basic wave data download
- **test_ww3_data_values_realistic**: Validate wave heights are realistic

### 3. Offshore Route Tests (`TestOffshoreRouteDownload`)
- **test_download_hampton_bermuda**: Complete route data download
- **test_download_with_16day_forecast**: Verify 16-day data for full passage

### 4. Data Quality Tests (`TestDataQuality`)
- **test_gfs_time_consistency**: Time dimension is ordered and consistent
- **test_gfs_coordinates_coverage**: Spatial coverage matches requested bbox

### 5. Error Handling Tests (`TestErrorHandling`)
- **test_invalid_date_raises_error**: Future dates are rejected
- **test_invalid_bbox_raises_error**: Invalid bounding boxes are caught

## Test Data

Integration tests use:
- **Recent run date**: 48 hours ago to ensure data availability
- **Small spatial regions**: To keep downloads fast
- **Limited time steps**: Download only what's needed for validation

## Expected Test Duration

- Individual test: 10-30 seconds
- Full integration suite: 3-5 minutes
- May vary based on network speed and server load

## Troubleshooting

### Tests Fail Due to Network Issues

```python
# Check NOAA server status
curl -I https://nomads.ncep.noaa.gov/dods/

# If connection fails, servers may be down for maintenance
```

### Tests Fail Due to Data Unavailability

NOAA servers typically have a 6-hour delay for GFS data. Tests use 48-hour-old data to avoid this issue, but occasionally older data may be purged.

```bash
# Try with more recent data
pytest tests/test_downloader_integration.py::TestGFSDownload::test_download_gfs_basic -v
```

### Tests Are Slow

Integration tests intentionally download minimal data, but network speed affects duration. Use `-v` flag to see progress:

```bash
pytest -m integration -v -s
```

## Continuous Integration

For CI/CD pipelines:

```yaml
# Run unit tests on every commit
- name: Run unit tests
  run: pytest

# Run integration tests on schedule or manually
- name: Run integration tests
  run: pytest -m integration
  if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
```

## Adding New Integration Tests

When adding new data download features:

1. Add integration test in `test_downloader_integration.py`
2. Mark with `@pytest.mark.integration`
3. Use `recent_run_date` fixture for reliable data
4. Keep downloads minimal (small bbox, few timesteps)
5. Validate data structure AND values

Example:

```python
@pytest.mark.integration
def test_new_download_feature(downloader, recent_run_date):
    """Test new data download capability."""
    data = downloader.download_new_feature(
        run_date=recent_run_date,
        bbox={"lat_min": 35.0, "lat_max": 40.0, "lon_min": -75.0, "lon_max": -70.0}
    )
    
    assert data is not None
    assert "required_variable" in data.variables
    # ... additional validation
```

## No Mock Data in Production

The integration tests verify that production code can successfully download real data. If mock data fallbacks exist in production code, these tests will fail, which is by design.

**Remember:** Accidental use of mock data for real analysis is a critical error. These tests prevent that.
