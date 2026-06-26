from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ProfileInput(BaseModel):
    years_coding: int = Field(..., example=8)
    primary_language: str = Field(..., example="TypeScript")
    org_size: str = Field(..., example="201-1,000 employees")
    country: str = Field(..., example="United States")
    uses_ai_tools: bool = Field(..., example=True)
    job_satisfaction: int = Field(..., example=4)
    remote_work: str = Field(..., example="Remote")
    career_stage: str = Field(..., example="Senior")

class ShapValue(BaseModel):
    feature: str
    value: float

class ChurnPredictionResponse(BaseModel):
    churn_probability: float
    risk_tier: str
    shap_values: List[ShapValue]
    recommendations: List[str]

class TrajectoryPoint(BaseModel):
    year: int
    salary: float

class ComparisonPoint(BaseModel):
    cluster: str
    salary: float
    yours: float

class CareerPredictionResponse(BaseModel):
    predicted_salary: float
    salary_range: List[float]
    percentile: float
    predicted_cluster: int
    cluster_name: str
    career_trajectory: List[TrajectoryPoint]
    comparison: List[ComparisonPoint]

class SearchRequest(BaseModel):
    query: str

class ClusterMatch(BaseModel):
    id: int
    name: str
    match_score: float
    description: str

class ClusterScore(BaseModel):
    name: str
    score: float

class SimilarDeveloper(BaseModel):
    id: str
    stage: str
    country: str
    language: str
    salary_range: str
    similarity: float

class SearchResponse(BaseModel):
    your_cluster: ClusterMatch
    cluster_scores: List[ClusterScore]
    similar_developers: List[SimilarDeveloper]

class ClusterPoint(BaseModel):
    x: float
    y: float
    cluster: int
    salary: int
    experience: int
    language: str
    stage: str

class ClusterProfile(BaseModel):
    id: int
    name: str
    count: int
    avgSalary: float
    avgExperience: float
    topTechs: List[str]
    description: str
    satisfaction: float
    remoteRatio: float
    churnRate: float

class ClustersResponse(BaseModel):
    points: List[ClusterPoint]
    profiles: List[ClusterProfile]

class ForecastPoint(BaseModel):
    year: int
    adoption: float
    low: Optional[float] = None
    high: Optional[float] = None
    isForecast: bool

class ForecastResponse(BaseModel):
    technology: str
    forecast: List[ForecastPoint]

class HealthResponse(BaseModel):
    status: str
    model_version: str
    uptime: float
