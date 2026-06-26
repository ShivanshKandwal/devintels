import pytest
from fastapi.testclient import TestClient
from src.api.main import app

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model_version" in data
    assert "uptime" in data

def test_predict_churn(client):
    payload = {
        "years_coding": 8,
        "primary_language": "TypeScript",
        "org_size": "201-1,000 employees",
        "country": "United States",
        "uses_ai_tools": True,
        "job_satisfaction": 4,
        "remote_work": "Remote",
        "career_stage": "Senior"
    }
    response = client.post("/predict/churn", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "churn_probability" in data
    assert "risk_tier" in data
    assert "shap_values" in data
    assert "recommendations" in data
    assert len(data["shap_values"]) > 0

def test_predict_career(client):
    payload = {
        "years_coding": 8,
        "primary_language": "TypeScript",
        "org_size": "201-1,000 employees",
        "country": "United States",
        "uses_ai_tools": True,
        "job_satisfaction": 4,
        "remote_work": "Remote",
        "career_stage": "Senior"
    }
    response = client.post("/predict/career", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "predicted_salary" in data
    assert "salary_range" in data
    assert "percentile" in data
    assert "predicted_cluster" in data
    assert "career_trajectory" in data
    assert "comparison" in data

def test_search_similar(client):
    payload = {"query": "I am a Python ML researcher with 5 years experience"}
    response = client.post("/search/similar", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "your_cluster" in data
    assert "cluster_scores" in data
    assert "similar_developers" in data
    assert len(data["similar_developers"]) == 5

def test_search_similar_empty(client):
    payload = {"query": "   "}
    response = client.post("/search/similar", json=payload)
    assert response.status_code == 400

def test_get_clusters(client):
    response = client.get("/data/clusters")
    assert response.status_code == 200
    data = response.json()
    assert "points" in data
    assert "profiles" in data
    assert len(data["profiles"]) == 5
    assert len(data["points"]) > 0

def test_get_forecast(client):
    response = client.get("/data/forecast/Python")
    assert response.status_code == 200
    data = response.json()
    assert data["technology"] == "Python"
    assert "forecast" in data
    assert len(data["forecast"]) == 5

def test_get_forecast_not_found(client):
    response = client.get("/data/forecast/NonExistentTechXYZ")
    assert response.status_code == 404

