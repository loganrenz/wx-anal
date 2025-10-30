"""
Weather model data downloader for NOAA models.

This module provides functionality to download weather model data from
NOAA NOMADS servers via OPeNDAP, including GFS, GEFS, WW3, and HYCOM.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin

import requests
import xarray as xr
import numpy as np

logger = logging.getLogger(__name__)


class WeatherDownloader:
    """Download weather model data from NOAA sources."""

    # NOMADS OPeNDAP base URLs
    NOMADS_BASE = "https://nomads.ncep.noaa.gov/dods/"
    
    # Model-specific paths
    MODEL_PATHS = {
        "gfs": "gfs_0p25/gfs{date}/gfs_0p25_{cycle}z",
        "gefs": "gens_bc/gens{date}/gec00_{cycle}z",
        "ww3": "wave/nww3/{date}/nww3.{date}",
    }

    # Standard pressure levels for atmospheric data
    PRESSURE_LEVELS = [1000, 925, 850, 700, 500, 300, 250, 200, 100]

    def __init__(self, config: Optional[Any] = None):
        """
        Initialize weather downloader.

        Args:
            config: Configuration object with data_dir and timeout settings
        """
        self.config = config
        self.session = requests.Session()
        if config:
            self.session.timeout = config.timeout

    def _get_model_url(
        self, model: str, run_date: datetime, cycle: int = 0
    ) -> str:
        """
        Construct OPeNDAP URL for a model run.

        Args:
            model: Model name (gfs, gefs, ww3)
            run_date: Model run date
            cycle: Forecast cycle (0, 6, 12, 18)

        Returns:
            OPeNDAP URL string
        """
        date_str = run_date.strftime("%Y%m%d")
        cycle_str = f"{cycle:02d}"
        
        if model not in self.MODEL_PATHS:
            raise ValueError(f"Unknown model: {model}")
        
        path = self.MODEL_PATHS[model].format(date=date_str, cycle=cycle_str)
        return urljoin(self.NOMADS_BASE, path)

    def get_latest_run(self, model: str = "gfs") -> datetime:
        """
        Get the latest available model run time.

        Args:
            model: Model name

        Returns:
            Datetime of latest run
        """
        # NOAA typically has 6-hour delay for GFS
        now = datetime.utcnow()
        delay_hours = 6
        latest = now - timedelta(hours=delay_hours)
        
        # Round down to nearest cycle (0, 6, 12, 18 UTC)
        cycle = (latest.hour // 6) * 6
        return latest.replace(hour=cycle, minute=0, second=0, microsecond=0)

    def download_gfs(
        self,
        run_date: Optional[datetime] = None,
        cycle: int = 0,
        forecast_hours: Optional[List[int]] = None,
        levels: Optional[List[int]] = None,
        variables: Optional[List[str]] = None,
        bbox: Optional[Dict[str, float]] = None,
    ) -> xr.Dataset:
        """
        Download GFS model data via OPeNDAP.

        Args:
            run_date: Model run date (uses latest if None)
            cycle: Forecast cycle (0, 6, 12, 18)
            forecast_hours: List of forecast hours to download
            levels: Pressure levels to download (hPa)
            variables: List of variables to download
            bbox: Bounding box dict with keys: lat_min, lat_max, lon_min, lon_max

        Returns:
            xarray Dataset with requested data
        """
        if run_date is None:
            run_date = self.get_latest_run("gfs")

        if forecast_hours is None:
            forecast_hours = list(range(0, 121, 6))  # 0 to 120 hours, 6-hour steps

        if levels is None:
            levels = [1000, 850, 700, 500, 300]

        if variables is None:
            variables = [
                "hgtprs",  # Geopotential height
                "ugrdprs",  # U-component wind
                "vgrdprs",  # V-component wind
                "tmpprs",  # Temperature
                "vvelprs",  # Vertical velocity
                "absvprs",  # Absolute vorticity
                "ugrd10m",  # 10m U-wind
                "vgrd10m",  # 10m V-wind
                "pressfc",  # Surface pressure (MSLP)
            ]

        logger.info(f"Downloading GFS data for {run_date} cycle {cycle}")
        
        try:
            url = self._get_model_url("gfs", run_date, cycle)
            
            # Open dataset via OPeNDAP
            ds = xr.open_dataset(url, engine="netcdf4")
            
            # Select forecast times (limit to available data)
            if "time" in ds.dims:
                available_times = len(ds.time)
                valid_hours = [h for h in forecast_hours if h < available_times]
                if not valid_hours:
                    logger.warning(f"No valid forecast hours available. Requested up to {max(forecast_hours)}, but only {available_times} available")
                    valid_hours = list(range(min(available_times, 50)))  # Use first 50 or less
                ds = ds.isel(time=valid_hours)
            
            # Select pressure levels for 3D variables
            if "lev" in ds.dims and levels:
                ds = ds.sel(lev=levels)
            
            # Select spatial region
            if bbox:
                ds = ds.sel(
                    lat=slice(bbox["lat_min"], bbox["lat_max"]),
                    lon=slice(bbox["lon_min"], bbox["lon_max"])
                )
            
            # Select variables
            available_vars = [v for v in variables if v in ds.variables]
            if available_vars:
                ds = ds[available_vars]
            
            # Load data into memory
            ds = ds.load()
            
            logger.info(f"Successfully downloaded GFS data: {list(ds.variables)}")
            return ds
            
        except Exception as e:
            logger.error(f"Error downloading GFS data: {e}")
            raise

    def download_gefs(
        self,
        run_date: Optional[datetime] = None,
        cycle: int = 0,
        forecast_hours: Optional[List[int]] = None,
        members: Optional[List[int]] = None,
        variables: Optional[List[str]] = None,
        bbox: Optional[Dict[str, float]] = None,
    ) -> xr.Dataset:
        """
        Download GEFS ensemble model data.

        Args:
            run_date: Model run date
            cycle: Forecast cycle
            forecast_hours: List of forecast hours
            members: List of ensemble members (0-30, 0=control)
            variables: Variables to download
            bbox: Bounding box

        Returns:
            xarray Dataset with ensemble data
        """
        if run_date is None:
            run_date = self.get_latest_run("gefs")

        if forecast_hours is None:
            forecast_hours = list(range(0, 241, 12))  # 0 to 240 hours

        if members is None:
            members = list(range(0, 21))  # Control + 20 perturbed members

        logger.info(f"Downloading GEFS data for {run_date} cycle {cycle}")
        
        try:
            # For GEFS, we'd need to download multiple ensemble members
            # This is a simplified version - production code would handle all members
            url = self._get_model_url("gefs", run_date, cycle)
            ds = xr.open_dataset(url, engine="netcdf4")
            
            # Select forecast times
            if "time" in ds.dims:
                ds = ds.isel(time=forecast_hours)
            
            # Select spatial region
            if bbox:
                ds = ds.sel(
                    lat=slice(bbox["lat_min"], bbox["lat_max"]),
                    lon=slice(bbox["lon_min"], bbox["lon_max"])
                )
            
            ds = ds.load()
            logger.info(f"Successfully downloaded GEFS data")
            return ds
            
        except Exception as e:
            logger.error(f"Error downloading GEFS data: {e}")
            raise

    def download_ww3(
        self,
        run_date: Optional[datetime] = None,
        forecast_hours: Optional[List[int]] = None,
        bbox: Optional[Dict[str, float]] = None,
    ) -> xr.Dataset:
        """
        Download WaveWatch III (WW3) wave model data.

        Args:
            run_date: Model run date
            forecast_hours: List of forecast hours
            bbox: Bounding box

        Returns:
            xarray Dataset with wave data
        """
        if run_date is None:
            run_date = self.get_latest_run("ww3")

        if forecast_hours is None:
            forecast_hours = list(range(0, 181, 3))  # 0 to 180 hours, 3-hour steps

        logger.info(f"Downloading WW3 data for {run_date}")
        
        try:
            url = self._get_model_url("ww3", run_date, 0)
            ds = xr.open_dataset(url, engine="netcdf4")
            
            # Select forecast times
            if "time" in ds.dims:
                ds = ds.isel(time=forecast_hours)
            
            # Select spatial region
            if bbox:
                ds = ds.sel(
                    lat=slice(bbox["lat_min"], bbox["lat_max"]),
                    lon=slice(bbox["lon_min"], bbox["lon_max"])
                )
            
            ds = ds.load()
            logger.info(f"Successfully downloaded WW3 data")
            return ds
            
        except Exception as e:
            logger.error(f"Error downloading WW3 data: {e}")
            raise

    def download_offshore_route_data(
        self,
        route_name: str = "hampton-bermuda",
        run_date: Optional[datetime] = None,
        forecast_days: int = 10,
        use_mock_data: bool = False,
    ) -> Dict[str, xr.Dataset]:
        """
        Download comprehensive data for offshore route analysis.

        Args:
            route_name: Route identifier
            run_date: Model run date
            forecast_days: Number of forecast days
            use_mock_data: If True, generate mock data instead of downloading

        Returns:
            Dictionary with 'gfs', 'gefs', and 'ww3' datasets
        """
        if use_mock_data:
            logger.info("Using mock data for demonstration")
            from .mock_data import generate_mock_route_data
            if run_date is None:
                run_date = self.get_latest_run("gfs")
            return generate_mock_route_data(route_name, run_date, forecast_days)
        # Define route bounding boxes
        route_boxes = {
            "hampton-bermuda": {
                "lat_min": 32.0,
                "lat_max": 42.0,
                "lon_min": -77.0,
                "lon_max": -64.0,
            },
            "bermuda-antigua": {
                "lat_min": 17.0,
                "lat_max": 33.0,
                "lon_min": -65.0,
                "lon_max": -61.0,
            },
            "gulfstream": {
                "lat_min": 25.0,
                "lat_max": 45.0,
                "lon_min": -100.0,
                "lon_max": -50.0,
            },
        }

        bbox = route_boxes.get(route_name, route_boxes["gulfstream"])
        forecast_hours = list(range(0, forecast_days * 24 + 1, 6))

        data = {}
        
        try:
            # Download GFS
            data["gfs"] = self.download_gfs(
                run_date=run_date,
                forecast_hours=forecast_hours,
                bbox=bbox,
            )
        except Exception as e:
            logger.warning(f"Could not download GFS: {e}")
            data["gfs"] = None

        try:
            # Download GEFS
            data["gefs"] = self.download_gefs(
                run_date=run_date,
                forecast_hours=forecast_hours,
                bbox=bbox,
            )
        except Exception as e:
            logger.warning(f"Could not download GEFS: {e}")
            data["gefs"] = None

        try:
            # Download WW3
            data["ww3"] = self.download_ww3(
                run_date=run_date,
                forecast_hours=forecast_hours,
                bbox=bbox,
            )
        except Exception as e:
            logger.warning(f"Could not download WW3: {e}")
            data["ww3"] = None

        return data

    def save_to_cache(self, dataset: xr.Dataset, filename: str) -> Path:
        """
        Save dataset to cache directory.

        Args:
            dataset: xarray Dataset
            filename: Cache filename

        Returns:
            Path to saved file
        """
        if self.config:
            cache_path = self.config.data_dir / filename
        else:
            cache_path = Path("data") / filename
        
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        dataset.to_netcdf(cache_path)
        logger.info(f"Saved dataset to {cache_path}")
        return cache_path

    def load_from_cache(self, filename: str) -> Optional[xr.Dataset]:
        """
        Load dataset from cache.

        Args:
            filename: Cache filename

        Returns:
            Dataset if found, None otherwise
        """
        if self.config:
            cache_path = self.config.data_dir / filename
        else:
            cache_path = Path("data") / filename
        
        if cache_path.exists():
            logger.info(f"Loading dataset from {cache_path}")
            return xr.open_dataset(cache_path)
        return None
