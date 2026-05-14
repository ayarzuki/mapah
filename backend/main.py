import os
import json
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

client = OpenAI(
    api_key=os.getenv("KIMI_API_KEY", ""),
    base_url="https://api.moonshot.cn/v1",
)

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
    
    # 2. Call Kimi LLM to generate SWOT and Score
    num_competitors = len(competitors)
    
    prompt = f"""
You are an expert location intelligence analyst.
I want to open a '{payload.category}' business at coordinates (Lat: {payload.lat}, Lng: {payload.lng}).
I found {num_competitors} direct competitors within a {payload.radius} meter radius.

Based on this data and your general knowledge about business viability, generate a strict JSON response with the following format:
{{
    "score": <integer 0-100 representing viability score>,
    "swot": {{
        "strengths": ["<strength1>", "<strength2>"],
        "weaknesses": ["<weakness1>", "<weakness2>"],
        "opportunities": ["<opportunity1>", "<opportunity2>"],
        "threats": ["<threat1>", "<threat2>"]
    }}
}}

Ensure your response is valid JSON and ONLY JSON. No markdown wrappers like ```json.
"""

    swot = {
        "strengths": [],
        "weaknesses": [f"{num_competitors} existing competitors within {payload.radius/1000}km"],
        "opportunities": [],
        "threats": []
    }
    score = 50

    try:
        completion = client.chat.completions.create(
            model="moonshot-v1-8k",
            messages=[
                {"role": "system", "content": "You are a JSON-only API. You must strictly return a valid JSON object."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        raw_content = completion.choices[0].message.content.strip()
        if raw_content.startswith("```json"):
            raw_content = raw_content[7:-3]
        elif raw_content.startswith("```"):
            raw_content = raw_content[3:-3]
            
        llm_response = json.loads(raw_content)
        score = llm_response.get("score", score)
        swot = llm_response.get("swot", swot)
        
    except Exception as e:
        print(f"Kimi API Error: {e}")
        # Fallback logic if LLM fails
        if num_competitors == 0:
            score = 60
            swot["strengths"] = ["First mover advantage"]
        else:
            score = max(10, 90 - (num_competitors * 3))
            swot["threats"] = ["Market saturation"]

    return {
        "status": "success",
        "score": score,
        "swot": swot,
        "competitors": competitors,
        "raw_competitor_count": num_competitors
    }
