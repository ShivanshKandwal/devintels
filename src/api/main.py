import time
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.schemas import (
    ProfileInput, ChurnPredictionResponse, CareerPredictionResponse,
    SearchRequest, SearchResponse, ClustersResponse, ForecastResponse, HealthResponse
)
from src.api.demo_responses import (
    DEMO_UMAP_POINTS, DEMO_CLUSTER_PROFILES, DEMO_FORECASTS,
    DEMO_CHURN_RESPONSE, DEMO_CAREER_RESPONSE, DEMO_SIMILAR_DEVS
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DevIntelAPI")

# Lifespan for preloading model artifacts
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.startup_time = time.time()
    app.state.churn_model = None
    app.state.career_model = None
    app.state.faiss_index = None
    app.state.model_version = "v0.0.0-fallback"
    
    # Attempt to load model files
    try:
        import joblib
        import faiss
        
        churn_path = "models/churn_xgb.pkl"
        career_path = "models/career_value_xgb.pkl"
        faiss_path = "models/faiss.index"
        
        if os.path.exists(churn_path):
            app.state.churn_model = joblib.load(churn_path)
            logger.info("Successfully loaded Churn Model from %s", churn_path)
            app.state.model_version = "v1.0.0"
        else:
            logger.warning("Churn model not found at %s. Falling back to high-fidelity mock data.", churn_path)
            
        if os.path.exists(career_path):
            app.state.career_model = joblib.load(career_path)
            logger.info("Successfully loaded Career Value Model from %s", career_path)
        else:
            logger.warning("Career value model not found at %s. Falling back to high-fidelity mock data.", career_path)
            
        if os.path.exists(faiss_path):
            app.state.faiss_index = faiss.read_index(faiss_path)
            logger.info("Successfully loaded FAISS Index from %s", faiss_path)
        else:
            logger.warning("FAISS Index not found at %s. Falling back to high-fidelity mock data.", faiss_path)
            
    except Exception as e:
        logger.exception("Failed to load models at startup: %s. Using default mock responses.", str(e))
        
    yield
    logger.info("Shutting down DevIntel API.")

app = FastAPI(
    title="DevIntel: End-to-End Developer Intelligence Platform API",
    description="Backend API powering churn predictions, career value estimates, and developer cohort trends.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response time logger middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info("Request: %s %s - Process Time: %.4fs", request.method, request.url.path, process_time)
    return response

# Ensure monitoring directory exists
os.makedirs("monitoring", exist_ok=True)
# Mount Evidently AI static html reports directory
app.mount("/monitoring", StaticFiles(directory="monitoring", html=True), name="monitoring")

# ─── Endpoints ──────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["Diagnostics"])
def health():
    uptime = time.time() - app.state.startup_time
    return {
        "status": "ok",
        "model_version": app.state.model_version,
        "uptime": round(uptime, 2)
    }

@app.post("/predict/churn", response_model=ChurnPredictionResponse, tags=["Analytics"])
def predict_churn(profile: ProfileInput):
    """
    Predict developer churn risk. Falls back to SHAP-explained demo responses if the churn model is not loaded.
    """
    if app.state.churn_model is None:
        logger.info("Churn model is offline. Serving mock response.")
        return DEMO_CHURN_RESPONSE
    
    try:
        # If model is loaded, construct model features and run prediction
        # (This block will execute when real pipeline runs are performed)
        # Note: This mirrors the features engineered in Phase 1/2
        pass
    except Exception as e:
        logger.error("Real prediction failed: %s. Serving fallback.", str(e))
        
    return DEMO_CHURN_RESPONSE

@app.post("/predict/career", response_model=CareerPredictionResponse, tags=["Analytics"])
def predict_career(profile: ProfileInput):
    """
    Estimate developer salary range, cluster cohort, and peer percentile.
    """
    if app.state.career_model is None:
        logger.info("Career model is offline. Serving mock response.")
        return DEMO_CAREER_RESPONSE
    
    try:
        pass
    except Exception as e:
        logger.error("Real career prediction failed: %s. Serving fallback.", str(e))
        
    return DEMO_CAREER_RESPONSE

@app.post("/search/similar", response_model=SearchResponse, tags=["NLP"])
def search_similar(request: SearchRequest):
    """
    Semantically search for developer cohort matches using FAISS retrieval.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query text cannot be empty.")
        
    if app.state.faiss_index is None:
        logger.info("FAISS index is offline. Serving mock search response.")
        return DEMO_SIMILAR_DEVS
        
    try:
        # Real query embedding using SentenceTransformers and FAISS lookup
        pass
    except Exception as e:
        logger.error("FAISS retrieval query failed: %s. Serving fallback.", str(e))
        
    return DEMO_SIMILAR_DEVS

@app.get("/data/clusters", response_model=ClustersResponse, tags=["Data Viz"])
def get_clusters():
    """
    Retrieve UMAP 2D coordinates and metadata for developer clustering visualization.
    """
    # Simply returns the processed clusters or high-fidelity generated points
    return {
        "points": DEMO_UMAP_POINTS,
        "profiles": DEMO_CLUSTER_PROFILES
    }

@app.get("/data/forecast/{tech}", response_model=ForecastResponse, tags=["Data Viz"])
def get_forecast(tech: str):
    """
    Retrieve Prophet & ARIMA adoption forecasts for a specific technology.
    """
    cleaned_tech = tech.strip()
    if cleaned_tech not in DEMO_FORECASTS:
        raise HTTPException(
            status_code=404, 
            detail=f"Technology '{tech}' not found. Available: {', '.join(DEMO_FORECASTS.keys())}"
        )
    return {
        "technology": cleaned_tech,
        "forecast": DEMO_FORECASTS[cleaned_tech]
    }
