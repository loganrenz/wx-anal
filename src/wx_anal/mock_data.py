"""
Mock weather data generator for testing and demonstration.

This module provides synthetic weather data that mimics the structure
and characteristics of real NOAA model data, useful for testing and
development when real data access is unavailable.
"""

import numpy as np
import xarray as xr
from datetime import datetime, timedelta
from typing import Optional, Dict, List


def generate_mock_gfs(
    start_time: datetime,
    forecast_hours: List[int],
    bbox: Dict[str, float],
    levels: Optional[List[int]] = None,
) -> xr.Dataset:
    """
    Generate mock GFS data with realistic structure.
    
    Args:
        start_time: Model initialization time
        forecast_hours: Forecast hours to generate
        bbox: Bounding box with lat_min, lat_max, lon_min, lon_max
        levels: Pressure levels in hPa
        
    Returns:
        xarray Dataset with mock GFS data
    """
    if levels is None:
        levels = [1000, 850, 700, 500, 300]
    
    # Create coordinate arrays
    lats = np.arange(bbox["lat_min"], bbox["lat_max"] + 0.25, 0.25)
    lons = np.arange(bbox["lon_min"], bbox["lon_max"] + 0.25, 0.25)
    times = [start_time + timedelta(hours=h) for h in forecast_hours]
    
    # Create realistic-looking data with some spatial and temporal variation
    nlat, nlon, ntime, nlev = len(lats), len(lons), len(times), len(levels)
    
    # Generate base patterns
    lat_mesh, lon_mesh = np.meshgrid(lats, lons, indexing='ij')
    
    # Create a mock cut-off low over Louisiana (25-34N, 88-96W)
    cutoff_lat, cutoff_lon = 29.5, -92.0
    cutoff_strength = 0.0
    
    # Check if our bbox includes Louisiana region (or is close enough)
    # Be more lenient to show cut-off low in Hampton-Bermuda route
    if (bbox["lat_min"] <= 38 and bbox["lat_max"] >= 25 and 
        bbox["lon_min"] <= -75):
        cutoff_strength = 1.0
    
    data_vars = {}
    
    # Geopotential height at 500 hPa
    hgt = np.zeros((ntime, nlev, nlat, nlon))
    for t in range(ntime):
        for k, lev in enumerate(levels):
            # Base height decreases with pressure
            base = 10000 - (lev * 8)
            
            # Add wave pattern (trough/ridge)
            wave = 200 * np.sin(lon_mesh * np.pi / 30)
            
            # Add cut-off low signature at 500 hPa
            if lev == 500 and cutoff_strength > 0:
                dist = np.sqrt((lat_mesh - cutoff_lat)**2 + (lon_mesh - cutoff_lon)**2)
                cutoff = -300 * np.exp(-dist**2 / 20) * cutoff_strength * (1 - t / ntime)
                hgt[t, k] = base + wave + cutoff
            else:
                hgt[t, k] = base + wave
    
    data_vars["hgtprs"] = (["time", "lev", "lat", "lon"], hgt)
    
    # Absolute vorticity at 500 hPa (for cut-off low detection)
    vort = np.zeros((ntime, nlev, nlat, nlon))
    for t in range(ntime):
        for k, lev in enumerate(levels):
            # Planetary vorticity (Coriolis)
            f = 2 * 7.2921e-5 * np.sin(np.radians(lat_mesh))
            
            # Add cut-off low vorticity signature
            if lev == 500 and cutoff_strength > 0:
                dist = np.sqrt((lat_mesh - cutoff_lat)**2 + (lon_mesh - cutoff_lon)**2)
                # Peak vorticity of ~10e-5 s^-1 (above detection threshold)
                cutoff_vort = 12e-5 * np.exp(-dist**2 / 15) * cutoff_strength * (1 - t * 0.7 / ntime)
                vort[t, k] = f + cutoff_vort
            else:
                vort[t, k] = f + 2e-5 * np.random.randn(nlat, nlon)
    
    data_vars["absvprs"] = (["time", "lev", "lat", "lon"], vort)
    
    # U and V wind components at pressure levels
    u = np.zeros((ntime, nlev, nlat, nlon))
    v = np.zeros((ntime, nlev, nlat, nlon))
    
    for t in range(ntime):
        for k, lev in enumerate(levels):
            # Westerlies strengthen with height
            base_u = 10 + (1000 - lev) * 0.03
            
            # Add jet stream at 300 hPa
            if lev == 300:
                # Strong westerlies around 40N
                jet_strength = 40 * np.exp(-((lat_mesh - 40)**2) / 50)
                u[t, k] = base_u + jet_strength + 5 * np.random.randn(nlat, nlon)
            else:
                u[t, k] = base_u + 5 * np.random.randn(nlat, nlon)
            
            # Meridional component (north-south)
            v[t, k] = 2 + 3 * np.random.randn(nlat, nlon)
    
    data_vars["ugrdprs"] = (["time", "lev", "lat", "lon"], u)
    data_vars["vgrdprs"] = (["time", "lev", "lat", "lon"], v)
    
    # 10m winds (surface)
    u10 = np.zeros((ntime, nlat, nlon))
    v10 = np.zeros((ntime, nlat, nlon))
    
    for t in range(ntime):
        # Realistic surface winds (15-25 kt typical, up to 35 kt in bad weather)
        base_wind = 7.5 + 2.5 * (t / ntime)  # Increasing wind over time
        
        # Add some variation
        u10[t] = base_wind + 5 * np.random.randn(nlat, nlon)
        v10[t] = 3 + 4 * np.random.randn(nlat, nlon)
    
    data_vars["ugrd10m"] = (["time", "lat", "lon"], u10)
    data_vars["vgrd10m"] = (["time", "lat", "lon"], v10)
    
    # Surface pressure (MSLP)
    pres = np.zeros((ntime, nlat, nlon))
    for t in range(ntime):
        # Standard pressure with some variation
        pres[t] = 101325 + 500 * np.sin(lon_mesh * np.pi / 40) + 200 * np.random.randn(nlat, nlon)
    
    data_vars["pressfc"] = (["time", "lat", "lon"], pres)
    
    # Create dataset
    ds = xr.Dataset(
        data_vars=data_vars,
        coords={
            "time": times,
            "lev": levels,
            "lat": lats,
            "lon": lons,
        },
        attrs={
            "title": "Mock GFS Data",
            "source": "wx-anal synthetic data generator",
            "initialization_time": start_time.isoformat(),
        }
    )
    
    return ds


