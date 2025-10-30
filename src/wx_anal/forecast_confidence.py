"""
Forecast confidence analysis based on multi-run consistency.

This module provides tools to assess forecast confidence by comparing
multiple model runs and detecting run-to-run consistency or flip-flops.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

import numpy as np

logger = logging.getLogger(__name__)


class ForecastConfidence:
    """Analyze forecast confidence from multiple model runs."""
    
    # Confidence thresholds
    HIGH_CONFIDENCE_AGREEMENT = 0.8  # 80%+ runs agree
    MODERATE_CONFIDENCE_AGREEMENT = 0.6  # 60-80% runs agree
    LOW_CONFIDENCE_AGREEMENT = 0.4  # 40-60% runs agree
    
    def __init__(self):
        """Initialize forecast confidence analyzer."""
        pass
    
    def analyze_cutoff_consistency(
        self,
        multi_run_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze consistency of cut-off low detection across runs.
        
        Args:
            multi_run_results: List of results from multiple runs, each with
                             'success', 'cutoff_detected', 'cutoff_data', etc.
        
        Returns:
            Dictionary with confidence analysis
        """
        results = {
            "confidence_level": "UNKNOWN",
            "confidence_score": 0.0,  # 0-100 scale
            "runs_analyzed": 0,
            "runs_with_cutoff": 0,
            "detection_rate": 0.0,
            "recent_trend": "STABLE",
            "flip_flops": 0,
            "recommendation_confidence": "LOW",
        }
        
        # Filter successful runs
        successful_runs = [r for r in multi_run_results if r.get("success", False)]
        results["runs_analyzed"] = len(successful_runs)
        
        if len(successful_runs) < 2:
            results["confidence_level"] = "INSUFFICIENT_DATA"
            return results
        
        # Count detections
        detections = [r.get("cutoff_detected", False) for r in successful_runs]
        results["runs_with_cutoff"] = sum(detections)
        results["detection_rate"] = sum(detections) / len(detections)
        
        # Calculate flip-flops (changes between consecutive runs)
        flip_flops = 0
        for i in range(1, len(detections)):
            if detections[i] != detections[i-1]:
                flip_flops += 1
        results["flip_flops"] = flip_flops
        
        # Analyze recent trend (last 3 runs vs older runs)
        if len(successful_runs) >= 6:
            recent = detections[:3]
            older = detections[6:]
            recent_rate = sum(recent) / len(recent)
            older_rate = sum(older) / len(older) if older else 0.0
            
            if recent_rate > older_rate + 0.3:
                results["recent_trend"] = "INCREASING"
            elif recent_rate < older_rate - 0.3:
                results["recent_trend"] = "DECREASING"
            else:
                results["recent_trend"] = "STABLE"
        
        # Determine confidence level
        detection_rate = results["detection_rate"]
        
        if detection_rate >= self.HIGH_CONFIDENCE_AGREEMENT or \
           detection_rate <= (1 - self.HIGH_CONFIDENCE_AGREEMENT):
            # Strong agreement (either mostly yes or mostly no)
            if flip_flops <= 1:
                results["confidence_level"] = "HIGH"
                results["confidence_score"] = 85.0
                results["recommendation_confidence"] = "HIGH"
            else:
                results["confidence_level"] = "MODERATE"
                results["confidence_score"] = 65.0
                results["recommendation_confidence"] = "MODERATE"
        
        elif self.MODERATE_CONFIDENCE_AGREEMENT <= detection_rate <= \
             (1 - self.MODERATE_CONFIDENCE_AGREEMENT):
            # Moderate agreement
            if flip_flops <= 2:
                results["confidence_level"] = "MODERATE"
                results["confidence_score"] = 55.0
                results["recommendation_confidence"] = "MODERATE"
            else:
                results["confidence_level"] = "LOW"
                results["confidence_score"] = 35.0
                results["recommendation_confidence"] = "LOW"
        
        else:
            # Mixed signals - low confidence
            results["confidence_level"] = "LOW"
            results["confidence_score"] = 25.0
            results["recommendation_confidence"] = "VERY_LOW"
        
        # Penalty for flip-flops and unstable trends
        if flip_flops > 2:
            results["confidence_score"] *= 0.8
        if results["recent_trend"] in ["INCREASING", "DECREASING"]:
            results["confidence_score"] *= 0.9
        
        results["confidence_score"] = min(100.0, results["confidence_score"])
        
        logger.info(
            f"Forecast confidence: {results['confidence_level']} "
            f"({results['confidence_score']:.0f}/100), "
            f"detection rate={detection_rate:.1%}, flip_flops={flip_flops}"
        )
        
        return results
    
    def get_confidence_message(self, confidence_results: Dict[str, Any]) -> str:
        """
        Generate human-readable confidence message.
        
        Args:
            confidence_results: Results from analyze_cutoff_consistency
        
        Returns:
            Confidence message string
        """
        level = confidence_results["confidence_level"]
        detection_rate = confidence_results["detection_rate"]
        flip_flops = confidence_results["flip_flops"]
        trend = confidence_results["recent_trend"]
        
        if level == "HIGH":
            if detection_rate > 0.8:
                msg = "HIGH confidence: All recent runs consistently show the cut-off low."
            elif detection_rate < 0.2:
                msg = "HIGH confidence: All recent runs consistently show NO cut-off low."
            else:
                msg = "HIGH confidence: Consistent model behavior across runs."
        
        elif level == "MODERATE":
            msg = f"MODERATE confidence: {detection_rate:.0%} of runs show the feature."
            if flip_flops > 0:
                msg += f" Some run-to-run variation ({flip_flops} flip-flops)."
        
        elif level == "LOW":
            msg = "LOW confidence: Inconsistent model behavior. "
            msg += f"Detection rate={detection_rate:.0%}, {flip_flops} flip-flops."
        
        else:
            msg = "Cannot assess confidence: insufficient data."
        
        if trend == "INCREASING":
            msg += " Recent runs show increasing concern."
        elif trend == "DECREASING":
            msg += " Recent runs show decreasing concern."
        
        return msg
    
    def adjust_risk_for_confidence(
        self,
        base_risk_score: float,
        confidence_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Adjust risk score based on forecast confidence.
        
        Low confidence increases perceived risk because forecast is unreliable.
        
        Args:
            base_risk_score: Base risk score (0-100)
            confidence_results: Results from analyze_cutoff_consistency
        
        Returns:
            Dictionary with adjusted risk and explanation
        """
        confidence_level = confidence_results["confidence_level"]
        confidence_score = confidence_results["confidence_score"]
        
        # Uncertainty penalty
        if confidence_level == "HIGH":
            uncertainty_penalty = 0.0
        elif confidence_level == "MODERATE":
            uncertainty_penalty = 10.0
        elif confidence_level == "LOW":
            uncertainty_penalty = 20.0
        else:
            uncertainty_penalty = 15.0
        
        adjusted_risk = min(100.0, base_risk_score + uncertainty_penalty)
        
        results = {
            "base_risk": base_risk_score,
            "uncertainty_penalty": uncertainty_penalty,
            "adjusted_risk": adjusted_risk,
            "confidence_level": confidence_level,
            "confidence_score": confidence_score,
            "explanation": self._get_adjustment_explanation(
                base_risk_score, adjusted_risk, confidence_level
            ),
        }
        
        return results
    
    def _get_adjustment_explanation(
        self,
        base_risk: float,
        adjusted_risk: float,
        confidence_level: str
    ) -> str:
        """Generate explanation for risk adjustment."""
        if base_risk == adjusted_risk:
            return "No adjustment: forecast confidence is high."
        
        penalty = adjusted_risk - base_risk
        
        if confidence_level == "LOW":
            return (
                f"Risk increased by {penalty:.0f} points due to LOW forecast "
                f"confidence. Model runs are inconsistent."
            )
        elif confidence_level == "MODERATE":
            return (
                f"Risk increased by {penalty:.0f} points due to MODERATE forecast "
                f"confidence. Some run-to-run variation observed."
            )
        else:
            return f"Risk adjusted by {penalty:.0f} points for forecast uncertainty."
    
    def compare_vessel_risks(
        self,
        slow_risk: Dict[str, Any],
        typical_risk: Dict[str, Any],
        fast_risk: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Compare risks across vessel types and generate recommendations.
        
        Args:
            slow_risk: Risk assessment for slow boats
            typical_risk: Risk assessment for typical boats
            fast_risk: Risk assessment for fast boats
        
        Returns:
            Dictionary with vessel-specific recommendations
        """
        recommendations = {}
        
        # Slow boats
        if slow_risk["risk_score"] > 60:
            recommendations["slow"] = (
                "HIGH RISK for slow boats. Strong recommendation to delay departure "
                "or consider stopping in Bermuda to avoid extended exposure."
            )
        elif slow_risk["risk_score"] > 40:
            recommendations["slow"] = (
                "MODERATE RISK for slow boats. Extended passage time increases "
                "exposure to weather. Monitor closely and consider Bermuda bailout."
            )
        else:
            recommendations["slow"] = (
                "Acceptable conditions for slow boats, but monitor forecasts. "
                "Passage will take 5-6 days."
            )
        
        # Typical boats
        if typical_risk["risk_score"] > 60:
            recommendations["typical"] = (
                "HIGH RISK for typical cruising boats. Recommend delaying departure."
            )
        elif typical_risk["risk_score"] > 40:
            recommendations["typical"] = (
                "MODERATE RISK for typical boats. Conditions marginal but manageable "
                "for experienced crews."
            )
        else:
            recommendations["typical"] = (
                "Favorable conditions for typical cruising boats. 4-5 day passage."
            )
        
        # Fast boats
        if fast_risk["risk_score"] > 60:
            recommendations["fast"] = (
                "HIGH RISK even for fast boats. Recommend delaying departure."
            )
        elif fast_risk["risk_score"] > 40:
            recommendations["fast"] = (
                "MODERATE RISK for fast boats. Speed advantage helps but conditions "
                "still challenging."
            )
        else:
            recommendations["fast"] = (
                "Good window for fast boats. Can outrun developing systems. 3-4 day passage."
            )
        
        # Comparative analysis
        risk_spread = max(
            slow_risk["risk_score"],
            typical_risk["risk_score"],
            fast_risk["risk_score"]
        ) - min(
            slow_risk["risk_score"],
            typical_risk["risk_score"],
            fast_risk["risk_score"]
        )
        
        if risk_spread > 20:
            recommendations["summary"] = (
                "Window significantly better for faster boats. Vessel speed is "
                "a major factor in this forecast."
            )
        elif all(r["risk_score"] > 60 for r in [slow_risk, typical_risk, fast_risk]):
            recommendations["summary"] = (
                "Conditions hazardous for all vessel types. Delay recommended."
            )
        elif all(r["risk_score"] < 40 for r in [slow_risk, typical_risk, fast_risk]):
            recommendations["summary"] = (
                "Favorable conditions for all vessel types. Good departure window."
            )
        else:
            recommendations["summary"] = (
                "Mixed conditions. Faster boats have better prospects."
            )
        
        return recommendations
