# Changelog

All notable changes to the mapah.id project will be documented in this file.

## [2026-05-16] - Security Hardening, Validation, and Infrastructure
### Security
- **CORS Restriction**: Replaced `allow_origins=["*"]` with configurable `ALLOWED_ORIGINS` environment variable (default: `http://localhost:5173,http://localhost:3000`)
- **Authentication Validation**: Pro mode now validates `Authorization: Bearer` token header before allowing Google Places API access. Returns `401` if unauthenticated
- **JWT_SECRET**: Added to `.env.example` for future token verification implementation

### Backend Improvements
- **Input Validation**: Added Pydantic `field_validator` decorators for all request fields:
  - `lat`: Must be between -90 and 90
  - `lng`: Must be between -180 and 180
  - `category`: Non-empty, stripped, max 100 characters
  - `radius`: Must be between 100 and 10000 meters
- **Rate Limiting**: Added in-memory rate limiter (10 requests/minute per IP) on `/api/analyze` endpoint. Returns `429` when exceeded
- **Logging**: Replaced all `print()` statements with Python `logging` module using structured format with timestamps and log levels
- **LLM JSON Parsing**: Extracted into dedicated `parse_llm_response()` function with regex-based markdown block stripping. Added specific `json.JSONDecodeError` exception handling
- **HTTP Error Handling**: Added `response.raise_for_status()` for Google Places and Overpass API calls

### Frontend Improvements
- **Missing Dependencies**: Added to `package.json`: `react-leaflet`, `leaflet`, `axios`, `tailwindcss`, `postcss`, `autoprefixer`
- **Environment-Based API URL**: Replaced hardcoded `http://localhost:8000` with `import.meta.env.VITE_API_URL` fallback
- **Complete SWOT Display**: Added missing Opportunities and Threats sections to the results UI
- **Page Title**: Changed from "Vite + React" to "mapah.id - AI Location Intelligence"

### Infrastructure
- **Docker**: Added `Dockerfile` for backend (Python 3.12-slim) and frontend (multi-stage Node 20 + Nginx)
- **Docker Compose**: Added `docker-compose.yml` with backend and frontend services, shared `.env` file
- **Nginx Config**: Added `frontend/nginx.conf` with SPA fallback routing and `/api/` proxy to backend
- **Docker Ignore**: Added `.dockerignore` files for both backend and frontend
- **PostCSS**: Added `postcss.config.js` required for Tailwind CSS compilation

### Testing
- **Backend Tests**: Created `backend/tests/test_main.py` with 12 test cases covering:
  - Root and app endpoint responses
  - Input validation (invalid lat, lng, empty category, invalid radius)
  - LLM JSON parsing (plain JSON, markdown blocks, invalid JSON)
  - Full analyze endpoint with mocked dependencies
  - Pro mode auth requirement and token validation

### Documentation
- **README**: Updated with accurate project structure tree, setup instructions for both backend and frontend, and environment variable documentation
- **Changelog**: This entry

## [2026-05-14] - LLM & Dynamic Search Integration
### Added
- **Kimi (Moonshot API) Integration**: Replaced the mock Viability Score and SWOT analysis logic with a real connection to the `moonshot-v1-8k` model via the `openai` SDK.
- **Dynamic Category Search**: The frontend UI was updated from a strict dropdown to a free-text input field. The backend now translates custom text inputs into a robust dynamic regex-based query for OpenStreetMap's Overpass API, enabling users to search for custom brands (like "Indomaret") or broad categories seamlessly.
- **Environment Management**: Configured robust `.env` handling for API keys (`KIMI_API_KEY`) and created `.env.example`.
- **Git Hygiene**: Formulated a comprehensive `.gitignore` ensuring that Python caches, virtual environments, and `node_modules` are safely excluded from source control.
- **Authentication & Landing Page**: Created a premium SaaS landing page with Google OAuth Sign-in integration. The app was split into a public marketing page (`/`) and a secured private dashboard (`/app`).
- **Premium Tier (Pro Plan) & Google Maps Engine**: Added a "Pro Mode" toggle and a Pricing section. Integrated the official Google Places API as a premium data source alternative to OpenStreetMap, allowing users with a `GOOGLE_MAPS_API_KEY` to pull exact context and POI data into the LLM.
