import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app, parse_llm_response

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200


def test_read_app():
    response = client.get("/app")
    assert response.status_code == 200


def test_analyze_invalid_lat():
    response = client.post("/api/analyze", json={
        "lat": 100,
        "lng": 106.8123,
        "category": "Coffee Shop"
    })
    assert response.status_code == 422


def test_analyze_invalid_lng():
    response = client.post("/api/analyze", json={
        "lat": -6.2415,
        "lng": 200,
        "category": "Coffee Shop"
    })
    assert response.status_code == 422


def test_analyze_empty_category():
    response = client.post("/api/analyze", json={
        "lat": -6.2415,
        "lng": 106.8123,
        "category": "   "
    })
    assert response.status_code == 422


def test_analyze_invalid_radius():
    response = client.post("/api/analyze", json={
        "lat": -6.2415,
        "lng": 106.8123,
        "category": "Coffee Shop",
        "radius": 50
    })
    assert response.status_code == 422


def test_parse_llm_response_plain_json():
    raw = '{"score": 75, "swot": {"strengths": ["good"], "weaknesses": [], "opportunities": [], "threats": []}}'
    result = parse_llm_response(raw)
    assert result["score"] == 75
    assert result["swot"]["strengths"] == ["good"]


def test_parse_llm_response_markdown_json_block():
    raw = '```json\n{"score": 80, "swot": {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}}\n```'
    result = parse_llm_response(raw)
    assert result["score"] == 80


def test_parse_llm_response_markdown_block():
    raw = '```\n{"score": 60, "swot": {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}}\n```'
    result = parse_llm_response(raw)
    assert result["score"] == 60


def test_parse_llm_response_invalid_json():
    raw = "not valid json"
    with pytest.raises(Exception):
        parse_llm_response(raw)


@patch("main.fetch_overpass")
@patch("main.client")
def test_analyze_location_success(mock_openai_client, mock_overpass):
    mock_overpass.return_value = {"elements": []}

    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = '{"score": 70, "swot": {"strengths": ["test"], "weaknesses": [], "opportunities": [], "threats": []}}'
    mock_openai_client.chat.completions.create.return_value = mock_completion

    response = client.post("/api/analyze", json={
        "lat": -6.2415,
        "lng": 106.8123,
        "category": "Coffee Shop",
        "radius": 2000
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["score"] == 70
    assert "swot" in data
    assert "competitors" in data


def test_pro_mode_requires_auth():
    response = client.post("/api/analyze", json={
        "lat": -6.2415,
        "lng": 106.8123,
        "category": "Coffee Shop",
        "is_pro": True
    })
    assert response.status_code == 401


def test_pro_mode_with_auth():
    response = client.post("/api/analyze", json={
        "lat": -6.2415,
        "lng": 106.8123,
        "category": "Coffee Shop",
        "is_pro": True
    }, headers={"Authorization": "Bearer valid_token_123"})
    assert response.status_code in [200, 503]
