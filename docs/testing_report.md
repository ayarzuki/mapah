# Testing Report - 2026-05-16

## Test Environment
- **Backend**: FastAPI on `http://localhost:8000`
- **Frontend**: React/Vite on `http://localhost:5173`
- **Date**: May 16, 2026

---

## Bugs Found & Fixed

### 1. Overpass API Returns 0 Competitors (CRITICAL)
**Symptom**: All analyze requests returned `raw_competitor_count: 0` regardless of location.

**Root Cause**: Two issues in `fetch_overpass()`:
- Used `httpx.get()` with `params=` which URL-encodes the query and breaks Overpass syntax
- Missing `User-Agent` header — Overpass API returns `406 Not Acceptable` without a valid User-Agent

**Fix**: Changed to `httpx.post()` with raw query body and added `User-Agent: mapah.id/1.0` header.

**Before**: 0 competitors found
**After**: 95 competitors found in Jakarta area (3km radius, Coffee Shop)

### 2. Rate Limit Threshold Off-by-One
**Symptom**: Rate limit triggered at request 9 instead of 10.

**Cause**: Previous test requests within the same 60-second window counted toward the limit.

**Status**: Working as designed. The in-memory rate limiter correctly enforces 10 requests per 60-second window per IP.

---

## Drawbacks Identified

### 1. LLM Analysis Falls Back to Simple Scoring
**Issue**: When Kimi API key is not configured or fails, the fallback scoring is overly simplistic:
```python
score = max(10, 90 - (num_competitors * 3))
```
This produces the same score for any location with the same competitor count, ignoring:
- Competitor quality/ratings
- Population density
- Foot traffic generators
- Economic context of the area

**Impact**: Free-tier users get generic, non-actionable insights.

### 2. No Address Search / Geocoding
**Issue**: Users must manually click on the map to select a location. There is no:
- Address search bar
- Geocoding integration (Google Geocoding API, OpenStreetMap Nominatim)
- "Use my location" GPS button

**Impact**: Poor UX for users who know an address but not coordinates.

### 3. No Radius Selector in React Frontend
**Issue**: The `backend/static/app.html` has a Pro Mode toggle, but the React `App.jsx` has:
- No radius selector (hardcoded to default 2000m)
- No Pro Mode toggle
- No address search
- Still uses dropdown instead of free-text input (regression from backend's dynamic search feature)

**Impact**: React frontend is less functional than the vanilla HTML version.

### 4. Competitor List Shows "Unnamed Competitor" Frequently
**Issue**: Many OSM nodes don't have a `name` tag, resulting in generic "Unnamed Competitor" labels on the map.

**Impact**: Cluttered map with duplicate popup labels, hard to distinguish competitors.

### 5. No Loading State for Map Markers
**Issue**: When analyzing, the button shows "Analyzing..." but the map doesn't indicate that competitor data is being fetched. Users may think nothing is happening during the 15-30 second LLM call.

### 6. Score Color Logic Only in Vanilla HTML
**Issue**: The React frontend always shows the score in blue (`text-blue-900`). The vanilla `app.html` has color logic:
- Green for score >= 80
- Yellow for score >= 50
- Red for score < 50

**Impact**: React users can't visually distinguish good vs bad scores.

### 7. SWOT Sections Show Empty Lists
**Issue**: When fallback scoring is used, `opportunities` and `threats` arrays are often empty, rendering blank sections in the UI with just a header and no content.

### 8. No Error Boundary in React
**Issue**: If the API fails or returns malformed data, the React app will crash with an unhandled error instead of showing a user-friendly error message.

### 9. Duplicate Frontend Implementations
**Issue**: Two separate UIs exist:
- `backend/static/app.html` — More features (Pro toggle, free-text input, score coloring)
- `frontend/src/App.jsx` — Less features but uses modern React stack

**Impact**: Maintenance burden, feature drift between versions.

### 10. No Pagination or Clustering for Competitor Markers
**Issue**: All 50 competitors are rendered as individual map markers. In dense areas (like Jakarta), markers overlap completely and the map becomes unusable.

**Impact**: Poor visualization in high-density areas.

---

## Features to Improve

| Priority | Feature | Description |
|----------|---------|-------------|
| **P0** | Fix React frontend parity | Add free-text input, radius selector, Pro mode toggle, score coloring to match `app.html` |
| **P0** | Address search bar | Integrate Nominatim (free) or Google Geocoding for address-to-coordinate lookup |
| **P1** | Marker clustering | Use `leaflet.markercluster` to group overlapping competitor pins |
| **P1** | "Use my location" button | Browser geolocation API to center map on user's current position |
| **P1** | Traffic generators display | Fetch and display nearby schools, offices, transit hubs on the map |
| **P1** | Empty SWOT handling | Hide empty SWOT sections or show placeholder text |
| **P2** | Competitor detail cards | Show competitor name, rating (if available), distance from selected point |
| **P2** | Analysis history | Save past analyses to localStorage or database for comparison |
| **P2** | Export report | Generate PDF or shareable link for the SWOT analysis |
| **P2** | Better fallback scoring | Use multiple factors (density, area type, time of day) instead of just competitor count |
| **P3** | Dark mode toggle | Theme switcher for the UI |
| **P3** | Multi-language support | i18n for Indonesian and English |

---

## API Performance

| Endpoint | Avg Response Time | Notes |
|----------|-------------------|-------|
| `GET /` | < 50ms | Static HTML |
| `GET /app` | < 50ms | Static HTML |
| `POST /api/analyze` (no LLM) | 2-5s | Overpass API call only |
| `POST /api/analyze` (with LLM) | 10-30s | Overpass + Kimi API call |
| Rate limit (429) | < 10ms | In-memory check |

---

## Test Results Summary

| Test | Result |
|------|--------|
| Backend starts successfully | PASS |
| Frontend starts successfully | PASS |
| Invalid lat validation (100) | PASS — returns 422 |
| Invalid lng validation (200) | PASS — returns 422 |
| Empty category validation | PASS — returns 422 |
| Invalid radius validation (50) | PASS — returns 422 |
| Pro mode without auth | PASS — returns 401 |
| Overpass competitor fetch | PASS — 95 competitors found |
| Rate limiting (10 req/min) | PASS — 429 after limit |
| LLM fallback scoring | PASS — returns fallback data |
| React frontend serves | PASS — HTML loads |
