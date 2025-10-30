"""
Route planning and analysis for offshore passages.

This module handles route-specific planning, including waypoint generation,
vessel speed calculations, and departure window analysis.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

import numpy as np
from shapely.geometry import LineString, Point
from scipy.interpolate import interp1d

logger = logging.getLogger(__name__)


class VesselSpeed(Enum):
    """Vessel speed categories based on typical performance."""
    
    SLOW = "slow"  # 5-5.5 knots, 120-130 nm/day
    TYPICAL = "typical"  # 6-6.5 knots, 140-160 nm/day
    FAST = "fast"  # 7-8.5 knots, 170-200 nm/day


@dataclass
class Vessel:
    """Vessel characteristics for route planning."""
    
    name: str
    speed_category: VesselSpeed
    avg_speed_knots: float
    max_wind_tolerance: float = 40.0  # knots
    max_wave_tolerance: float = 4.0  # meters
    motor_speed: Optional[float] = None  # knots when motoring
    
    @property
    def nm_per_day(self) -> float:
        """Calculate nautical miles per day."""
        return self.avg_speed_knots * 24
    
    @classmethod
    def slow_boat(cls, name: str = "SlowBoat") -> "Vessel":
        """Create a slow boat profile (5-5.5 knots, 120-130 nm/day)."""
        return cls(
            name=name,
            speed_category=VesselSpeed.SLOW,
            avg_speed_knots=5.25,
            motor_speed=5.0,
        )
    
    @classmethod
    def typical_boat(cls, name: str = "TypicalBoat") -> "Vessel":
        """Create a typical cruising boat profile (6-6.5 knots, 140-160 nm/day)."""
        return cls(
            name=name,
            speed_category=VesselSpeed.TYPICAL,
            avg_speed_knots=6.25,
            motor_speed=6.0,
        )
    
    @classmethod
    def fast_boat(cls, name: str = "FastBoat") -> "Vessel":
        """Create a fast boat profile (7-8.5 knots, 170-200 nm/day)."""
        return cls(
            name=name,
            speed_category=VesselSpeed.FAST,
            avg_speed_knots=7.75,
            motor_speed=7.0,
        )


class Route:
    """Represents an offshore sailing route with waypoints."""
    
    # Pre-defined routes
    ROUTES = {
        "hampton-bermuda": {
            "start": (37.0, -76.3),  # Hampton/Chesapeake Bay
            "end": (32.3, -64.8),  # Bermuda
            "description": "Hampton Roads to Bermuda",
            "distance_nm": 640,
        },
        "hampton-antigua": {
            "start": (37.0, -76.3),  # Hampton
            "end": (17.0, -61.8),  # Antigua
            "description": "Hampton Roads to Antigua",
            "distance_nm": 1500,
        },
        "bermuda-antigua": {
            "start": (32.3, -64.8),  # Bermuda
            "end": (17.0, -61.8),  # Antigua
            "description": "Bermuda to Antigua",
            "distance_nm": 850,
        },
        "beaufort-bermuda": {
            "start": (34.7, -76.7),  # Beaufort, NC
            "end": (32.3, -64.8),  # Bermuda
            "description": "Beaufort to Bermuda",
            "distance_nm": 580,
        },
    }
    
    def __init__(
        self,
        name: str,
        waypoints: Optional[List[Tuple[float, float]]] = None,
        vessel: Optional[Vessel] = None,
    ):
        """
        Initialize route.
        
        Args:
            name: Route name or identifier
            waypoints: List of (lat, lon) waypoints
            vessel: Vessel characteristics
        """
        self.name = name
        self.vessel = vessel or Vessel.typical_boat()
        self.variant_name = "direct"  # Default variant
        
        if waypoints:
            self.waypoints = waypoints
        elif name in self.ROUTES:
            route_def = self.ROUTES[name]
            self.waypoints = [route_def["start"], route_def["end"]]
            self.distance_nm = route_def["distance_nm"]
        else:
            raise ValueError(f"Unknown route: {name}. Provide waypoints or use a predefined route.")
        
        self.line = LineString([(lon, lat) for lat, lon in self.waypoints])
    
    def interpolate_waypoints(self, num_points: int = 50) -> List[Tuple[float, float]]:
        """
        Generate interpolated waypoints along the route.
        
        Args:
            num_points: Number of points to generate
            
        Returns:
            List of (lat, lon) waypoints
        """
        # Create parameterized curve
        distances = [0]
        for i in range(1, len(self.waypoints)):
            lat1, lon1 = self.waypoints[i-1]
            lat2, lon2 = self.waypoints[i]
            dist = self._haversine_distance(lat1, lon1, lat2, lon2)
            distances.append(distances[-1] + dist)
        
        # Normalize distances
        distances = np.array(distances)
        distances = distances / distances[-1]
        
        # Interpolate
        lats = [wp[0] for wp in self.waypoints]
        lons = [wp[1] for wp in self.waypoints]
        
        f_lat = interp1d(distances, lats, kind='linear')
        f_lon = interp1d(distances, lons, kind='linear')
        
        t = np.linspace(0, 1, num_points)
        interpolated = [(f_lat(ti), f_lon(ti)) for ti in t]
        
        return interpolated
    
    def get_waypoints_by_time(
        self,
        departure_time: datetime,
        time_step_hours: int = 6,
    ) -> List[Dict[str, Any]]:
        """
        Calculate vessel position at regular time intervals.
        
        Args:
            departure_time: Departure datetime
            time_step_hours: Time interval in hours
            
        Returns:
            List of dicts with time, lat, lon, distance_traveled
        """
        total_distance_nm = self._calculate_total_distance()
        total_time_hours = total_distance_nm / self.vessel.avg_speed_knots
        
        num_steps = int(total_time_hours / time_step_hours) + 1
        waypoints_timed = []
        
        for step in range(num_steps):
            elapsed_hours = step * time_step_hours
            if elapsed_hours > total_time_hours:
                elapsed_hours = total_time_hours
            
            distance_traveled = elapsed_hours * self.vessel.avg_speed_knots
            fraction = distance_traveled / total_distance_nm
            
            # Get position at this fraction
            position = self._position_at_fraction(fraction)
            
            waypoints_timed.append({
                "time": departure_time + timedelta(hours=elapsed_hours),
                "lat": position[0],
                "lon": position[1],
                "distance_nm": distance_traveled,
                "elapsed_hours": elapsed_hours,
            })
            
            if elapsed_hours >= total_time_hours:
                break
        
        return waypoints_timed
    
    def estimate_arrival_time(self, departure_time: datetime) -> datetime:
        """
        Estimate arrival time based on vessel speed.
        
        Args:
            departure_time: Departure datetime
            
        Returns:
            Estimated arrival datetime
        """
        total_distance_nm = self._calculate_total_distance()
        total_hours = total_distance_nm / self.vessel.avg_speed_knots
        return departure_time + timedelta(hours=total_hours)
    
    def get_distance(self) -> float:
        """
        Get total route distance in nautical miles.
        
        Returns:
            Distance in nautical miles
        """
        return self._calculate_total_distance()
    
    def _calculate_total_distance(self) -> float:
        """Calculate total route distance in nautical miles."""
        if hasattr(self, 'distance_nm'):
            return self.distance_nm
        
        total = 0.0
        for i in range(1, len(self.waypoints)):
            lat1, lon1 = self.waypoints[i-1]
            lat2, lon2 = self.waypoints[i]
            total += self._haversine_distance(lat1, lon1, lat2, lon2)
        
        return total
    
    def _position_at_fraction(self, fraction: float) -> Tuple[float, float]:
        """Get lat/lon at fractional distance along route."""
        if fraction <= 0:
            return self.waypoints[0]
        if fraction >= 1:
            return self.waypoints[-1]
        
        # Calculate cumulative distances
        distances = [0]
        for i in range(1, len(self.waypoints)):
            lat1, lon1 = self.waypoints[i-1]
            lat2, lon2 = self.waypoints[i]
            dist = self._haversine_distance(lat1, lon1, lat2, lon2)
            distances.append(distances[-1] + dist)
        
        total_distance = distances[-1]
        target_distance = fraction * total_distance
        
        # Find segment containing target distance
        for i in range(1, len(distances)):
            if target_distance <= distances[i]:
                # Interpolate within this segment
                segment_fraction = (target_distance - distances[i-1]) / (distances[i] - distances[i-1])
                lat1, lon1 = self.waypoints[i-1]
                lat2, lon2 = self.waypoints[i]
                
                lat = lat1 + segment_fraction * (lat2 - lat1)
                lon = lon1 + segment_fraction * (lon2 - lon1)
                return (lat, lon)
        
        return self.waypoints[-1]
    
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points in nautical miles.
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            Distance in nautical miles
        """
        R = 3440.065  # Earth radius in nautical miles
        
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        return R * c


