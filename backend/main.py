import os
import json
import re
import logging
from datetime import datetime
from collections import defaultdict
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv
from openai import OpenAI
import httpx

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=os.getenv("KIMI_API_KEY", ""),
    base_url="https://api.moonshot.cn/v1",
)

app = FastAPI(title="mapah.id API")

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Simple in-memory rate limiter
rate_limit_store: dict = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 10  # requests per window

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")


def check_rate_limit(client_ip: str) -> bool:
    now = datetime.now()
    requests = rate_limit_store[client_ip]
    rate_limit_store[client_ip] = [t for t in requests if (now - t).total_seconds() < RATE_LIMIT_WINDOW]
    if len(rate_limit_store[client_ip]) >= RATE_LIMIT_MAX:
        return False
    rate_limit_store[client_ip].append(now)
    return True


def verify_auth_token(request: Request) -> bool:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        if token and token != "mock_jwt_token_123":
            logger.info("Auth token present for request from %s", request.client.host)
            return True
    return False


class AnalyzeRequest(BaseModel):
    lat: float
    lng: float
    category: str
    radius: int = 2000
    is_pro: bool = False

    @field_validator("lat")
    @classmethod
    def validate_lat(cls, v):
        if not -90 <= v <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("lng")
    @classmethod
    def validate_lng(cls, v):
        if not -180 <= v <= 180:
            raise ValueError("Longitude must be between -180 and 180")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Category cannot be empty")
        if len(v) > 100:
            raise ValueError("Category must be 100 characters or less")
        return v

    @field_validator("radius")
    @classmethod
    def validate_radius(cls, v):
        if not 100 <= v <= 10000:
            raise ValueError("Radius must be between 100 and 10000 meters")
        return v


CATEGORY_MAPPING = {
    "Coffee Shop": "node['amenity'='cafe']",
    "Minimarket": "node['shop'='convenience']",
    "Laundromat": "node['shop'='laundry']",
    "Car Wash": "node['amenity'='car_wash']"
}


def fetch_google_places(category: str, lat: float, lng: float, radius: int):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "keyword": category,
        "key": GOOGLE_MAPS_API_KEY
    }
    try:
        response = httpx.get(url, params=params, timeout=15.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error("Google Places HTTP error: %s", e)
    except Exception as e:
        logger.error("Google Places error: %s", e)
    return {"results": []}


def fetch_overpass(query: str):
    overpass_url = "http://overpass-api.de/api/interpreter"
    headers = {"User-Agent": "mapah.id/1.0"}
    try:
        response = httpx.post(overpass_url, data=query, headers=headers, timeout=30.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error("Overpass HTTP error: %s", e)
    except Exception as e:
        logger.error("Overpass error: %s", e)
    return {"elements": []}


def parse_llm_response(raw_content: str) -> dict:
    raw_content = raw_content.strip()
    patterns = [
        r"^```json\s*(.*?)\s*```$",
        r"^```\s*(.*?)\s*```$",
    ]
    for pattern in patterns:
        match = re.match(pattern, raw_content, re.DOTALL)
        if match:
            raw_content = match.group(1).strip()
            break

    return json.loads(raw_content)


@app.get("/")
def read_root():
    return FileResponse("static/index.html")


@app.get("/app")
def read_app():
    return FileResponse("static/app.html")


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/api/analyze")
def analyze_location(payload: AnalyzeRequest, request: Request):
    client_ip = request.client.host

    if not check_rate_limit(client_ip):
        logger.warning("Rate limit exceeded for IP: %s", client_ip)
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

    if payload.is_pro:
        if not verify_auth_token(request):
            raise HTTPException(status_code=401, detail="Authentication required for Pro mode.")
        if not GOOGLE_MAPS_API_KEY:
            raise HTTPException(status_code=503, detail="Google Maps API not configured.")

    logger.info(
        "Analyze request from %s: lat=%s, lng=%s, category=%s, radius=%s, is_pro=%s",
        client_ip, payload.lat, payload.lng, payload.category, payload.radius, payload.is_pro
    )

    competitors = []

    if payload.is_pro and GOOGLE_MAPS_API_KEY:
        comp_data = fetch_google_places(payload.category, payload.lat, payload.lng, payload.radius)
        for element in comp_data.get('results', []):
            name = element.get('name', 'Unnamed Competitor')
            loc = element.get('geometry', {}).get('location', {})
            clat = loc.get('lat')
            clng = loc.get('lng')
            if clat and clng:
                competitors.append({"name": name, "lat": clat, "lng": clng})
    else:
        category_map = {k.lower(): v for k, v in CATEGORY_MAPPING.items()}
        cat_lower = payload.category.lower()

        if cat_lower in category_map:
            query_body = f"{category_map[cat_lower]}(around:{payload.radius},{payload.lat},{payload.lng});"
        else:
            safe_cat = payload.category.replace('"', '\\"')
            query_body = f"""
            node["name"~"(?i){safe_cat}"](around:{payload.radius},{payload.lat},{payload.lng});
            way["name"~"(?i){safe_cat}"](around:{payload.radius},{payload.lat},{payload.lng});
            node["amenity"~"(?i){safe_cat}"](around:{payload.radius},{payload.lat},{payload.lng});
            node["shop"~"(?i){safe_cat}"](around:{payload.radius},{payload.lat},{payload.lng});
            """

        overpass_query_comp = f"""
        [out:json];
        (
          {query_body}
        );
        out center;
        """
        comp_data = fetch_overpass(overpass_query_comp)

        for element in comp_data.get('elements', []):
            name = element.get('tags', {}).get('name', 'Unnamed Competitor')
            clat = element.get('lat') or element.get('center', {}).get('lat')
            clng = element.get('lon') or element.get('center', {}).get('lon')

            if clat and clng:
                competitors.append({"name": name, "lat": clat, "lng": clng})

    competitors = competitors[:50]

    num_competitors = len(competitors)
    logger.info("Found %d competitors for category '%s'", num_competitors, payload.category)

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
        "weaknesses": [f"{num_competitors} existing competitors within {payload.radius/1000:.1f}km"],
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
        llm_response = parse_llm_response(raw_content)
        score = llm_response.get("score", score)
        swot = llm_response.get("swot", swot)
        logger.info("LLM analysis completed successfully")

    except json.JSONDecodeError as e:
        logger.error("Failed to parse LLM JSON response: %s", e)
        if num_competitors == 0:
            score = 60
            swot["strengths"] = ["First mover advantage"]
        else:
            score = max(10, 90 - (num_competitors * 3))
            swot["threats"] = ["Market saturation"]
    except Exception as e:
        logger.error("Kimi API error: %s", e)
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
