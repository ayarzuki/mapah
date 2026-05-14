import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="mapah.id API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    lat: float
    lng: float
    category: str
    radius: int = 2000

CATEGORY_MAPPING = {
    "Coffee Shop": "node['amenity'='cafe']",
    "Minimarket": "node['shop'='convenience']",
    "Laundromat": "node['shop'='laundry']",
    "Car Wash": "node['amenity'='car_wash']"
}

def fetch_overpass(query: str):
    overpass_url = "http://overpass-api.de/api/interpreter"
    try:
        response = httpx.get(overpass_url, params={'data': query}, timeout=15.0)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Overpass Error: {e}")
    return {"elements": []}

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/api/analyze")
def analyze_location(payload: AnalyzeRequest):
    # Try exact match first for predefined categories
    category_map = {k.lower(): v for k, v in CATEGORY_MAPPING.items()}
    cat_lower = payload.category.lower()
    
    if cat_lower in category_map:
        query_body = f"{category_map[cat_lower]}(around:{payload.radius},{payload.lat},{payload.lng});"
    else:
        # Dynamic regex search across names and common tags for custom inputs
        safe_cat = payload.category.replace('"', '\\"')
        query_body = f"""
        node["name"~"(?i){safe_cat}"](around:{payload.radius},{payload.lat},{payload.lng});
        way["name"~"(?i){safe_cat}"](around:{payload.radius},{payload.lat},{payload.lng});
        node["amenity"~"(?i){safe_cat}"](around:{payload.radius},{payload.lat},{payload.lng});
        node["shop"~"(?i){safe_cat}"](around:{payload.radius},{payload.lat},{payload.lng});
        """
    
    # 1. Fetch real Competitors from OpenStreetMap
    overpass_query_comp = f"""
    [out:json];
    (
      {query_body}
    );
    out center;
    """
    comp_data = fetch_overpass(overpass_query_comp)
    
    competitors = []
    for element in comp_data.get('elements', []):
        name = element.get('tags', {}).get('name', 'Unnamed Competitor')
        # Handle nodes vs ways
        lat = element.get('lat') or element.get('center', {}).get('lat')
        lon = element.get('lon') or element.get('center', {}).get('lon')
        
        if lat and lon:
            competitors.append({"name": name, "lat": lat, "lng": lon})
            
    # Limit to top 50 competitors to prevent overwhelming the map
    competitors = competitors[:50]
    
    # 2. Simple mock logic for AI until LLM is plugged in
    num_competitors = len(competitors)
    
    # Calculate a simple score: too many competitors = lower score, but some competitors = proven market
    if num_competitors == 0:
        score = 60 # Unproven market
        swot = {
            "strengths": ["First mover advantage"],
            "weaknesses": ["Unproven market demand"],
            "opportunities": ["Establish monopoly in this neighborhood"],
            "threats": ["Lack of foot traffic drivers"]
        }
    else:
        # Penalize heavily if more than 15 competitors
        score = max(10, 90 - (num_competitors * 3))
        swot = {
            "strengths": ["Proven demand for this business type in the area"],
            "weaknesses": [f"High saturation with {num_competitors} existing competitors within {payload.radius/1000}km"],
            "opportunities": ["Focus on quality or niche differentiation to steal market share"],
            "threats": ["Price wars with existing competitors"]
        }

    return {
        "status": "success",
        "score": score,
        "swot": swot,
        "competitors": competitors,
        "raw_competitor_count": num_competitors
    }
