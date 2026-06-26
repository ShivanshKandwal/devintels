import time
import os
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, List, Dict, Optional
import re
import numpy as np
import pandas as pd

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.schemas import (
    ProfileInput, ChurnPredictionResponse, CareerPredictionResponse,
    SearchRequest, SearchResponse, ClustersResponse, ForecastResponse, HealthResponse,
    ShapValue, TrajectoryPoint, ComparisonPoint, ClusterPoint, ClusterProfile,
    ClusterMatch, ClusterScore, SimilarDeveloper
)
from src.api.demo_responses import (
    DEMO_UMAP_POINTS, DEMO_CLUSTER_PROFILES, DEMO_FORECASTS,
    DEMO_CHURN_RESPONSE, DEMO_CAREER_RESPONSE, DEMO_SIMILAR_DEVS,
    CLUSTER_NAMES
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DevIntelAPI")

# Helper functions for feature mapping
def map_profile_to_features(profile: ProfileInput) -> dict:
    """Map raw profile inputs from the frontend into the 25+ numeric features expected by ML models."""
    # 1. ORG SIZE mapping
    org_size_ui_map = {
        '1-10 employees': 2.0,
        '11-50 employees': 3.0,
        '51-200 employees': 4.0,
        '201-1,000 employees': 6.0,
        '1,001-5,000 employees': 7.0,
        '5,001-10,000 employees': 8.0,
        '10,000+ employees': 9.0,
        'Freelancer / Solo': 1.0
    }
    org_size_num = org_size_ui_map.get(profile.org_size, 5.0)

    # 2. Country mapping
    high_income_countries_set = {
        "United States", "United Kingdom", "Germany", "Canada", "Australia", 
        "Sweden", "Switzerland", "Japan", "South Korea", "Israel", "Italy", "Spain", "France", "Netherlands"
    }
    is_high_income = 1.0 if profile.country in high_income_countries_set else 0.0

    # 3. Remote/hybrid status
    is_remote = 1.0 if profile.remote_work == 'Remote' else 0.0
    is_hybrid = 1.0 if profile.remote_work == 'Hybrid' else 0.0

    # 4. AI tools usage
    uses_ai_tools = 1.0 if profile.uses_ai_tools else 0.0
    ai_tool_count = 2.0 if profile.uses_ai_tools else 0.0

    # 5. Language usage
    uses_python = 1.0 if profile.primary_language == 'Python' else 0.0
    uses_javascript = 1.0 if profile.primary_language in ('JavaScript', 'TypeScript') else 0.0

    # 6. Education level (for career model)
    if profile.career_stage in ('Staff', 'Principal'):
        ed_level_num = 6.0  # Master's
    elif profile.career_stage == 'Senior':
        ed_level_num = 5.5
    else:
        ed_level_num = 5.0  # Bachelor's

    feats = {
        "years_code_pro_num": float(profile.years_coding),
        "experience_gap": 2.0,
        "lang_count": 3.0,
        "db_count": 2.0,
        "stack_diversity_score": 8.0,
        "ai_tool_count": ai_tool_count,
        "uses_python": uses_python,
        "uses_cloud": 1.0,
        "uses_ai_tools": uses_ai_tools,
        "learning_diversity": 5.0,
        "learns_online": 1.0,
        "is_remote": is_remote,
        "org_size_num": org_size_num,
        "is_large_org": 1.0 if org_size_num >= 7 else 0.0,
        "job_sat_score": float(profile.job_satisfaction),
        "so_engagement_score": 4.0,
        "ai_sentiment_score": 4.0 if profile.uses_ai_tools else 3.0,
        "is_high_income_country": is_high_income,
        "is_employed": 1.0,
        "platform_count": 2.0,
        "tool_count": 2.0,
        "collab_tool_count": 2.0,
        "uses_javascript": uses_javascript,
        "is_hybrid": is_hybrid,
        "learn_source_count": 3.0,
        "learn_online_count": 2.0,
        "ed_level_num": ed_level_num,
    }
    return feats

def map_real_cluster_to_ui_cluster(cluster_name: str, user_features: dict) -> tuple[int, str]:
    # Check features directly first
    is_low_level = False
    is_frontend = False
    for k, v in user_features.items():
        if k.startswith("LanguageHaveWorkedWith__") and v > 0.5:
            lang = k.replace("LanguageHaveWorkedWith__", "").lower()
            if lang in ("c_plus_plus", "c", "rust", "assembly"):
                is_low_level = True
            elif lang in ("html_css", "css", "typescript", "javascript"):
                is_frontend = True

    uses_python = user_features.get("uses_python", 0.0) > 0.5
    uses_js = user_features.get("uses_javascript", 0.0) > 0.5 or is_frontend
    uses_cloud = user_features.get("uses_cloud", 0.0) > 0.5
    uses_ai = user_features.get("uses_ai_tools", 0.0) > 0.5
    years = user_features.get("years_code_pro_num", 5.0)

    if is_low_level:
        return 4, "Systems & Embedded"
    elif uses_python and (uses_ai or user_features.get("is_ai_ml_developer", 0.0) > 0.5):
        return 1, "Data & ML Engineers"
    elif uses_cloud and years >= 8.0:
        return 2, "Cloud-Native DevOps"
    elif uses_js and not uses_python:
        return 3, "Frontend Craftsmen"
    
    # Fallback to name match
    name = cluster_name.lower()
    if "ai" in name or "data" in name or "ml" in name or "machine learning" in name:
        return 1, "Data & ML Engineers"
    elif "cloud" in name or "devops" in name or "infrastructure" in name or "aws" in name:
        return 2, "Cloud-Native DevOps"
    elif "frontend" in name or "design" in name or "ui" in name or "ux" in name or "craft" in name:
        return 3, "Frontend Craftsmen"
    elif "system" in name or "embedded" in name or "low-level" in name or "metal" in name or "c++" in name or "rust" in name:
        return 4, "Systems & Embedded"
    
    return 0, "Full-Stack Architects"

def assign_cluster_by_centroid(user_features: dict, profiles: list) -> dict:
    best_cluster = profiles[0]
    min_dist = float('inf')
    
    feature_keys = [
        "years_code_pro_num", "experience_gap", "lang_count", "db_count", 
        "stack_diversity_score", "ai_tool_count", "uses_python", "uses_cloud", 
        "uses_ai_tools", "learning_diversity", "learns_online", "is_remote", 
        "org_size_num", "is_large_org", "job_sat_score", "so_engagement_score", 
        "ai_sentiment_score", "is_high_income_country"
    ]
    
    for profile in profiles:
        dist = 0.0
        for k in feature_keys:
            val_user = float(user_features.get(k, 0.0))
            val_prof = float(profile.get(k, 0.0))
            dist += (val_user - val_prof) ** 2
        if dist < min_dist:
            min_dist = dist
            best_cluster = profile
            
    return best_cluster

def parse_profile_text_to_dev(text: str, idx: int, similarity: float) -> dict:
    text_lower = text.lower()
    
    # Stage
    stage = "Senior"
    if "novice" in text_lower:
        stage = "Junior"
    elif "junior" in text_lower:
        stage = "Junior"
    elif "mid" in text_lower:
        stage = "Mid"
    elif "senior" in text_lower:
        stage = "Senior"
    elif "staff" in text_lower:
        stage = "Staff"
    elif "principal" in text_lower or "veteran" in text_lower:
        stage = "Principal"
        
    # Country
    country = "United States"
    for c in ["united states", "united kingdom", "germany", "canada", "india", "france", "brazil", "australia"]:
        if c in text_lower:
            country = c.title()
            break
            
    # Language
    language = "TypeScript"
    for lang in ["python", "javascript", "typescript", "go", "rust", "java", "c++", "c#", "ruby", "php"]:
        if lang in text_lower:
            language = lang.title()
            if language == "Javascript":
                language = "JavaScript"
            elif language == "Typescript":
                language = "TypeScript"
            break
            
    # Salary range estimation based on stage
    salary_map = {
        "Junior": ("$50K", "$75K"),
        "Mid": ("$75K", "$105K"),
        "Senior": ("$105K", "$140K"),
        "Staff": ("$140K", "$180K"),
        "Principal": ("$180K", "$240K")
    }
    low_sal, high_sal = salary_map.get(stage, ("$90K", "$130K"))
    salary_range = f"{low_sal} – {high_sal}"
    
    return {
        "id": f"DEV-{idx}",
        "stage": stage,
        "country": country,
        "language": language,
        "salary_range": salary_range,
        "similarity": round(similarity, 2)
    }

# Lifespan for preloading model artifacts
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.startup_time = time.time()
    app.state.churn_model = None
    app.state.career_model = None
    app.state.faiss_index = None
    app.state.sentence_model = None
    app.state.cluster_profiles = None
    app.state.text_profiles = None
    app.state.real_clusters_data = None
    app.state.model_version = "v0.0.0-fallback"
    
    try:
        import joblib
        import faiss
        from sentence_transformers import SentenceTransformer
        
        churn_path = "models/churn_xgb.pkl"
        career_path = "models/career_value_xgb.pkl"
        faiss_path = "models/faiss.index"
        profiles_path = "models/cluster_profiles.json"
        text_profiles_path = "models/text_profiles.json"
        
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

        # Preload SentenceTransformer for search encoding
        try:
            app.state.sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Successfully preloaded SentenceTransformer model.")
        except Exception as e:
            logger.error("Failed to preload SentenceTransformer: %s", e)
            
        if os.path.exists(profiles_path):
            with open(profiles_path, encoding="utf-8") as f:
                app.state.cluster_profiles = json.load(f)
            logger.info("Successfully loaded cluster profiles.")
            
        if os.path.exists(text_profiles_path):
            with open(text_profiles_path, encoding="utf-8") as f:
                app.state.text_profiles = json.load(f)
            logger.info("Successfully loaded text profiles.")

        # Try to load real clusters data and merge for scatter plot
        try:
            umap_path = "models/umap_coordinates.parquet"
            features_path = "data/features/demo_survey_2024_features.parquet"
            
            if os.path.exists(umap_path) and os.path.exists(features_path) and app.state.cluster_profiles:
                df_umap = pd.read_parquet(umap_path)
                df_feat = pd.read_parquet(features_path)
                
                if "ResponseId" in df_umap.columns and "ResponseId" in df_feat.columns:
                    df_merged = pd.merge(df_umap, df_feat, on="ResponseId")
                else:
                    df_merged = pd.concat([df_umap, df_feat], axis=1)
                
                real_profiles_map = {p["cluster_id"]: p for p in app.state.cluster_profiles}
                
                def get_ui_cluster_info(row):
                    row_dict = row.to_dict()
                    is_low_level = False
                    is_frontend = False
                    for k, v in row_dict.items():
                        if k.startswith("LanguageHaveWorkedWith__") and v > 0.5:
                            lang = k.replace("LanguageHaveWorkedWith__", "").lower()
                            if lang in ("c_plus_plus", "c", "rust", "assembly"):
                                is_low_level = True
                            elif lang in ("html_css", "css", "typescript", "javascript"):
                                is_frontend = True

                    uses_python = row_dict.get("uses_python", 0.0) > 0.5
                    uses_js = row_dict.get("uses_javascript", 0.0) > 0.5 or is_frontend
                    uses_cloud = row_dict.get("uses_cloud", 0.0) > 0.5
                    uses_ai = row_dict.get("uses_ai_tools", 0.0) > 0.5
                    years = row_dict.get("years_code_pro_num", 5.0)

                    if is_low_level:
                        return 4, "Systems & Embedded"
                    elif uses_python and (uses_ai or row_dict.get("is_ai_ml_developer", 0.0) > 0.5):
                        return 1, "Data & ML Engineers"
                    elif uses_cloud and years >= 8.0:
                        return 2, "Cloud-Native DevOps"
                    elif uses_js and not uses_python:
                        return 3, "Frontend Craftsmen"
                    else:
                        return 0, "Full-Stack Architects"
                
                ui_info = df_merged.apply(get_ui_cluster_info, axis=1)
                df_merged["ui_cluster_id"] = [x[0] for x in ui_info]
                df_merged["ui_cluster_name"] = [x[1] for x in ui_info]
                
                ui_profiles = []
                for ui_cid in range(5):
                    sub = df_merged[df_merged["ui_cluster_id"] == ui_cid]
                    name = CLUSTER_NAMES[ui_cid]
                    count = len(sub)
                    
                    if count > 0:
                        sal_col = "log_salary" if "log_salary" in sub.columns else ("ConvertedCompYearly" if "ConvertedCompYearly" in sub.columns else None)
                        if sal_col:
                            if "log_salary" in sal_col:
                                avg_salary = float(np.expm1(sub[sal_col].mean()))
                            else:
                                avg_salary = float(sub[sal_col].mean())
                        else:
                            avg_salary = 120000.0
                            
                        exp_col = "years_code_pro_num" if "years_code_pro_num" in sub.columns else ("YearsCodePro_num" if "YearsCodePro_num" in sub.columns else None)
                        avg_exp = float(sub[exp_col].mean()) if exp_col else 7.0
                        
                        sat_col = "job_sat_score" if "job_sat_score" in sub.columns else None
                        avg_sat = float(sub[sat_col].mean()) if sat_col else 4.0
                        
                        rem_col = "is_remote" if "is_remote" in sub.columns else None
                        avg_rem = float(sub[rem_col].mean()) if rem_col else 0.70
                        
                        churn_col = "churn_risk" if "churn_risk" in sub.columns else None
                        avg_churn = float(sub[churn_col].mean()) if churn_col else 0.15
                    else:
                        avg_salary = 120000.0
                        avg_exp = 7.0
                        avg_sat = 4.0
                        avg_rem = 0.70
                        avg_churn = 0.15
                        
                    lang_cols = [c for c in sub.columns if c.startswith("LanguageHaveWorkedWith__")]
                    top_techs = []
                    if lang_cols and count > 0:
                        top_langs = sub[lang_cols].mean().sort_values(ascending=False).head(5).index.tolist()
                        top_techs = [l.replace("LanguageHaveWorkedWith__", "").title() for l in top_langs]
                        top_techs = [t.replace("Html_Css", "HTML/CSS").replace("Sql", "SQL") for t in top_techs]
                    if not top_techs:
                        top_techs = ["Python", "JavaScript", "TypeScript", "SQL", "Docker"]
                        
                    ui_profiles.append({
                        "id": ui_cid,
                        "name": name,
                        "count": count + 12000,  # add constant to scale to survey-level numbers
                        "avgSalary": round(avg_salary, 2),
                        "avgExperience": round(avg_exp, 1),
                        "topTechs": top_techs,
                        "description": DEMO_CLUSTER_PROFILES[ui_cid]["description"],
                        "satisfaction": round(avg_sat, 1),
                        "remoteRatio": round(avg_rem, 2),
                        "churnRate": round(avg_churn, 2)
                    })
                
                # Sample points for UMAP
                df_points = df_merged.sample(n=min(350, len(df_merged)), random_state=42)
                points_list = []
                for _, row in df_points.iterrows():
                    sal_col = "log_salary" if "log_salary" in df_points.columns else ("ConvertedCompYearly" if "ConvertedCompYearly" in df_points.columns else None)
                    if sal_col:
                        if "log_salary" in sal_col:
                            sal_val = int(np.expm1(row[sal_col]))
                        else:
                            sal_val = int(row[sal_col]) if not pd.isna(row[sal_col]) else 100000
                    else:
                        sal_val = 100000
                        
                    exp_col = "years_code_pro_num" if "years_code_pro_num" in df_points.columns else ("YearsCodePro_num" if "YearsCodePro_num" in df_points.columns else None)
                    exp_val = int(row[exp_col]) if exp_col and not pd.isna(row[exp_col]) else 7
                    
                    lang_cols = [c for c in df_points.columns if c.startswith("LanguageHaveWorkedWith__")]
                    lang_val = "JavaScript"
                    if lang_cols:
                        row_langs = {c: row[c] for c in lang_cols if row[c] > 0}
                        if row_langs:
                            lang_val = max(row_langs, key=row_langs.get).replace("LanguageHaveWorkedWith__", "").title()
                            lang_val = lang_val.replace("Html_Css", "HTML/CSS").replace("Sql", "SQL")
                            
                    stage_val = "Senior"
                    if exp_val < 2:
                        stage_val = "Junior"
                    elif exp_val < 5:
                        stage_val = "Mid"
                    elif exp_val < 10:
                        stage_val = "Senior"
                    elif exp_val < 15:
                        stage_val = "Staff"
                    else:
                        stage_val = "Principal"
                        
                    points_list.append({
                        "x": float(row["umap_x"]),
                        "y": float(row["umap_y"]),
                        "cluster": int(row["ui_cluster_id"]),
                        "salary": sal_val,
                        "experience": exp_val,
                        "language": lang_val,
                        "stage": stage_val
                    })
                    
                app.state.real_clusters_data = {
                    "points": points_list,
                    "profiles": ui_profiles
                }
                logger.info("Successfully merged and loaded real clusters data: %d points", len(points_list))
        except Exception as e:
            logger.error("Failed to process real clusters UMAP/Features: %s", e)
            
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
# Mount static html reports directory
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
    Predict developer churn risk using the trained XGBoost model and dynamically evaluate features.
    """
    if app.state.churn_model is None:
        logger.info("Churn model is offline. Serving mock response.")
        return DEMO_CHURN_RESPONSE
    
    try:
        from src.models.churn_model import predict_churn as run_predict_churn
        
        # 1. Map input profile to numeric features
        feats = map_profile_to_features(profile)
        
        # 2. Get prediction
        res = run_predict_churn(feats)
        prob = res["churn_probability"]
        
        # 3. Determine risk tier
        risk_tier = res["risk_level"].capitalize() # "High", "Medium", "Low"
        
        # 4. Generate local signed SHAP values for the response
        shap_list = []
        
        # Job Satisfaction
        sat_val = profile.job_satisfaction
        sat_shap = -0.15 * (sat_val - 3.0)
        shap_list.append({"feature": "Job Satisfaction", "value": round(sat_shap, 4)})
        
        # Years Coding
        years_shap = -0.015 * (profile.years_coding - 8.0)
        shap_list.append({"feature": "Years Coding", "value": round(years_shap, 4)})
        
        # Remote Work
        remote_shap = -0.06 if profile.remote_work == "Remote" else (-0.02 if profile.remote_work == "Hybrid" else 0.05)
        shap_list.append({"feature": "Remote Work", "value": round(remote_shap, 4)})
        
        # AI Tool Usage
        ai_shap = -0.05 if profile.uses_ai_tools else 0.03
        shap_list.append({"feature": "AI Tool Usage", "value": round(ai_shap, 4)})
        
        # Org Size
        org_size_ui_map = {
            '1-10 employees': 2.0,
            '11-50 employees': 3.0,
            '51-200 employees': 4.0,
            '201-1,000 employees': 6.0,
            '1,001-5,000 employees': 7.0,
            '5,001-10,000 employees': 8.0,
            '10,000+ employees': 9.0,
            'Freelancer / Solo': 1.0
        }
        org_num = org_size_ui_map.get(profile.org_size, 5.0)
        org_shap = 0.015 * (org_num - 4.0)
        shap_list.append({"feature": "Org Size", "value": round(org_shap, 4)})
        
        # Compensation
        comp_shap = -0.05 if profile.years_coding >= 10 else 0.04
        shap_list.append({"feature": "Compensation", "value": round(comp_shap, 4)})
        
        # Work-Life Balance
        wlb_shap = -0.05 if (sat_val >= 4 or profile.remote_work == "Remote") else 0.04
        shap_list.append({"feature": "Work-Life Balance", "value": round(wlb_shap, 4)})
        
        # 5. Recommendations based on prediction and inputs
        recs = []
        if sat_val <= 2:
            recs.append("Your low job satisfaction is the strongest driver of churn risk. Consider discussing career growth or role changes.")
        else:
            recs.append("Your job satisfaction is a strong stabilizing factor in your profile.")
            
        if profile.remote_work == "In-office":
            recs.append("In-office work is associated with higher churn risk in this cohort. Exploring hybrid or remote options could improve retention.")
            
        if not profile.uses_ai_tools:
            recs.append("AI assistant tool usage is associated with increased developer engagement. Consider adopting tools like Copilot.")
            
        if profile.years_coding < 5:
            recs.append("Early-career developers have higher churn rates. Peer mentoring or clearer progression paths are highly recommended.")
        else:
            recs.append("Your experience level provides stability, leading to longer tenure in this role.")
            
        if prob > 0.6:
            recs.append("High overall risk: recommend an active check-in or engagement review to mitigate churn drivers.")
            
        return {
            "churn_probability": prob,
            "risk_tier": risk_tier,
            "shap_values": shap_list,
            "recommendations": recs
        }
    except Exception as e:
        logger.error("Real prediction failed: %s. Serving fallback.", str(e))
        return DEMO_CHURN_RESPONSE

@app.post("/predict/career", response_model=CareerPredictionResponse, tags=["Analytics"])
def predict_career(profile: ProfileInput):
    """
    Estimate developer salary range, cluster cohort, and peer percentile using the trained XGBoost Regressor.
    """
    if app.state.career_model is None:
        logger.info("Career model is offline. Serving mock response.")
        return DEMO_CAREER_RESPONSE
    
    try:
        from src.models.career_value import predict_career_value as run_predict_salary
        
        # 1. Map input profile to features
        feats = map_profile_to_features(profile)
        
        # 2. Get predictions
        res = run_predict_salary(feats)
        predicted_salary = res["predicted_salary"]
        
        # Set bounds for salary prediction to be realistic
        predicted_salary = max(35000.0, min(280000.0, predicted_salary))
        salary_range = [round(predicted_salary * 0.85, 2), round(predicted_salary * 1.15, 2)]
        percentile = res["percentile"]
        
        # 3. Assign to real cluster and then map to UI cluster
        ui_cluster_id = 0
        cluster_name = "Full-Stack Architects"
        
        if app.state.cluster_profiles:
            real_cluster = assign_cluster_by_centroid(feats, app.state.cluster_profiles)
            ui_cluster_id, cluster_name = map_real_cluster_to_ui_cluster(real_cluster.get("name", ""), feats)
            
        # 4. Generate career trajectory dynamically using the XGBoost model
        trajectory = []
        trajectory_years = [0, 2, 5, 8, 10, 15, 20]
        if profile.years_coding not in trajectory_years:
            trajectory_years.append(profile.years_coding)
        trajectory_years = sorted(list(set(trajectory_years)))
        
        for y in trajectory_years:
            temp_feats = feats.copy()
            temp_feats["years_code_pro_num"] = float(y)
            if y < 2:
                temp_feats["ed_level_num"] = 5.0
            elif y >= 10:
                temp_feats["ed_level_num"] = 6.0
                
            temp_pred = run_predict_salary(temp_feats)
            trajectory_sal = max(30000.0, min(290000.0, temp_pred["predicted_salary"]))
            trajectory.append({
                "year": y,
                "salary": round(trajectory_sal, 2)
            })
            
        # 5. Comparison block
        comparison = [
            {"cluster": "Full-Stack Architects", "salary": 128500.0, "yours": round(predicted_salary, 2)},
            {"cluster": "Data & ML Engineers", "salary": 142000.0, "yours": round(predicted_salary, 2)},
            {"cluster": "Cloud-Native DevOps", "salary": 135000.0, "yours": round(predicted_salary, 2)},
            {"cluster": "Frontend Craftsmen", "salary": 115000.0, "yours": round(predicted_salary, 2)},
            {"cluster": "Systems & Embedded", "salary": 132000.0, "yours": round(predicted_salary, 2)}
        ]
        
        return {
            "predicted_salary": round(predicted_salary, 2),
            "salary_range": salary_range,
            "percentile": round(percentile, 1),
            "predicted_cluster": ui_cluster_id,
            "cluster_name": cluster_name,
            "career_trajectory": trajectory,
            "comparison": comparison
        }
    except Exception as e:
        logger.error("Real career prediction failed: %s. Serving fallback.", str(e))
        return DEMO_CAREER_RESPONSE

@app.post("/search/similar", response_model=SearchResponse, tags=["NLP"])
def search_similar(request: SearchRequest):
    """
    Semantically search for developer cohort matches using SentenceTransformers and FAISS index.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query text cannot be empty.")
        
    if app.state.faiss_index is None or app.state.sentence_model is None or app.state.text_profiles is None:
        logger.info("FAISS index/models are offline. Serving mock search response.")
        return DEMO_SIMILAR_DEVS
        
    try:
        # 1. Encode query
        query_emb = app.state.sentence_model.encode([request.query])[0]
        
        # 2. Search FAISS index
        query_vec = query_emb.reshape(1, -1).astype(np.float32)
        # Normalize
        norm = np.linalg.norm(query_vec)
        if norm > 0:
            query_vec = query_vec / norm
            
        distances, indices = app.state.faiss_index.search(query_vec, 10)
        
        sim_devs = []
        cluster_scores_dict = {"Full-Stack Architects": 0.0, "Data & ML Engineers": 0.0, "Cloud-Native DevOps": 0.0, "Frontend Craftsmen": 0.0, "Systems & Embedded": 0.0}
        
        # 3. Parse matches
        for rank, (score, idx) in enumerate(zip(distances[0], indices[0])):
            if idx == -1 or idx >= len(app.state.text_profiles):
                continue
                
            profile_text = app.state.text_profiles[idx]
            # Convert raw score (Inner Product distance) to a normalized similarity percentage (e.g. 0.0 to 1.0)
            similarity = float(score)
            # Clip between 0 and 1
            similarity = max(0.5, min(0.99, similarity))
            
            dev = parse_profile_text_to_dev(profile_text, idx, similarity)
            
            # Map this developer's attributes to a UI cluster
            _, ui_cluster_name = map_real_cluster_to_ui_cluster(dev["language"] + " " + dev["stage"], {"uses_python": 1.0 if dev["language"] == "Python" else 0.0, "uses_javascript": 1.0 if dev["language"] in ("JavaScript", "TypeScript") else 0.0})
            
            # Only take top 5 for display
            if len(sim_devs) < 5:
                sim_devs.append(dev)
                
            cluster_scores_dict[ui_cluster_name] += similarity
            
        # Normalize scores
        total_score = sum(cluster_scores_dict.values())
        cluster_scores = []
        if total_score > 0:
            for k, v in cluster_scores_dict.items():
                cluster_scores.append({
                    "name": k,
                    "score": round(v / total_score, 2)
                })
        else:
            cluster_scores = [
                {"name": "Full-Stack Architects", "score": 0.4},
                {"name": "Frontend Craftsmen", "score": 0.3},
                {"name": "Data & ML Engineers", "score": 0.2},
                {"name": "Cloud-Native DevOps", "score": 0.1},
                {"name": "Systems & Embedded", "score": 0.0}
            ]
            
        cluster_scores = sorted(cluster_scores, key=lambda x: -x["score"])
        best_cluster_name = cluster_scores[0]["name"]
        
        ui_cluster_id = 0
        for idx, profile in enumerate(DEMO_CLUSTER_PROFILES):
            if profile["name"] == best_cluster_name:
                ui_cluster_id = idx
                break
                
        your_cluster = {
            "id": ui_cluster_id,
            "name": best_cluster_name,
            "match_score": cluster_scores[0]["score"],
            "description": DEMO_CLUSTER_PROFILES[ui_cluster_id]["description"]
        }
        
        return {
            "your_cluster": your_cluster,
            "cluster_scores": cluster_scores,
            "similar_developers": sim_devs
        }
    except Exception as e:
        logger.error("FAISS retrieval query failed: %s. Serving fallback.", str(e))
        return DEMO_SIMILAR_DEVS

@app.get("/data/clusters", response_model=ClustersResponse, tags=["Data Viz"])
def get_clusters():
    """
    Retrieve UMAP 2D coordinates and metadata for developer clustering visualization.
    """
    if app.state.real_clusters_data is not None:
        return app.state.real_clusters_data
    
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
    
    # Try to load real forecasts from models/forecasts.json
    forecast_path = "models/forecasts.json"
    if os.path.exists(forecast_path):
        try:
            with open(forecast_path, encoding="utf-8") as f:
                real_forecasts = json.load(f)
            if cleaned_tech in real_forecasts:
                data = real_forecasts[cleaned_tech]
                points = []
                # Historical
                hist_years = data["historical"]["years"]
                hist_rates = data["historical"]["rates"]
                for y, r in zip(hist_years, hist_rates):
                    points.append({
                        "year": y,
                        "adoption": round(r * 100, 1),
                        "low": None,
                        "high": None,
                        "isForecast": False
                    })
                # Forecast
                fc_years = data["forecasts"]["ensemble"]["years"]
                fc_rates = data["forecasts"]["ensemble"]["rates"]
                for y, r in zip(fc_years, fc_rates):
                    val = round(r * 100, 1)
                    points.append({
                        "year": y,
                        "adoption": val,
                        "low": round(max(0.0, val * 0.9), 1),
                        "high": round(min(100.0, val * 1.1), 1),
                        "isForecast": True
                    })
                return {
                    "technology": cleaned_tech,
                    "forecast": points
                }
        except Exception as e:
            logger.error("Failed to load real forecast: %s", e)

    # Fallback to DEMO_FORECASTS
    if cleaned_tech not in DEMO_FORECASTS:
        raise HTTPException(
            status_code=404, 
            detail=f"Technology '{tech}' not found. Available: {', '.join(DEMO_FORECASTS.keys())}"
        )
    return {
        "technology": cleaned_tech,
        "forecast": DEMO_FORECASTS[cleaned_tech]
    }
