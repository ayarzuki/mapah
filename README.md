# mapah.id

mapah.id is an automated market research web application designed to evaluate the viability of opening a specific business in a chosen location. By analyzing competitor density, local demographics, and point-of-interest (POI) context, the application provides entrepreneurs with AI-powered insights to make informed business decisions.

## Core Features
- **Interactive Location Selection:** Search by address, coordinate, or drop a pin on an interactive map.
- **Competitor Analysis:** Automated scanning of existing competitors within a configurable radius (e.g., 1km, 3km, 5km).
- **Traffic Generator Mapping:** Identification of nearby foot-traffic drivers (schools, universities, transit hubs, offices).
- **AI-Powered Viability Score:** Integration with Large Language Models (LLMs) to generate a SWOT analysis and an actionable Viability Score (0-100).
- **Property Finder Overlay:** Visualize available commercial properties for rent or sale directly on the map.
- **Dual Data Engines:** Free tier uses OpenStreetMap (Overpass API), Pro tier uses Google Places API.

## Project Structure
```
mapah/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   └── static/              # Landing page and app HTML
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   └── main.jsx         # Entry point
│   ├── package.json         # Node dependencies
│   ├── vite.config.js       # Vite configuration
│   └── tailwind.config.js   # Tailwind CSS config
├── docs/                    # Project documentation
├── .env.example             # Environment variable template
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env  # Edit with your API keys
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables
Copy `.env.example` to `.env` and configure:
- `KIMI_API_KEY` - Kimi/Moonshot API key for LLM analysis
- `GOOGLE_MAPS_API_KEY` - Google Places API key (Pro mode)
- `ALLOWED_ORIGINS` - Comma-separated list of allowed CORS origins
- `JWT_SECRET` - Secret key for authentication

## Documentation
Please refer to the [Technical Specification](docs/technical_specification.md) for full details on the system architecture, API dependencies, and implementation phases.
