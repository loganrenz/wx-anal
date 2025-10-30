"""
Advanced sea state analysis including heading-relative conditions.

This module provides detailed analysis of wind and wave conditions relative
to vessel heading, including wave period, steepness, and Gulf Stream interactions.
"""

import logging
from typing import Dict, List, Tuple, Optional, Any

import numpy as np

logger = logging.getLogger(__name__)


class SeaStateAnalyzer:
    """Analyze sea state conditions relative to vessel motion."""
    
    # Wave period thresholds for steepness
    SHORT_PERIOD_THRESHOLD = 7.0  # seconds - steep, uncomfortable
    MODERATE_PERIOD_THRESHOLD = 10.0  # seconds - moderate steepness
    
    # Relative angle categories (degrees off bow)
    HEAD_ANGLE_MAX = 45  # 0-45° = head seas
    BEAM_ANGLE_MIN = 45  # 45-135° = beam seas
    BEAM_ANGLE_MAX = 135
    # 135-180° = following/stern seas
    
    def __init__(self):
        """Initialize sea state analyzer."""
        pass
    
    def analyze_heading_relative_wind(
        self,
        wind_speed: float,
        wind_direction: float,
        vessel_heading: float,
        vessel_speed: float = 6.0,
    ) -> Dict[str, Any]:
        """
        Analyze wind conditions relative to vessel heading.
        
        Args:
            wind_speed: True wind speed in m/s
            wind_direction: True wind direction in degrees (meteorological, FROM)
            vessel_heading: Vessel heading in degrees
            vessel_speed: Vessel speed in knots
        
        Returns:
            Dictionary with heading-relative analysis
        """
        # Calculate relative wind angle
        relative_angle = self._calculate_relative_angle(wind_direction, vessel_heading)
        
        # Determine wind position
        wind_position = self._classify_wind_position(relative_angle)
        
        # Calculate apparent wind (simplified)
        # In practice, this requires vector addition of true wind and vessel motion
        apparent_wind_speed = wind_speed  # Simplified for now
        
        # Assess comfort/safety based on position
        comfort_factor = self._assess_wind_comfort(
            wind_speed, relative_angle, wind_position
        )
        
        results = {
            "wind_speed_ms": wind_speed,
            "wind_speed_kt": wind_speed * 1.94384,
            "true_wind_direction": wind_direction,
            "vessel_heading": vessel_heading,
            "relative_angle": relative_angle,
            "wind_position": wind_position,
            "apparent_wind_speed": apparent_wind_speed,
            "comfort_factor": comfort_factor,  # 0-100, higher is better
            "assessment": self._get_wind_assessment(wind_speed, wind_position, comfort_factor),
        }
        
        return results
    
    def analyze_heading_relative_waves(
        self,
        wave_height: float,
        wave_direction: float,
        wave_period: float,
        vessel_heading: float,
        in_gulf_stream: bool = False,
        current_speed: float = 0.0,
        current_direction: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Analyze wave conditions relative to vessel heading.
        
        Args:
            wave_height: Significant wave height in meters
            wave_direction: Wave direction in degrees (FROM)
            wave_period: Dominant wave period in seconds
            vessel_heading: Vessel heading in degrees
            in_gulf_stream: Whether vessel is in Gulf Stream
            current_speed: Current speed in knots (if in Gulf Stream)
            current_direction: Current direction in degrees
        
        Returns:
            Dictionary with heading-relative wave analysis
        """
        # Calculate relative wave angle
        relative_angle = self._calculate_relative_angle(wave_direction, vessel_heading)
        
        # Determine wave position
        wave_position = self._classify_wave_position(relative_angle)
        
        # Calculate wave steepness
        steepness = self._calculate_wave_steepness(wave_height, wave_period)
        steepness_category = self._classify_wave_steepness(steepness)
        
        # Apply Gulf Stream amplification if applicable
        effective_height = wave_height
        if in_gulf_stream:
            amplification = self._calculate_gulf_stream_amplification(
                wave_height, wave_period, wave_direction,
                current_speed, current_direction
            )
            effective_height = wave_height * amplification
        
        # Assess comfort/safety based on position and steepness
        comfort_factor = self._assess_wave_comfort(
            effective_height, wave_period, relative_angle, wave_position
        )
        
        results = {
            "wave_height_m": wave_height,
            "wave_height_ft": wave_height * 3.28084,
            "effective_height_m": effective_height,
            "effective_height_ft": effective_height * 3.28084,
            "wave_direction": wave_direction,
            "wave_period_s": wave_period,
            "vessel_heading": vessel_heading,
            "relative_angle": relative_angle,
            "wave_position": wave_position,
            "steepness": steepness,
            "steepness_category": steepness_category,
            "in_gulf_stream": in_gulf_stream,
            "gulf_stream_amplification": effective_height / wave_height if wave_height > 0 else 1.0,
            "comfort_factor": comfort_factor,  # 0-100, higher is better
            "assessment": self._get_wave_assessment(
                effective_height, wave_period, wave_position, steepness_category, comfort_factor
            ),
        }
        
        return results
    
    def calculate_combined_discomfort(
        self,
        wind_analysis: Dict[str, Any],
        wave_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculate combined discomfort index from wind and waves.
        
        Args:
            wind_analysis: Results from analyze_heading_relative_wind
            wave_analysis: Results from analyze_heading_relative_waves
        
        Returns:
            Combined discomfort assessment
        """
        # Comfort factors are 0-100, higher is better
        # Convert to discomfort (0-100, higher is worse)
        wind_discomfort = 100 - wind_analysis["comfort_factor"]
        wave_discomfort = 100 - wave_analysis["comfort_factor"]
        
        # Waves typically dominate discomfort
        combined_discomfort = wave_discomfort * 0.7 + wind_discomfort * 0.3
        
        # If both head-on, amplify discomfort
        if (wind_analysis["wind_position"] == "HEAD" and 
            wave_analysis["wave_position"] == "HEAD"):
            combined_discomfort *= 1.2
        
        combined_discomfort = min(100.0, combined_discomfort)
        combined_comfort = 100 - combined_discomfort
        
        # Categorize
        if combined_discomfort < 25:
            category = "COMFORTABLE"
            description = "Comfortable conditions for passage making."
        elif combined_discomfort < 50:
            category = "ACCEPTABLE"
            description = "Acceptable but somewhat uncomfortable. Manageable for experienced crews."
        elif combined_discomfort < 70:
            category = "UNCOMFORTABLE"
            description = "Uncomfortable conditions. Challenging for crew, slow progress."
        else:
            category = "MISERABLE"
            description = "Miserable conditions. Safety concerns, crew fatigue, potential equipment stress."
        
        return {
            "combined_discomfort": combined_discomfort,
            "combined_comfort": combined_comfort,
            "category": category,
            "description": description,
            "wind_contribution": wind_discomfort,
            "wave_contribution": wave_discomfort,
        }
    
    def _calculate_relative_angle(self, feature_direction: float, vessel_heading: float) -> float:
        """
        Calculate relative angle (0-180°) of feature relative to bow.
        
        Args:
            feature_direction: Direction feature is FROM (meteorological convention)
            vessel_heading: Vessel heading (direction vessel is going TO)
        
        Returns:
            Relative angle from bow (0-180°)
        """
        # Feature direction is FROM, vessel heading is TO
        # Relative angle is difference between them
        relative = abs(feature_direction - vessel_heading)
        if relative > 180:
            relative = 360 - relative
        
        return relative
    
    def _classify_wind_position(self, relative_angle: float) -> str:
        """Classify wind position relative to vessel."""
        if relative_angle <= self.HEAD_ANGLE_MAX:
            return "HEAD"
        elif relative_angle <= self.BEAM_ANGLE_MAX:
            return "BEAM"
        else:
            return "STERN"
    
    def _classify_wave_position(self, relative_angle: float) -> str:
        """Classify wave position relative to vessel."""
        return self._classify_wind_position(relative_angle)
    
    def _calculate_wave_steepness(self, height: float, period: float) -> float:
        """
        Calculate wave steepness ratio.
        
        Steepness = height / wavelength
        Wavelength ≈ 1.56 * period^2 (in deep water)
        """
        if period <= 0:
            return 0.0
        
        wavelength = 1.56 * period ** 2  # meters
        steepness = height / wavelength if wavelength > 0 else 0.0
        
        return steepness
    
    def _classify_wave_steepness(self, steepness: float) -> str:
        """Classify wave steepness."""
        if steepness < 0.02:
            return "GENTLE"
        elif steepness < 0.035:
            return "MODERATE"
        elif steepness < 0.05:
            return "STEEP"
        else:
            return "VERY_STEEP"
    
    def _calculate_gulf_stream_amplification(
        self,
        wave_height: float,
        wave_period: float,
        wave_direction: float,
        current_speed: float,
        current_direction: float,
    ) -> float:
        """
        Calculate wave height amplification in opposing current (Gulf Stream).
        
        Waves steepen when opposing current, flatten when following current.
        """
        if current_speed <= 0:
            return 1.0
        
        # Calculate if waves oppose current
        relative_angle = abs((wave_direction - current_direction + 180) % 360 - 180)
        
        # Maximum opposition at 180°, minimum at 0°
        opposition_factor = np.cos(np.radians(relative_angle))
        
        # Amplification increases with current speed and wave period
        # Short-period waves are affected more
        if wave_period < self.SHORT_PERIOD_THRESHOLD:
            base_amplification = 1.0 + (current_speed * 0.15 * opposition_factor)
        else:
            base_amplification = 1.0 + (current_speed * 0.08 * opposition_factor)
        
        # Cap amplification
        return max(0.8, min(1.5, base_amplification))
    
    def _assess_wind_comfort(
        self,
        wind_speed: float,
        relative_angle: float,
        wind_position: str
    ) -> float:
        """
        Assess wind comfort (0-100, higher is better).
        
        Head winds are much worse than beam or stern winds at same speed.
        """
        # Base comfort from wind speed
        wind_speed_kt = wind_speed * 1.94384
        
        if wind_speed_kt < 15:
            base_comfort = 90
        elif wind_speed_kt < 25:
            base_comfort = 70
        elif wind_speed_kt < 35:
            base_comfort = 45
        else:
            base_comfort = 20
        
        # Adjust for position
        if wind_position == "HEAD":
            position_penalty = 30
        elif wind_position == "BEAM":
            position_penalty = 10
        else:  # STERN
            position_penalty = 0
        
        comfort = max(0, base_comfort - position_penalty)
        return comfort
    
    def _assess_wave_comfort(
        self,
        height: float,
        period: float,
        relative_angle: float,
        wave_position: str
    ) -> float:
        """
        Assess wave comfort (0-100, higher is better).
        
        Head seas with short period are much worse than beam or stern seas.
        """
        # Base comfort from height
        height_ft = height * 3.28084
        
        if height_ft < 4:
            base_comfort = 85
        elif height_ft < 8:
            base_comfort = 65
        elif height_ft < 12:
            base_comfort = 40
        else:
            base_comfort = 15
        
        # Period adjustment (short period = steeper = worse)
        if period < self.SHORT_PERIOD_THRESHOLD:
            period_penalty = 20
        elif period < self.MODERATE_PERIOD_THRESHOLD:
            period_penalty = 10
        else:
            period_penalty = 0
        
        # Position adjustment (head seas worse than beam, beam worse than stern)
        if wave_position == "HEAD":
            position_penalty = 25
        elif wave_position == "BEAM":
            position_penalty = 10
        else:  # STERN
            position_penalty = 0
        
        comfort = max(0, base_comfort - period_penalty - position_penalty)
        return comfort
    
    def _get_wind_assessment(
        self,
        wind_speed: float,
        wind_position: str,
        comfort_factor: float
    ) -> str:
        """Generate human-readable wind assessment."""
        wind_speed_kt = wind_speed * 1.94384
        
        if wind_position == "HEAD":
            pos_desc = "on the nose"
        elif wind_position == "BEAM":
            pos_desc = "on the beam"
        else:
            pos_desc = "from astern"
        
        if comfort_factor > 70:
            severity = "Favorable"
        elif comfort_factor > 50:
            severity = "Manageable"
        elif comfort_factor > 30:
            severity = "Challenging"
        else:
            severity = "Difficult"
        
        return f"{severity}: {wind_speed_kt:.0f} kt {pos_desc}"
    
    def _get_wave_assessment(
        self,
        height: float,
        period: float,
        wave_position: str,
        steepness_category: str,
        comfort_factor: float
    ) -> str:
        """Generate human-readable wave assessment."""
        height_ft = height * 3.28084
        
        if wave_position == "HEAD":
            pos_desc = "on the nose"
        elif wave_position == "BEAM":
            pos_desc = "on the beam"
        else:
            pos_desc = "from astern"
        
        if comfort_factor > 70:
            severity = "Comfortable"
        elif comfort_factor > 50:
            severity = "Tolerable"
        elif comfort_factor > 30:
            severity = "Uncomfortable"
        else:
            severity = "Severe"
        
        return (
            f"{severity}: {height_ft:.0f} ft @ {period:.0f}s {pos_desc} "
            f"({steepness_category.lower()} seas)"
        )
