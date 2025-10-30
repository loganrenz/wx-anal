"""
Integration tests for weather data downloading.

These tests verify that we can successfully download real weather data
from NOAA servers and that the data has the expected structure and content.

NOTE: These tests require internet connection and may take several minutes to run.
They are marked with @pytest.mark.integration so they can be run separately.
"""

import pytest
from datetime import datetime, timedelta
import logging

from wx_anal import Config, WeatherDownloader

logger = logging.getLogger(__name__)

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def downloader():
    """Create downloader with test configuration."""
    config = Config(data_dir="./test_data")
    return WeatherDownloader(config)


@pytest.fixture
def recent_run_date():
    """Get a recent model run date (48 hours ago to ensure availability)."""
    now = datetime.utcnow()
    # Go back 48 hours to ensure data is available
    recent = now - timedelta(hours=48)
    # Round to nearest 6-hour cycle
    cycle = (recent.hour // 6) * 6
    return recent.replace(hour=cycle, minute=0, second=0, microsecond=0)


class TestGFSDownload:
    """Test GFS data downloading."""
    
    def test_download_gfs_basic(self, downloader, recent_run_date):
        """Test basic GFS download with minimal parameters."""
        # Download just a few hours of data for speed
        ds = downloader.download_gfs(
            run_date=recent_run_date,
            cycle=0,
            forecast_hours=[0, 3, 6],
            bbox={
                "lat_min": 35.0,
                "lat_max": 40.0,
                "lon_min": -75.0,
                "lon_max": -70.0,
            }
        )
        
        # Verify dataset structure
        assert ds is not None
        assert "time" in ds.dims
        assert len(ds.time) == 3  # 0, 3, 6 hours
        
        # Verify we have key variables
        assert "ugrd10m" in ds.variables or "ugrdprs" in ds.variables
        assert "vgrd10m" in ds.variables or "vgrdprs" in ds.variables
        
        logger.info(f"GFS download successful: {list(ds.variables)}")
        logger.info(f"Time range: {ds.time.values[0]} to {ds.time.values[-1]}")
    
    def test_download_gfs_16day_forecast(self, downloader, recent_run_date):
        """Test downloading full 16-day GFS forecast."""
        # Download every 24 hours to keep test fast
        forecast_hours = list(range(0, 385, 24))
        
        ds = downloader.download_gfs(
            run_date=recent_run_date,
            cycle=0,
            forecast_hours=forecast_hours,
            bbox={
                "lat_min": 32.0,
                "lat_max": 42.0,
                "lon_min": -77.0,
                "lon_max": -64.0,
            }
        )
        
        # Verify we got extended forecast
        assert ds is not None
        assert len(ds.time) >= 10  # At least 10 days of data
        
        # Verify data extends to at least 10 days
        time_range = (ds.time.values[-1] - ds.time.values[0])
        days = time_range / 1e9 / 86400  # Convert nanoseconds to days
        assert days >= 10, f"Expected at least 10 days, got {days:.1f}"
        
        logger.info(f"16-day forecast downloaded: {len(ds.time)} timesteps")
        logger.info(f"Forecast extends {days:.1f} days")
    
    def test_gfs_has_required_variables(self, downloader, recent_run_date):
        """Test that GFS data contains required variables for analysis."""
        ds = downloader.download_gfs(
            run_date=recent_run_date,
            cycle=0,
            forecast_hours=[0, 6, 12],
            bbox={
                "lat_min": 35.0,
                "lat_max": 40.0,
                "lon_min": -75.0,
                "lon_max": -70.0,
            }
        )
        
        # Required for wind analysis
        assert "ugrd10m" in ds.variables, "Missing 10m U-wind"
        assert "vgrd10m" in ds.variables, "Missing 10m V-wind"
        
        # Required for cut-off low detection (if 3D data available)
        has_3d = "lev" in ds.dims
        if has_3d:
            assert any(v in ds.variables for v in ["absvprs", "vortprs"]), \
                "Missing vorticity data for cut-off detection"
        
        logger.info(f"All required variables present in GFS data")
    
    def test_gfs_data_values_realistic(self, downloader, recent_run_date):
        """Test that GFS data contains realistic values."""
        ds = downloader.download_gfs(
            run_date=recent_run_date,
            cycle=0,
            forecast_hours=[0, 6],
            bbox={
                "lat_min": 35.0,
                "lat_max": 40.0,
                "lon_min": -75.0,
                "lon_max": -70.0,
            }
        )
        
        # Check 10m winds are realistic (not NaN, reasonable range)
        u10 = ds["ugrd10m"]
        v10 = ds["vgrd10m"]
        
        # Should have data (not all NaN)
        assert not u10.isnull().all(), "All U-wind values are NaN"
        assert not v10.isnull().all(), "All V-wind values are NaN"
        
        # Wind speeds should be in reasonable range (-50 to 50 m/s)
        assert u10.min() > -50 and u10.max() < 50, "U-wind values out of range"
        assert v10.min() > -50 and v10.max() < 50, "V-wind values out of range"
        
        logger.info(f"GFS data values are realistic:")
        logger.info(f"  U-wind range: {float(u10.min()):.1f} to {float(u10.max()):.1f} m/s")
        logger.info(f"  V-wind range: {float(v10.min()):.1f} to {float(v10.max()):.1f} m/s")


class TestWW3Download:
    """Test WaveWatch III data downloading."""
    
    def test_download_ww3_basic(self, downloader, recent_run_date):
        """Test basic WW3 wave data download."""
        ds = downloader.download_ww3(
            run_date=recent_run_date,
            forecast_hours=[0, 3, 6],
            bbox={
                "lat_min": 35.0,
                "lat_max": 40.0,
                "lon_min": -75.0,
                "lon_max": -70.0,
            }
        )
        
        # Verify dataset structure
        assert ds is not None
        assert "time" in ds.dims
        
        # Should have wave height variable
        wave_vars = ["htsgwsfc", "swh", "hs", "significant_wave_height"]
        has_wave_height = any(v in ds.variables for v in wave_vars)
        assert has_wave_height, f"Missing wave height. Variables: {list(ds.variables)}"
        
        logger.info(f"WW3 download successful: {list(ds.variables)}")
    
    def test_ww3_data_values_realistic(self, downloader, recent_run_date):
        """Test that WW3 data contains realistic wave heights."""
        ds = downloader.download_ww3(
            run_date=recent_run_date,
            forecast_hours=[0, 6],
            bbox={
                "lat_min": 35.0,
                "lat_max": 40.0,
                "lon_min": -75.0,
                "lon_max": -70.0,
            }
        )
        
        # Find wave height variable
        wave_var = None
        for v in ["htsgwsfc", "swh", "hs", "significant_wave_height"]:
            if v in ds.variables:
                wave_var = v
                break
        
        assert wave_var is not None, "No wave height variable found"
        
        waves = ds[wave_var]
        
        # Should have data
        assert not waves.isnull().all(), "All wave heights are NaN"
        
        # Wave heights should be realistic (0 to 20m)
        assert waves.min() >= 0, "Negative wave heights"
        assert waves.max() < 20, "Unrealistic wave heights (>20m)"
        
        logger.info(f"WW3 wave heights realistic:")
        logger.info(f"  Range: {float(waves.min()):.1f} to {float(waves.max()):.1f} m")


class TestOffshoreRouteDownload:
    """Test downloading complete offshore route data."""
    
    def test_download_hampton_bermuda(self, downloader, recent_run_date):
        """Test downloading data for Hampton-Bermuda route."""
        data = downloader.download_offshore_route_data(
            route_name="hampton-bermuda",
            run_date=recent_run_date,
            forecast_days=5,  # Just 5 days for speed
        )
        
        # Should return dictionary with model data
        assert isinstance(data, dict)
        assert "gfs" in data
        assert "ww3" in data
        
        # At least GFS should be available
        assert data["gfs"] is not None, "GFS data download failed"
        
        # Verify GFS covers route area
        gfs = data["gfs"]
        assert gfs.lat.min() <= 32.3  # Bermuda
        assert gfs.lat.max() >= 37.0  # Hampton
        assert gfs.lon.min() <= -76.3  # Hampton
        assert gfs.lon.max() >= -64.8  # Bermuda
        
        logger.info("Hampton-Bermuda route data download successful")
        logger.info(f"  GFS: {gfs.dims}")
        if data["ww3"] is not None:
            logger.info(f"  WW3: {data['ww3'].dims}")
    
    def test_download_with_16day_forecast(self, downloader, recent_run_date):
        """Test downloading full 16-day forecast for route."""
        data = downloader.download_offshore_route_data(
            route_name="hampton-bermuda",
            run_date=recent_run_date,
            forecast_days=16,
        )
        
        assert data["gfs"] is not None
        
        # Verify forecast extends to at least 10 days
        gfs = data["gfs"]
        if len(gfs.time) > 1:
            time_range = (gfs.time.values[-1] - gfs.time.values[0])
            days = time_range / 1e9 / 86400
            assert days >= 10, f"Expected at least 10 days, got {days:.1f}"
            
            logger.info(f"16-day forecast: {len(gfs.time)} timesteps over {days:.1f} days")


class TestDataQuality:
    """Test data quality and consistency."""
    
    def test_gfs_time_consistency(self, downloader, recent_run_date):
        """Test that GFS time dimension is consistent and ordered."""
        ds = downloader.download_gfs(
            run_date=recent_run_date,
            cycle=0,
            forecast_hours=list(range(0, 49, 6)),  # 0 to 48 hours
            bbox={
                "lat_min": 35.0,
                "lat_max": 40.0,
                "lon_min": -75.0,
                "lon_max": -70.0,
            }
        )
        
        # Time should be monotonically increasing
        times = ds.time.values
        assert len(times) > 1
        
        time_diffs = [(times[i+1] - times[i]) for i in range(len(times)-1)]
        # All time steps should be positive (increasing)
        assert all(td > 0 for td in time_diffs), "Time not monotonically increasing"
        
        logger.info(f"Time dimension consistent: {len(times)} timesteps")
    
    def test_gfs_coordinates_coverage(self, downloader, recent_run_date):
        """Test that GFS provides adequate spatial coverage."""
        bbox = {
            "lat_min": 32.0,
            "lat_max": 42.0,
            "lon_min": -77.0,
            "lon_max": -64.0,
        }
        
        ds = downloader.download_gfs(
            run_date=recent_run_date,
            cycle=0,
            forecast_hours=[0],
            bbox=bbox,
        )
        
        # Should cover requested area
        assert ds.lat.min() <= bbox["lat_min"] + 1.0  # Allow 1 degree tolerance
        assert ds.lat.max() >= bbox["lat_max"] - 1.0
        assert ds.lon.min() <= bbox["lon_min"] + 1.0
        assert ds.lon.max() >= bbox["lon_max"] - 1.0
        
        # Should have reasonable resolution
        lat_spacing = float(abs(ds.lat[1] - ds.lat[0]))
        lon_spacing = float(abs(ds.lon[1] - ds.lon[0]))
        
        assert lat_spacing < 1.0, f"Latitude spacing too coarse: {lat_spacing}°"
        assert lon_spacing < 1.0, f"Longitude spacing too coarse: {lon_spacing}°"
        
        logger.info(f"Spatial coverage adequate:")
        logger.info(f"  Lat: {float(ds.lat.min()):.1f} to {float(ds.lat.max()):.1f}")
        logger.info(f"  Lon: {float(ds.lon.min()):.1f} to {float(ds.lon.max()):.1f}")
        logger.info(f"  Resolution: {lat_spacing:.3f}° x {lon_spacing:.3f}°")


class TestErrorHandling:
    """Test error handling for download failures."""
    
    def test_invalid_date_raises_error(self, downloader):
        """Test that invalid dates raise appropriate errors."""
        # Try to download data from far future (should fail)
        future_date = datetime.utcnow() + timedelta(days=10)
        
        with pytest.raises(Exception):
            downloader.download_gfs(
                run_date=future_date,
                cycle=0,
                forecast_hours=[0],
            )
    
    def test_invalid_bbox_raises_error(self, downloader, recent_run_date):
        """Test that invalid bounding boxes raise errors."""
        # Invalid bbox (lat_min > lat_max)
        with pytest.raises(Exception):
            downloader.download_gfs(
                run_date=recent_run_date,
                cycle=0,
                forecast_hours=[0],
                bbox={
                    "lat_min": 40.0,
                    "lat_max": 30.0,  # Invalid: min > max
                    "lon_min": -75.0,
                    "lon_max": -70.0,
                }
            )


# Mark integration tests to run separately
def pytest_configure(config):
    """Configure pytest to recognize integration marker."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires network)"
    )
