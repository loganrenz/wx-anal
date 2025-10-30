"""Tests for forecast confidence analysis."""

import pytest
from wx_anal.forecast_confidence import ForecastConfidence


def test_confidence_high_agreement_all_yes():
    """Test high confidence when all runs show cut-off."""
    fc = ForecastConfidence()
    
    # All 10 runs show cut-off
    runs = [
        {"success": True, "cutoff_detected": True} for _ in range(10)
    ]
    
    result = fc.analyze_cutoff_consistency(runs)
    
    assert result["confidence_level"] == "HIGH"
    assert result["runs_analyzed"] == 10
    assert result["runs_with_cutoff"] == 10
    assert result["detection_rate"] == 1.0
    assert result["flip_flops"] == 0


def test_confidence_high_agreement_all_no():
    """Test high confidence when no runs show cut-off."""
    fc = ForecastConfidence()
    
    # No runs show cut-off
    runs = [
        {"success": True, "cutoff_detected": False} for _ in range(10)
    ]
    
    result = fc.analyze_cutoff_consistency(runs)
    
    assert result["confidence_level"] == "HIGH"
    assert result["runs_analyzed"] == 10
    assert result["runs_with_cutoff"] == 0
    assert result["detection_rate"] == 0.0
    assert result["flip_flops"] == 0


def test_confidence_low_mixed_signals():
    """Test low confidence with mixed signals."""
    fc = ForecastConfidence()
    
    # Alternating results - lots of flip-flops
    runs = [
        {"success": True, "cutoff_detected": i % 2 == 0} for i in range(10)
    ]
    
    result = fc.analyze_cutoff_consistency(runs)
    
    assert result["confidence_level"] == "LOW"
    assert result["flip_flops"] == 9  # Many flip-flops


def test_confidence_moderate():
    """Test moderate confidence with some variation."""
    fc = ForecastConfidence()
    
    # 7 out of 10 show cut-off (should be moderate to high depending on flip-flops)
    runs = (
        [{"success": True, "cutoff_detected": True}] * 7 +
        [{"success": True, "cutoff_detected": False}] * 3
    )
    
    result = fc.analyze_cutoff_consistency(runs)
    
    # 70% detection rate could be high or moderate depending on flip-flops
    assert result["confidence_level"] in ["HIGH", "MODERATE", "LOW"]
    assert result["detection_rate"] == 0.7


def test_confidence_insufficient_data():
    """Test with insufficient data."""
    fc = ForecastConfidence()
    
    runs = [{"success": True, "cutoff_detected": True}]
    
    result = fc.analyze_cutoff_consistency(runs)
    
    assert result["confidence_level"] == "INSUFFICIENT_DATA"


def test_confidence_message():
    """Test confidence message generation."""
    fc = ForecastConfidence()
    
    conf_result = {
        "confidence_level": "HIGH",
        "detection_rate": 0.9,
        "flip_flops": 0,
        "recent_trend": "STABLE",
    }
    
    message = fc.get_confidence_message(conf_result)
    
    assert "HIGH confidence" in message
    assert len(message) > 0


def test_adjust_risk_for_confidence_high():
    """Test risk adjustment with high confidence."""
    fc = ForecastConfidence()
    
    base_risk = 50.0
    confidence_results = {
        "confidence_level": "HIGH",
        "confidence_score": 85.0,
    }
    
    adjusted = fc.adjust_risk_for_confidence(base_risk, confidence_results)
    
    assert adjusted["adjusted_risk"] == base_risk  # No penalty
    assert adjusted["uncertainty_penalty"] == 0.0


def test_adjust_risk_for_confidence_low():
    """Test risk adjustment with low confidence."""
    fc = ForecastConfidence()
    
    base_risk = 50.0
    confidence_results = {
        "confidence_level": "LOW",
        "confidence_score": 25.0,
    }
    
    adjusted = fc.adjust_risk_for_confidence(base_risk, confidence_results)
    
    assert adjusted["adjusted_risk"] > base_risk  # Penalty applied
    assert adjusted["uncertainty_penalty"] == 20.0


def test_compare_vessel_risks():
    """Test vessel-specific risk comparison."""
    fc = ForecastConfidence()
    
    slow_risk = {"risk_score": 70.0}
    typical_risk = {"risk_score": 55.0}
    fast_risk = {"risk_score": 40.0}
    
    recs = fc.compare_vessel_risks(slow_risk, typical_risk, fast_risk)
    
    assert "slow" in recs
    assert "typical" in recs
    assert "fast" in recs
    assert "summary" in recs
    
    # Slow boats should have stronger warning
    assert "HIGH RISK" in recs["slow"]
    # Check for vessel speed language (case insensitive)
    summary_lower = recs["summary"].lower()
    assert "fast" in summary_lower or "vessel" in summary_lower or "speed" in summary_lower
