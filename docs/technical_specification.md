# Technical Specification: Location-Based Business Viability Analyzer

## 1. Product Overview
**Goal:** A web application that automates market research for entrepreneurs. It allows users to input a specific location and business type, and automatically evaluates the viability of opening that business by analyzing competitor density, local demographics, and point-of-interest (POI) context.

## 2. Core Features & Functional Requirements
*   **Interactive Location & Category Selection:**
    *   Users can search by address, drop a pin on an interactive map, or use current GPS coordinates.
    *   Users select their intended business category (e.g., Coffee Shop, Laundromat, Minimarket, Car Wash).
*   **Automated Competitor Analysis:**
    *   Query OpenStreetMap (Overpass API) to locate existing competitors within a dynamic radius.
    *   Uses dynamic regex searching to match specific brand names (e.g. "Indomaret") or generic amenity tags automatically.
*   **Traffic Generator & Context Mapping:**
    *   Identify nearby "anchors" or traffic generators (e.g., schools, universities, office buildings, public transit hubs, residential complexes) to estimate potential footfall.
*   **AI-Powered Market Analysis (Kimi LLM Integration):**
    *   Feeds the aggregated geospatial and competitor data into the Kimi API (`moonshot-v1-8k`) using the `openai` Python client.
    *   Generate a structured report including:
        *   **Viability Score (0-100)**
        *   **SWOT Analysis** (Strengths, Weaknesses, Opportunities, Threats)
        *   **Actionable Insights** (e.g., "High competitor density, but low average ratings suggest an opportunity for a premium quality offering.")
*   **Property Finder Integration:**
    *   Overlay available commercial properties or land for sale/rent in that exact area (leveraging the `megurim` scraper project).

## 3. System Architecture & Tech Stack
*   **Frontend (User Interface):**
    *   **Framework:** React (Next.js) or Vite.
    *   **Mapping:** Leaflet.js or Mapbox GL JS for rich, interactive map plotting.
    *   **Styling:** Tailwind CSS (for modern, dynamic, and premium UI components).
*   **Backend (Data Aggregation & AI Engine):**
    *   **Framework:** Python (FastAPI) – ideal for handling asynchronous data scraping and AI processing.
    *   **LLM API:** DeepSeek API or Kimi API for generating the analytical reports.
    *   **Geospatial Data Sources:** Google Places API, Overpass API (OpenStreetMap), or Foursquare API.
*   **Database (Optional for MVP):**
    *   PostgreSQL with PostGIS for caching location queries, or MongoDB for storing raw JSON API responses to reduce external API costs.

## 4. System Workflow
1.  **Input:** User queries `[-6.2415, 106.8123]` (Jakarta Selatan) for a `Coffee Shop`.
2.  **Data Fetch:** Backend queries mapping APIs for all coffee shops within a 2km radius + queries for nearby office buildings and transit stations.
3.  **LLM Processing:** Backend compiles a summary (e.g., *"15 competitors found, average rating 4.2. 3 large office buildings nearby"*) and sends a prompt to the LLM.
4.  **Output Visualization:** Frontend displays the interactive map with custom pins for competitors vs. traffic generators, alongside the AI's Viability Score and detailed analysis.

## 5. Next Steps for Execution
1.  **Select Map API:** Decide between Google Places (highly accurate but paid) or OpenStreetMap/Overpass (free but slightly less detailed).
2.  **Setup Backend:** Create the Python API endpoints to aggregate this data.
3.  **Build UI:** Initialize the React/Vite project and create the interactive map view.
