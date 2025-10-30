# Multi-Run Weather Analysis Report

**Generated:** 2025-10-30 02:45 UTC

**Analysis Type:** Model Run Consistency Check

---

## Model Runs Analyzed

**Latest Run:** 2025-10-29 18:00 UTC
**Analysis Period:** Last 60 hours (10 runs at 6-hour intervals)

| Run Time | Cycle | Age |
|----------|-------|-----|
| 2025-10-29 18:00 UTC | 18Z | 0h ago |
| 2025-10-29 12:00 UTC | 12Z | 6h ago |
| 2025-10-29 06:00 UTC | 06Z | 12h ago |
| 2025-10-29 00:00 UTC | 00Z | 18h ago |
| 2025-10-28 18:00 UTC | 18Z | 24h ago |
| 2025-10-28 12:00 UTC | 12Z | 30h ago |
| 2025-10-28 06:00 UTC | 06Z | 36h ago |
| 2025-10-28 00:00 UTC | 00Z | 42h ago |
| 2025-10-27 18:00 UTC | 18Z | 48h ago |
| 2025-10-27 12:00 UTC | 12Z | 54h ago |

---

## Analysis Summary

**Successfully Analyzed:** 10/10 runs
**Cut-off Low Detected:** 0/10 runs (0%)
**Reattachment Likely:** 0/1 detected runs

**Forecast Consensus:** 🟢 GOOD CASE - No cut-off low in any run
**Confidence Level:** HIGH

---

## Detailed Run-by-Run Analysis

### Run 1: 2025-10-29 18z

✅ **No Cut-off Low Detected**
- 500 hPa vorticity below threshold over Louisiana
- Stable pattern, no closed circulation

### Run 2: 2025-10-29 12z

✅ **No Cut-off Low Detected**
- 500 hPa vorticity below threshold over Louisiana
- Stable pattern, no closed circulation

### Run 3: 2025-10-29 06z

✅ **No Cut-off Low Detected**
- 500 hPa vorticity below threshold over Louisiana
- Stable pattern, no closed circulation

### Run 4: 2025-10-29 00z

✅ **No Cut-off Low Detected**
- 500 hPa vorticity below threshold over Louisiana
- Stable pattern, no closed circulation

### Run 5: 2025-10-28 18z

✅ **No Cut-off Low Detected**
- 500 hPa vorticity below threshold over Louisiana
- Stable pattern, no closed circulation

### Run 6: 2025-10-28 12z

✅ **No Cut-off Low Detected**
- 500 hPa vorticity below threshold over Louisiana
- Stable pattern, no closed circulation

### Run 7: 2025-10-28 06z

✅ **No Cut-off Low Detected**
- 500 hPa vorticity below threshold over Louisiana
- Stable pattern, no closed circulation

### Run 8: 2025-10-28 00z

✅ **No Cut-off Low Detected**
- 500 hPa vorticity below threshold over Louisiana
- Stable pattern, no closed circulation

### Run 9: 2025-10-27 18z

✅ **No Cut-off Low Detected**
- 500 hPa vorticity below threshold over Louisiana
- Stable pattern, no closed circulation

### Run 10: 2025-10-27 12z

✅ **No Cut-off Low Detected**
- 500 hPa vorticity below threshold over Louisiana
- Stable pattern, no closed circulation

---

## Trend Analysis

**Recent Runs (last 3):** 0/3 show cut-off (0%)
**Older Runs (runs 8-10):** 0/3 show cut-off (0%)

➡️ **Stable Forecast** - Consistent signal across time

---

## Multi-Model Comparison

### GFS (Global Forecast System)

✅ **Analyzed:** 10 recent runs (primary analysis above)

**Characteristics:**
- Resolution: 0.25° (~25 km)
- Update Frequency: Every 6 hours (00Z, 06Z, 12Z, 18Z)
- Forecast Range: 16 days
- Strengths: Frequent updates, free access, good for trends
- Limitations: Can over-amplify features, less skill at extended range

### ECMWF (European Model)

⚠️ **Status:** Not analyzed (requires subscription)

**Characteristics:**
- Resolution: 0.1° (~9 km)
- Update Frequency: Twice daily (00Z, 12Z)
- Forecast Range: 15 days
- Strengths: Generally considered most accurate, excellent upper-air analysis
- Access: Requires ECMWF account or commercial provider

**Typical Comparison with GFS:**
- ECMWF often more conservative with cut-off low formation
- Better handling of upper-level dynamics
- When ECMWF and GFS agree, confidence is high
- When they disagree, ECMWF typically more reliable

### CMC (Canadian Model)

⚠️ **Status:** Not analyzed (limited public access)

**Characteristics:**
- Resolution: 0.24° (~25 km)
- Update Frequency: Twice daily (00Z, 12Z)
- Forecast Range: 16 days
- Strengths: Independent verification, good North American coverage
- Access: Limited public OPeNDAP access

---

## Recommendations Based on Multi-Run Analysis

### 🟢 FAVORABLE FOR FRIDAY 10/31 DEPARTURE

**Rationale:**
- None of the 10 analyzed runs show cut-off low development
- Consistent signal across all model runs
- Chris Parker's feared 'bad case' scenario not materializing

**Action Items:**
1. ✓ Proceed with Friday afternoon departure planning
2. Continue monitoring 12Z and 18Z runs today for confirmation
3. Final go/no-go decision Friday morning based on latest data
4. Have contingency plan for Wednesday 11/5 if conditions change

---

## Technical Notes

**Analysis Method:**
- 500 hPa vorticity threshold: 8×10⁻⁵ s⁻¹
- Detection region: 25-34°N, 88-96°W (Louisiana)
- Reattachment criteria: >5° eastward motion + 300 hPa winds >30 m/s
- Spatial clustering: scipy.ndimage for feature identification

**Data Sources:**
- GFS: NOAA NOMADS OPeNDAP servers
- ECMWF: Not accessed (subscription required)
- CMC: Not accessed (limited public availability)

**Limitations:**
- Analysis limited to publicly accessible GFS data
- ECMWF and CMC comparison would strengthen confidence
- Model runs older than 3 days may not be available
- Network connectivity required for real-time analysis

---

*Multi-run analysis generated: 2025-10-30 02:45:44 UTC*

**Next Update:** Re-run analysis with `python generate_multi_run_report.py` for latest data