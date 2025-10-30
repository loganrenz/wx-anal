"""
Weather feature analyzer for detecting and tracking meteorological features.

This module provides functionality to detect cut-off lows, jet streams,
and other weather features relevant to offshore route planning.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

import numpy as np
import xarray as xr
from scipy import ndimage
from scipy.spatial import distance

logger = logging.getLogger(__name__)


class WeatherAnalyzer:
    """Analyze weather features from model data."""

    # Thresholds for feature detection
    CUTOFF_VORTICITY_THRESHOLD = 8e-5  # s^-1 for 500 hPa
    JET_WIND_THRESHOLD = 30.0  # m/s for 300 hPa
    STRONG_WIND_THRESHOLD = 15.0  # m/s (~30 kt) at 10m
    HIGH_WAVE_THRESHOLD = 3.0  # meters significant wave height
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize weather analyzer.

        Args:
            config: Configuration object
        """
        self.config = config

    def detect_cutoff_low(
        self,
        dataset: xr.Dataset,
        bbox: Optional[Dict[str, float]] = None,
        vorticity_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Detect cut-off upper-level low from 500 hPa data.

        A cut-off low is characterized by:
        - Positive vorticity maximum at 500 hPa
        - Closed geopotential height contours
        - Isolated from main jet stream

        Args:
            dataset: xarray Dataset with 500 hPa vorticity and height
            bbox: Bounding box dict for search region (Louisiana: 25-34°N, 88-96°W)
            vorticity_threshold: Minimum vorticity for detection

        Returns:
            Dictionary with detection results
        """
        if vorticity_threshold is None:
            vorticity_threshold = self.CUTOFF_VORTICITY_THRESHOLD

        if bbox is None:
            # Default Louisiana box
            bbox = {
                "lat_min": 25.0,
                "lat_max": 34.0,
                "lon_min": -96.0,
                "lon_max": -88.0,
            }

        results = {
            "detected": False,
            "times": [],
            "locations": [],
            "max_vorticity": [],
            "centroids": [],
        }

        try:
            # Extract 500 hPa vorticity
            if "absvprs" in dataset.variables:
                vort = dataset["absvprs"]
                if "lev" in vort.dims:
                    vort = vort.sel(lev=500, method="nearest")
            else:
                logger.warning("Vorticity data not available")
                return results

            # Select region
            vort_region = vort.sel(
                lat=slice(bbox["lat_min"], bbox["lat_max"]),
                lon=slice(bbox["lon_min"], bbox["lon_max"])
            )

            # Iterate over time steps
            for t_idx, time_val in enumerate(vort_region.time.values):
                vort_t = vort_region.isel(time=t_idx)
                
                # Find vorticity maxima
                if vort_t.size == 0:
                    continue
                max_vort = float(vort_t.max())
                
                if max_vort > vorticity_threshold:
                    results["detected"] = True
                    results["times"].append(time_val)
                    results["max_vorticity"].append(max_vort)
                    
                    # Find centroid of high vorticity region
                    mask = vort_t.values > vorticity_threshold
                    if mask.any():
                        labeled, num_features = ndimage.label(mask)
                        if num_features > 0:
                            # Get largest feature
                            sizes = ndimage.sum(mask, labeled, range(1, num_features + 1))
                            max_label = np.argmax(sizes) + 1
                            
                            # Calculate centroid
                            centroid = ndimage.center_of_mass(
                                vort_t.values, labeled, max_label
                            )
                            
                            # Convert to lat/lon
                            lat_idx, lon_idx = centroid
                            lat = float(vort_t.lat.values[int(lat_idx)])
                            lon = float(vort_t.lon.values[int(lon_idx)])
                            
                            results["centroids"].append({"lat": lat, "lon": lon})
                            results["locations"].append((lat, lon))

            logger.info(
                f"Cut-off low detection: {len(results['times'])} timesteps with vorticity > {vorticity_threshold}"
            )

        except Exception as e:
            logger.error(f"Error detecting cut-off low: {e}")

        return results

    def track_cutoff_reattachment(
        self,
        dataset: xr.Dataset,
        cutoff_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Track whether cut-off low reattaches to main jet stream.

        Reattachment is indicated by:
        - Eastward motion of vorticity centroid toward 75-70°W
        - Strengthening of 300 hPa winds over same latitude band

        Args:
            dataset: xarray Dataset with 300 hPa winds
            cutoff_results: Results from detect_cutoff_low

        Returns:
            Dictionary with tracking results
        """
        results = {
            "reattachment_detected": False,
            "eastward_motion": 0.0,  # degrees longitude
            "jet_strengthening": False,
            "timeline": [],
        }

        if not cutoff_results["detected"] or len(cutoff_results["centroids"]) < 2:
            return results

        try:
            # Calculate eastward motion
            centroids = cutoff_results["centroids"]
            start_lon = centroids[0]["lon"]
            end_lon = centroids[-1]["lon"]
            eastward_motion = end_lon - start_lon
            results["eastward_motion"] = eastward_motion

            # Check if moving toward reattachment zone (75-70°W)
            if eastward_motion > 5.0 and end_lon > -80.0:
                results["reattachment_detected"] = True

            # Check 300 hPa wind strengthening
            if "ugrdprs" in dataset.variables and "vgrdprs" in dataset.variables:
                u = dataset["ugrdprs"].sel(lev=300, method="nearest")
                v = dataset["vgrdprs"].sel(lev=300, method="nearest")
                windspeed = np.sqrt(u**2 + v**2)

                # Average over latitude band of cutoff
                avg_lat = np.mean([c["lat"] for c in centroids])
                lat_band = windspeed.sel(
                    lat=slice(avg_lat - 5, avg_lat + 5),
                    lon=slice(-85.0, -70.0)
                )

                # Check for strengthening over time
                mean_winds = lat_band.mean(dim=["lat", "lon"])
                if len(mean_winds) > 1:
                    wind_trend = float(mean_winds[-1]) - float(mean_winds[0])
                    if wind_trend > 5.0 and float(mean_winds[-1]) > self.JET_WIND_THRESHOLD:
                        results["jet_strengthening"] = True

            logger.info(
                f"Reattachment tracking: eastward={eastward_motion:.1f}°, "
                f"jet_strengthening={results['jet_strengthening']}"
            )

        except Exception as e:
            logger.error(f"Error tracking reattachment: {e}")

        return results

    def analyze_route_winds(
        self,
        dataset: xr.Dataset,
        route_points: List[Tuple[float, float]],
        wind_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Analyze wind conditions along a route.

        Args:
            dataset: xarray Dataset with 10m winds
            route_points: List of (lat, lon) waypoints
            wind_threshold: Wind speed threshold in m/s

        Returns:
            Dictionary with wind analysis results
        """
        if wind_threshold is None:
            wind_threshold = self.STRONG_WIND_THRESHOLD

        results = {
            "max_wind": 0.0,
            "mean_wind": 0.0,
            "percent_above_threshold": 0.0,
            "hazard_periods": [],
            "timeline": [],
        }

        try:
            # Extract 10m winds
            if "ugrd10m" in dataset.variables and "vgrd10m" in dataset.variables:
                u10 = dataset["ugrd10m"]
                v10 = dataset["vgrd10m"]
                windspeed = np.sqrt(u10**2 + v10**2)
            else:
                logger.warning("10m wind data not available")
                return results

            # Sample along route
            route_winds = []
            for lat, lon in route_points:
                try:
                    # Find nearest grid point
                    ws = windspeed.sel(lat=lat, lon=lon, method="nearest")
                    route_winds.append(ws.values)
                except (KeyError, ValueError) as e:
                    # Point outside data range, skip it
                    logger.debug(f"Skipping point ({lat}, {lon}): {e}")
                    continue
            
            if not route_winds:
                logger.warning("No valid route points found in dataset")
                return results

            route_winds = np.array(route_winds)
            
            # Calculate statistics
            results["max_wind"] = float(np.max(route_winds))
            results["mean_wind"] = float(np.mean(route_winds))
            
            above_threshold = route_winds > wind_threshold
            results["percent_above_threshold"] = float(
                100.0 * np.sum(above_threshold) / above_threshold.size
            )

            # Identify hazard periods (>6 consecutive hours above threshold)
            if "time" in windspeed.dims:
                for t_idx in range(len(windspeed.time)):
                    ws_t = windspeed.isel(time=t_idx)
                    max_wind_t = float(
                        np.max([
                            ws_t.sel(lat=lat, lon=lon, method="nearest").values
                            for lat, lon in route_points
                        ])
                    )
                    
                    results["timeline"].append({
                        "time": windspeed.time.values[t_idx],
                        "max_wind": max_wind_t,
                        "above_threshold": max_wind_t > wind_threshold,
                    })

            logger.info(
                f"Route wind analysis: max={results['max_wind']:.1f} m/s, "
                f"{results['percent_above_threshold']:.1f}% above threshold"
            )

        except Exception as e:
            logger.error(f"Error analyzing route winds: {e}")

        return results

    def analyze_route_waves(
        self,
        ww3_dataset: xr.Dataset,
        route_points: List[Tuple[float, float]],
        wave_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Analyze wave conditions along a route.

        Args:
            ww3_dataset: xarray Dataset with WW3 wave data
            route_points: List of (lat, lon) waypoints
            wave_threshold: Significant wave height threshold in meters

        Returns:
            Dictionary with wave analysis results
        """
        if wave_threshold is None:
            wave_threshold = self.HIGH_WAVE_THRESHOLD

        results = {
            "max_wave_height": 0.0,
            "mean_wave_height": 0.0,
            "percent_above_threshold": 0.0,
            "timeline": [],
        }

        try:
            # Extract significant wave height (variable name varies)
            hs = None
            for var_name in ["htsgwsfc", "swh", "hs", "significant_wave_height"]:
                if var_name in ww3_dataset.variables:
                    hs = ww3_dataset[var_name]
                    break

            if hs is None:
                logger.warning("Wave height data not available")
                return results

            # Sample along route
            route_waves = []
            for lat, lon in route_points:
                try:
                    hw = hs.sel(lat=lat, lon=lon, method="nearest")
                    route_waves.append(hw.values)
                except (KeyError, ValueError) as e:
                    # Point outside data range, skip it
                    logger.debug(f"Skipping point ({lat}, {lon}): {e}")
                    continue
            
            if not route_waves:
                logger.warning("No valid route points found in wave dataset")
                return results

            route_waves = np.array(route_waves)
            
            # Calculate statistics
            results["max_wave_height"] = float(np.max(route_waves))
            results["mean_wave_height"] = float(np.mean(route_waves))
            
            above_threshold = route_waves > wave_threshold
            results["percent_above_threshold"] = float(
                100.0 * np.sum(above_threshold) / above_threshold.size
            )

            # Build timeline
            if "time" in hs.dims:
                for t_idx in range(len(hs.time)):
                    hs_t = hs.isel(time=t_idx)
                    max_wave_t = float(
                        np.max([
                            hs_t.sel(lat=lat, lon=lon, method="nearest").values
                            for lat, lon in route_points
                        ])
                    )
                    
                    results["timeline"].append({
                        "time": hs.time.values[t_idx],
                        "max_wave": max_wave_t,
                        "above_threshold": max_wave_t > wave_threshold,
                    })

            logger.info(
                f"Route wave analysis: max={results['max_wave_height']:.1f} m, "
                f"{results['percent_above_threshold']:.1f}% above threshold"
            )

        except Exception as e:
            logger.error(f"Error analyzing route waves: {e}")

        return results

    def score_route_risk(
        self,
        wind_results: Dict[str, Any],
        wave_results: Dict[str, Any],
        cutoff_results: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate overall risk score for a route.

        Risk factors:
        - High winds (>30 kt / 15 m/s)
        - High seas (>3 m)
        - Presence of cut-off low
        - Percentage of time above thresholds

        Args:
            wind_results: Results from analyze_route_winds
            wave_results: Results from analyze_route_waves
            cutoff_results: Results from detect_cutoff_low

        Returns:
            Dictionary with risk assessment
        """
        risk_score = 0.0
        risk_factors = []

        # Wind risk (0-40 points)
        wind_risk = min(40.0, wind_results["percent_above_threshold"] * 0.4)
        risk_score += wind_risk
        if wind_risk > 20:
            risk_factors.append(f"High wind risk ({wind_risk:.0f}/40)")

        # Wave risk (0-40 points)
        wave_risk = min(40.0, wave_results["percent_above_threshold"] * 0.4)
        risk_score += wave_risk
        if wave_risk > 20:
            risk_factors.append(f"High wave risk ({wave_risk:.0f}/40)")

        # Cut-off low risk (0-20 points)
        cutoff_risk = 0.0
        if cutoff_results and cutoff_results["detected"]:
            cutoff_risk = 20.0
            risk_factors.append("Cut-off low detected")
        risk_score += cutoff_risk

        # Normalize to 0-100 scale
        risk_score = min(100.0, risk_score)

        # Categorize risk
        if risk_score < 30:
            risk_level = "LOW"
        elif risk_score < 60:
            risk_level = "MODERATE"
        else:
            risk_level = "HIGH"

        results = {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "wind_component": wind_risk,
            "wave_component": wave_risk,
            "cutoff_component": cutoff_risk,
            "recommendation": self._get_recommendation(risk_level, risk_factors),
        }

        logger.info(
            f"Route risk assessment: {risk_level} ({risk_score:.1f}/100)"
        )

        return results

    def _get_recommendation(
        self, risk_level: str, risk_factors: List[str]
    ) -> str:
        """Generate sailing recommendation based on risk assessment."""
        if risk_level == "LOW":
            return "Conditions favorable for departure. Monitor forecasts for changes."
        elif risk_level == "MODERATE":
            return "Conditions marginal. Consider delaying departure or preparing for challenging conditions."
        else:
            return "Conditions hazardous. Strongly recommend delaying departure until conditions improve."

    def analyze_ensemble_probability(
        self,
        gefs_dataset: xr.Dataset,
        route_points: List[Tuple[float, float]],
        threshold: float,
        variable: str = "wind",
    ) -> Dict[str, Any]:
        """
        Calculate ensemble probability of exceeding threshold.

        Args:
            gefs_dataset: GEFS ensemble dataset
            route_points: Route waypoints
            threshold: Threshold value
            variable: Variable to analyze ('wind' or 'wave')

        Returns:
            Dictionary with probability analysis
        """
        results = {
            "mean_probability": 0.0,
            "max_probability": 0.0,
            "timeline": [],
        }

        try:
            # This would need proper GEFS ensemble handling
            # For now, provide a framework
            logger.info("Ensemble probability analysis not fully implemented")
            
        except Exception as e:
            logger.error(f"Error in ensemble analysis: {e}")

        return results
