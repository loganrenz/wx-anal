# Enhanced Weather Analysis Demo & Web Viewer

## Overview

This directory contains a demonstration of the enhanced marine weather analysis capabilities and an interactive web viewer for visualizing the results.

## Files

- **`demo_enhanced_analysis.py`** - Python script that demonstrates all new features
- **`web_viewer.html`** - Interactive web-based visualization tool
- **`demo_analysis_output.json`** - JSON output from demo (generated when running demo)
- **`demo_output.txt`** - Human-readable text output from demo

## Running the Demo

### 1. Run the Analysis Demo

```bash
python demo_enhanced_analysis.py
```

This will generate:
- Console output showing all analysis results
- `demo_analysis_output.json` - structured data for the web viewer

### 2. View in Web Browser

Start a local web server:

```bash
python -m http.server 8080
```

Then open in your browser:
```
http://localhost:8080/web_viewer.html
```

## What the Demo Shows

### Part 1: Forecast Confidence Analysis
- Analyzes consistency across 10 model runs
- Calculates confidence score (0-100)
- Detects flip-flops (run-to-run changes)
- Identifies trends (INCREASING/DECREASING/STABLE)

**Output Example:**
```
Confidence Level:     MODERATE
Confidence Score:     47/100
Detection Rate:       80%
Flip-Flops:          4
Recent Trend:        DECREASING
```

### Part 2: Sea State Analysis (Heading-Relative)
- Analyzes wind/wave conditions relative to vessel heading
- Distinguishes HEAD, BEAM, and STERN positions
- Calculates wave steepness from height and period
- Models Gulf Stream amplification effects
- Generates combined discomfort index (0-100)

**Output Example:**
```
Scenario: Head Winds & Seas
  Wind: Difficult: 29 kt on the nose
    Position: HEAD, Comfort: 15/100
  Waves: Severe: 11 ft @ 7s on the nose (steep seas)
    Gulf Stream Amplification: 1.16x
  Combined Discomfort: 100/100 - MISERABLE
```

### Part 3: Route Variants
- Generates tactical route alternatives
- Creates northern, southern, and direct variants
- Different Gulf Stream crossing strategies

**Output Example:**
```
DIRECT:    640 nm (rhumbline)
NORTHERN:  841 nm (via 37°N to avoid early headwinds)
SOUTHERN:  718 nm (via 34.5°N, different stream exit)
```

### Part 4: Enhanced Risk Scoring
- Calculates risk for slow/typical/fast vessel classes
- Integrates forecast confidence into risk assessment
- Provides vessel-specific recommendations

**Output Example:**
```
SLOW BOATS (5.2 kt avg):
  Base Risk:      11/100
  Adjusted Risk:  21/100
  Risk Level:     LOW
  Recommendation: Extended 5-6 day passage. Monitor forecasts.

FAST BOATS (7.8 kt avg):
  Base Risk:      11/100
  Adjusted Risk:  21/100
  Risk Level:     LOW
  Recommendation: Can outrun developing systems. 3-4 day passage.
```

### Part 5: Vessel Comparison
- Side-by-side comparison of all vessel classes
- Identifies which boats have better/worse prospects
- Suggests bailout options for slow boats

## Web Viewer Features

The interactive web viewer displays:

### 1. Forecast Confidence Dashboard
- Visual confidence meter with color coding
- Statistics grid (runs analyzed, detection rate, flip-flops, trend)
- Human-readable interpretation

### 2. Sea State Visualization
- Cards for each scenario (head/beam/stern)
- Discomfort bars with color coding:
  - 🟢 Green: Comfortable (0-25)
  - 🟡 Yellow-Green: Acceptable (25-50)
  - 🟠 Orange: Uncomfortable (50-70)
  - 🔴 Red: Miserable (70-100)

### 3. Route Map
- Interactive SVG map showing all route variants
- Color-coded routes:
  - 🔵 Blue: Direct route
  - 🟢 Green: Northern variant
  - 🟠 Orange: Southern variant
