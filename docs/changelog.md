# Changelog

All notable changes to the mapah.id project will be documented in this file.

## [2026-05-14] - LLM & Dynamic Search Integration
### Added
- **Kimi (Moonshot API) Integration**: Replaced the mock Viability Score and SWOT analysis logic with a real connection to the `moonshot-v1-8k` model via the `openai` SDK.
- **Dynamic Category Search**: The frontend UI was updated from a strict dropdown to a free-text input field. The backend now translates custom text inputs into a robust dynamic regex-based query for OpenStreetMap's Overpass API, enabling users to search for custom brands (like "Indomaret") or broad categories seamlessly.
- **Environment Management**: Configured robust `.env` handling for API keys (`KIMI_API_KEY`) and created `.env.example`.
- **Git Hygiene**: Formulated a comprehensive `.gitignore` ensuring that Python caches, virtual environments, and `node_modules` are safely excluded from source control.