class GulfStream:
    """Gulf Stream analysis and routing."""
    
    @staticmethod
    def get_crossing_recommendation(
        departure_port: str,
        conditions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Get Gulf Stream crossing recommendations.
        
        Args:
            departure_port: Departure port (hampton, beaufort, etc.)
            conditions: Weather/wave conditions
            
        Returns:
            Dictionary with crossing recommendations
        """
        recommendations = {
            "recommended_crossing_lat": None,
            "recommended_exit_lat": None,
            "avoid_before": None,
            "rationale": [],
        }
        
        # Hampton departures
        if departure_port.lower() in ["hampton", "chesapeake"]:
            # Check wind/wave conditions
            if conditions.get("wind_speed", 0) > 25:
                recommendations["recommended_crossing_lat"] = 36.5
                recommendations["recommended_exit_lat"] = 36.0
                recommendations["avoid_before"] = "dawn Saturday"
                recommendations["rationale"].append(
                    "Strong winds - cross Gulf Stream south of Chesapeake Bay latitude"
                )
            else:
                recommendations["recommended_crossing_lat"] = 37.0
                recommendations["recommended_exit_lat"] = 36.5
                recommendations["rationale"].append(
                    "Moderate conditions - can cross at or near departure latitude"
                )
        
        # Beaufort departures
        elif departure_port.lower() in ["beaufort", "hatteras"]:
            recommendations["recommended_crossing_lat"] = 34.7
            recommendations["recommended_exit_lat"] = 34.5
            recommendations["rationale"].append(
                "Beaufort departure - typically milder conditions south of Hatteras"
            )
        
        return recommendations
    
    @staticmethod
    def estimate_current_benefit(
        route_waypoints: List[Tuple[float, float]],
        eddy_data: Optional[Dict] = None,
    ) -> float:
        """
        Estimate speed gain/loss from Gulf Stream currents.
        
        Args:
            route_waypoints: Route waypoints
            eddy_data: Optional eddy analysis data
            
        Returns:
            Estimated speed delta in knots (positive is favorable)
        """
        # Simplified estimation - would use actual current data in production
        # Gulf Stream typically provides 1-3 knots boost eastward
        
        # Check if route crosses Gulf Stream (roughly 70-75W longitude)
        crosses_stream = any(
            -76 < lon < -70 for lat, lon in route_waypoints
        )
        
        if crosses_stream:
            return 1.5  # Average favorable current
        return 0.0


class RouteVariant:
    """Represents tactical route variations (northern vs southern track)."""
    
    @staticmethod
    def create_variants(
        base_route_name: str,
        vessel: Optional[Vessel] = None,
    ) -> List[Route]:
        """
        Create tactical route variants for a base route.
        
        Args:
            base_route_name: Name of base route (e.g., 'hampton-bermuda')
            vessel: Vessel characteristics
        
        Returns:
            List of Route objects representing variants
        """
        if base_route_name not in Route.ROUTES:
            raise ValueError(f"Unknown route: {base_route_name}")
        
        base_def = Route.ROUTES[base_route_name]
        start = base_def["start"]
        end = base_def["end"]
        
        variants = []
        
        # Direct/rhumbline route
        direct_route = Route(base_route_name, vessel=vessel)
        direct_route.variant_name = "direct"
        variants.append(direct_route)
        
        # For Hampton-Bermuda and similar routes, create northern and southern variants
        if base_route_name in ["hampton-bermuda", "beaufort-bermuda"]:
            # Northern variant: go north first to 37°N, then southeast
            north_waypoints = [
                start,
                (37.0, start[1] - 2.0),  # North then east
                (36.0, -70.0),  # Exit Gulf Stream north
                end,
            ]
            north_route = Route(
                f"{base_route_name}-north",
                waypoints=north_waypoints,
                vessel=vessel,
            )
            north_route.variant_name = "northern"
            variants.append(north_route)
            
            # Southern variant: go south first to 34-35°N, then southeast
            south_waypoints = [
                start,
                (35.0, start[1]),  # South first
                (34.5, -72.0),  # Exit Gulf Stream south
                end,
            ]
            south_route = Route(
                f"{base_route_name}-south",
                waypoints=south_waypoints,
                vessel=vessel,
            )
            south_route.variant_name = "southern"
            variants.append(south_route)
        
        # For Hampton-Antigua, add Bermuda waypoint variants
        elif base_route_name == "hampton-antigua":
            # Via Bermuda
            bermuda = (32.3, -64.8)
            via_bermuda_waypoints = [start, bermuda, end]
            via_bermuda_route = Route(
                f"{base_route_name}-via-bermuda",
                waypoints=via_bermuda_waypoints,
                vessel=vessel,
            )
            via_bermuda_route.variant_name = "via_bermuda"
            variants.append(via_bermuda_route)
        
        return variants
    
    @staticmethod
    def recommend_best_variant(
        variants: List[Route],
        wind_forecasts: Dict[str, Any],
        wave_forecasts: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Recommend best route variant based on forecasts.
        
        Args:
            variants: List of route variants
            wind_forecasts: Wind forecast data
            wave_forecasts: Wave forecast data
        
        Returns:
            Recommendation dictionary
        """
        # Placeholder - would analyze each variant
        # For now, return framework
        return {
            "recommended_variant": variants[0].variant_name if variants else "direct",
            "rationale": "Direct route recommended (analysis not yet implemented)",
            "alternatives": [v.variant_name for v in variants[1:]] if len(variants) > 1 else [],
        }


def create_route_from_ports(
    departure_port: str,
    destination_port: str,
    vessel: Optional[Vessel] = None,
) -> Route:
    """
    Create a route from port names.
    
    Args:
        departure_port: Departure port name
        destination_port: Destination port name
        vessel: Vessel characteristics
        
    Returns:
        Route object
    """
    route_key = f"{departure_port.lower()}-{destination_port.lower()}"
    
    if route_key in Route.ROUTES:
        return Route(route_key, vessel=vessel)
    else:
        raise ValueError(
            f"Route {route_key} not defined. Available routes: {list(Route.ROUTES.keys())}"
        )