def generate_mock_ww3(
    start_time: datetime,
    forecast_hours: List[int],
    bbox: Dict[str, float],
) -> xr.Dataset:
    """
    Generate mock WaveWatch III data.
    
    Args:
        start_time: Model initialization time
        forecast_hours: Forecast hours to generate
        bbox: Bounding box
        
    Returns:
        xarray Dataset with mock wave data
    """
    # Create coordinates
    lats = np.arange(bbox["lat_min"], bbox["lat_max"] + 0.5, 0.5)
    lons = np.arange(bbox["lon_min"], bbox["lon_max"] + 0.5, 0.5)
    times = [start_time + timedelta(hours=h) for h in forecast_hours]
    
    nlat, nlon, ntime = len(lats), len(lons), len(times)
    
    # Generate wave heights
    lat_mesh, lon_mesh = np.meshgrid(lats, lons, indexing='ij')
    
    # Significant wave height
    hs = np.zeros((ntime, nlat, nlon))
    
    for t in range(ntime):
        # Base wave height (1-3m typical)
        base = 1.5 + 0.5 * (t / ntime)
        
        # Add spatial variation (higher in Gulf Stream)
        # Gulf Stream roughly at 70-75W
        gulf_stream = np.exp(-((lons + 72.5)**2) / 10)
        
        for i in range(nlat):
            hs[t, i, :] = base + 1.0 * gulf_stream + 0.5 * np.random.randn(nlon)
    
    # Ensure no negative waves
    hs = np.maximum(hs, 0.3)
    
    # Wave period
    period = 6 + 2 * (hs / 3.0)  # Longer periods with higher waves
    
    ds = xr.Dataset(
        {
            "htsgwsfc": (["time", "lat", "lon"], hs),
            "perpwsfc": (["time", "lat", "lon"], period),
        },
        coords={
            "time": times,
            "lat": lats,
            "lon": lons,
        },
        attrs={
            "title": "Mock WW3 Data",
            "source": "wx-anal synthetic data generator",
        }
    )
    
    return ds


def generate_mock_route_data(
    route_name: str,
    start_time: datetime,
    forecast_days: int = 10,
) -> Dict[str, xr.Dataset]:
    """
    Generate complete mock data set for route analysis.
    
    Args:
        route_name: Route identifier
        start_time: Model initialization time
        forecast_days: Number of forecast days
        
    Returns:
        Dictionary with 'gfs', 'gefs', and 'ww3' datasets
    """
    # Define route bounding boxes
    route_boxes = {
        "hampton-bermuda": {
            "lat_min": 32.0,
            "lat_max": 42.0,
            "lon_min": -77.0,
            "lon_max": -64.0,
        },
        "hampton-antigua": {
            "lat_min": 17.0,
            "lat_max": 42.0,
            "lon_min": -77.0,
            "lon_max": -61.0,
        },
        "bermuda-antigua": {
            "lat_min": 17.0,
            "lat_max": 33.0,
            "lon_min": -65.0,
            "lon_max": -61.0,
        },
        "beaufort-bermuda": {
            "lat_min": 32.0,
            "lat_max": 38.0,
            "lon_min": -77.0,
            "lon_max": -64.0,
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
    
    # Generate GFS
    gfs = generate_mock_gfs(
        start_time,
        forecast_hours,
        bbox,
        levels=[1000, 850, 700, 500, 300],
    )
    
    # Generate WW3
    ww3 = generate_mock_ww3(
        start_time,
        forecast_hours,
        bbox,
    )
    
    return {
        "gfs": gfs,
        "gefs": None,  # GEFS not implemented yet
        "ww3": ww3,
    }
