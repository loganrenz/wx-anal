# No Mock Data in Production - Policy Document

## Critical Safety Policy

**DANGER:** Using mock/synthetic data for real weather routing analysis can lead to dangerous decisions at sea. This policy ensures we never accidentally use fake data when real lives and vessels are at stake.

## The Problem

Mock data is useful for testing and demos, but:
- It doesn't reflect real weather patterns
- It can't show real hazards
- Using it for actual routing decisions is **dangerous**
- Accidental use can happen if fallbacks exist in production code

## The Solution

### Mock Data is ONLY Allowed in Tests

Mock data may only be used in:
- ✅ Unit test files (`tests/test_*.py` excluding `test_*_integration.py`)
- ✅ Demo scripts when explicitly documented as demonstration-only

### Mock Data is FORBIDDEN in Production

Mock data must NEVER be used in:
- ❌ CLI commands (`wx-anal`)
- ❌ Analysis scripts (`generate_weather_report.py`, `generate_multi_run_report.py`)
- ❌ Library code (`src/wx_anal/*.py`)
- ❌ Any code that could be used for real routing decisions

## Implementation

### Removed from Production Code

1. **Removed `use_mock_data` parameter** from:
   - `WeatherDownloader.download_offshore_route_data()`
   - `analyze_route()` in CLI
   - All production scripts

2. **Removed mock data fallbacks** from:
   - `generate_weather_report.py` - Now exits with error if data unavailable
   - `generate_multi_run_report.py` - No fallback to mock data
   - CLI - Fails immediately if download fails

3. **Demo script updated**:
   - `demo_enhanced_analysis.py` continues with limited analysis if data unavailable
   - Clearly documented as demonstration-only
   - Does not pretend to be a real analysis

### Kept in Test Code

1. **`mock_data.py` module**:
   - Remains in `src/wx_anal/` for backwards compatibility
   - Only imported by test files
   - Never imported by production code

2. **Test usage**:
   - Unit tests import `mock_data` directly: `from wx_anal.mock_data import generate_mock_route_data`
   - Integration tests use real data downloads
   - Clear separation between test and production code paths

## Integration Tests Enforce Policy

New integration tests in `test_downloader_integration.py`:
- Verify real data downloads work
- Test 16-day GFS forecast availability
- Validate data quality and realism
- Ensure download errors are caught properly

These tests WILL FAIL if:
- Production code tries to use mock data
- Download functions have mock data fallbacks
- Data quality is poor

## Developer Guidelines

### When Adding New Features

1. **Never add `use_mock_data` parameters**
2. **Never add fallbacks to mock data**
3. **Fail fast** if real data is unavailable
4. **Add integration tests** to verify real data works
5. **Document** any demo/test-only code clearly

### When Data Download Fails

Production code should:
```python
try:
    data = downloader.download_offshore_route_data(...)
except Exception as e:
    logger.error(f"Cannot download weather data: {e}")
    logger.error("Check internet connection and NOAA server status")
    sys.exit(1)  # FAIL - don't continue with fake data
```

Test code can:
```python
from wx_anal.mock_data import generate_mock_route_data

data = generate_mock_route_data("hampton-bermuda", departure, 5)
# Continue with test
```

### Code Review Checklist

When reviewing PRs, check:
- [ ] No `use_mock_data` parameters in production code
- [ ] No imports of `mock_data` in production code
- [ ] Download failures cause immediate exit, not fallback
- [ ] New download features have integration tests
- [ ] Demo scripts clearly marked as demonstration-only

## Examples

### ❌ WRONG - Production Code with Mock Fallback

```python
# DON'T DO THIS
try:
    data = downloader.download_gfs(...)
except:
    logger.warning("Using mock data instead")
    data = generate_mock_data()  # DANGER!
```

### ✅ CORRECT - Production Code Fails Fast

```python
# DO THIS
try:
    data = downloader.download_gfs(...)
except Exception as e:
    logger.error(f"Download failed: {e}")
    sys.exit(1)
```

### ✅ CORRECT - Test Code Uses Mock Data

```python
# Test file - OK to use mock data
def test_analysis_logic():
    from wx_anal.mock_data import generate_mock_route_data
    data = generate_mock_route_data("hampton-bermuda", departure, 5)
    # Test analysis logic
    assert analyzer.analyze(data) ...
```

## Running Tests

### Unit Tests (Use Mock Data)
```bash
# Run regular tests - these may use mock data internally
pytest
```

### Integration Tests (Use Real Data)
```bash
# Run integration tests - these NEVER use mock data
pytest -m integration
```

## Benefits

1. **Safety**: Can never accidentally route a vessel using fake weather
2. **Reliability**: Know immediately if data download is broken
3. **Clarity**: Clear separation between test and production code
4. **Trust**: Users can trust analysis is based on real data

## Consequences of Violation

Using mock data in production:
- **Immediately fails CI/CD** - integration tests will catch it
- **Code review rejection** - will not be merged
- **Safety hazard** - could lead to dangerous routing decisions

## Documentation

This policy is enforced by:
- This document (NO_MOCK_DATA_POLICY.md)
- Integration test documentation (tests/INTEGRATION_TESTS.md)
- Code comments in mock_data.py
- CI/CD pipeline checks

## Questions?

If you're unsure whether mock data is appropriate:
- **Default answer**: NO
- **Ask**: "Could this code path be used for a real routing decision?"
- **If yes**: NO MOCK DATA
- **If no**: Only if it's clearly a test or demo

## Last Updated

2025-10-30

## Related Documents

- tests/INTEGRATION_TESTS.md - Integration test guide
- README.md - Main project documentation
- DEMO_README.md - Demo script documentation