- Lat/lon grid with waypoint markers

### 4. Vessel Risk Comparison
- Risk cards for slow/typical/fast boats
- Risk level badges (LOW/MODERATE/HIGH)
- Vessel-specific recommendations

### 5. Timeline Controls (Placeholder)
- Slider for future timeline animation feature
- Framework for showing forecast evolution over time

## Understanding the Output

### Forecast Confidence Levels

- **HIGH (80-100)**: Models strongly agree, forecast reliable
- **MODERATE (50-79)**: Some variation, monitor for changes
- **LOW (0-49)**: Inconsistent models, wait for more runs

### Discomfort Categories

- **COMFORTABLE (0-25)**: Pleasant sailing conditions
- **ACCEPTABLE (25-50)**: Somewhat uncomfortable but manageable
- **UNCOMFORTABLE (50-70)**: Challenging, crew fatigue likely
- **MISERABLE (70-100)**: Safety concerns, severe discomfort

### Risk Levels

- **LOW (<30)**: Favorable departure window
- **MODERATE (30-60)**: Marginal, prepare for challenges
- **HIGH (>60)**: Hazardous, recommend delay

## Key Insights Demonstrated

1. **"30 kt on the nose ≠ 30 kt on the beam"**
   - Same wind speed, vastly different comfort
   - Head winds: 15/100 comfort
   - Beam winds: 35/100 comfort
   - Following winds: 45/100 comfort

2. **"Short period waves in Gulf Stream = nasty"**
   - 10 ft @ 7s in opposing current: STEEP, amplified 1.16x
   - 10 ft @ 11s following: GENTLE, no amplification
   - Period matters as much as height

3. **"Faster boats find better windows"**
   - Same forecast, different risk by vessel class
   - Fast boats outrun developing systems
   - Slow boats face extended exposure

4. **"Forecast confidence matters"**
   - 80% detection with 4 flip-flops = MODERATE confidence
   - Risk adjusted upward when models disagree
   - Need 2-3 consistent runs for high confidence

## Future Enhancements

The web viewer framework supports future additions:

- **Timeline Animation**: Play through forecast evolution
- **Color-Coded Features**: Different colors for weather systems
- **Interactive Map**: Click waypoints for details
- **Real-Time Data**: Load live NOAA data instead of mock
- **ECMWF Comparison**: Side-by-side model comparison
- **Historical Tracks**: Overlay previous passages

## Technical Details

### Data Format

The demo generates JSON output with this structure:

```json
{
  "generated_at": "2025-10-30T04:24:39Z",
  "scenario": {
    "route": "hampton-bermuda",
    "departure": "2025-10-31T18:00:00Z"
  },
  "forecast_confidence": {
    "confidence_level": "MODERATE",
    "confidence_score": 47,
    "runs_analyzed": 10,
    "detection_rate": 0.8,
    "flip_flops": 4,
    "recent_trend": "DECREASING"
  },
  "sea_state_scenarios": [...],
  "route_variants": [...],
  "risk_by_vessel": {...},
  "vessel_recommendations": {...}
}
```

### Browser Compatibility

The web viewer uses:
- HTML5 SVG for map visualization
- CSS Grid for responsive layout
- Vanilla JavaScript (no frameworks)
- Modern browser features (ES6+)

Tested on: Chrome, Firefox, Safari, Edge

## Summary

This demonstration shows how wx-anal now provides:

✅ **Forecast Confidence** - "Need 2-3 consistent runs" → Now quantified
✅ **Heading-Relative Conditions** - "30 kt on nose vs beam" → Now distinguished
✅ **Wave Physics** - "7s period in Stream = nasty" → Now calculated
✅ **Tactical Routing** - "North track vs south track" → Now generated
✅ **Vessel-Specific Advice** - "Slow boats bail in Bermuda" → Now recommended

This transforms wx-anal from a forecast summarizer into a professional-grade marine weather decision support tool.
