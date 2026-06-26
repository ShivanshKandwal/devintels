# DevIntel — Developer Intelligence Platform

> _"Who are the developers getting hired into AI/ML roles in 2025, what separates them from the rest, and can we predict career trajectory from behavior signals alone?"_

## What This Project Does

DevIntel is an end-to-end developer intelligence platform that analyzes 65,000+ Stack Overflow survey responses to segment developers into behavioral clusters, predict churn risk, forecast technology adoption trends, and surface career insights through NLP — all deployed as a live React + FastAPI web application.

## Live Demo

🔗 **Frontend:** _[Deployment URL pending]_  
🔗 **API:** _[Deployment URL pending]_

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  React Frontend (Vite)               │
│  Landing │ Landscape │ Analyzer │ Forecast │ Tribe   │
└────────────────────┬────────────────────────────────┘
                     │ Axios (REST)
┌────────────────────▼────────────────────────────────┐
│              FastAPI Backend (Uvicorn)                │
│  /predict/churn │ /predict/career │ /search/similar  │
│  /data/clusters │ /data/forecast  │ /health          │
└──┬─────────┬──────────┬───────────┬─────────────────┘
   │         │          │           │
┌──▼──┐  ┌──▼───┐  ┌───▼──┐  ┌───▼────┐
│XGBoost│ │FAISS │  │Prophet│  │Evidently│
│Churn  │ │Index │  │ARIMA  │  │Drift   │
│Model  │ │(NLP) │  │Models │  │Monitor │
└──────┘  └──────┘  └──────┘  └────────┘
```

## The 5 Sub-Projects

| # | Module | Notebook | Description |
|---|--------|----------|-------------|
| 1 | **Segmentation & Churn** | `notebooks/02_segmentation/` | UMAP + HDBSCAN clustering, XGBoost churn model with SHAP |
| 2 | **Tech Forecasting** | `notebooks/03_forecasting/` | Prophet + ARIMA adoption trend forecasting (2022–2026) |
| 3 | **NLP Pipeline** | `notebooks/04_nlp/` | Sentence-transformer embeddings, BERTopic, FAISS retrieval |
| 4 | **Experimentation** | `notebooks/05_experimentation/` | Propensity matching, causal forest uplift modeling |
| 5 | **Deployment** | `src/api/` + `frontend/` | Full-stack React + FastAPI application |

## Dataset

- **Primary:** Stack Overflow Developer Survey 2024 (65,437 rows × 114 columns)
- **Secondary:** Stack Overflow Developer Survey 2023 (for year-over-year trends)
- **Secondary:** Stack Overflow Developer Survey 2022 (extend time horizon)

Download from [Stack Overflow Annual Developer Survey](https://survey.stackoverflow.co/) and place in `data/raw/`.

## Key Results

_Fill after running models:_

- Churn model: ROC-AUC = `0.XX` on held-out test set
- Segmentation: `N` distinct developer clusters (silhouette = `0.XX`)
- Top forecasted growth: Rust adoption to reach `XX%` by 2026
- AI tool users show `XX%` higher job satisfaction after propensity matching (p = `0.00X`)

## How to Run Locally

### Backend

```bash
cd devintels
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn src.api.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### MLflow UI

```bash
mlflow ui --port 5000
```

## Project Structure

```
devintels/
├── data/
│   ├── raw/                  # Original CSV files
│   ├── processed/            # Cleaned, merged datasets
│   └── features/             # Feature-engineered outputs
├── notebooks/                # Jupyter notebooks (EDA → Deployment)
├── src/
│   ├── data/                 # Data loading, cleaning pipelines
│   ├── features/             # Feature engineering modules
│   ├── models/               # Model training scripts
│   ├── nlp/                  # NLP pipeline
│   └── api/                  # FastAPI backend
├── frontend/                 # React + Vite app
├── mlflow/                   # Experiment tracking
├── monitoring/               # Evidently AI reports
├── tests/                    # pytest test suite
├── models/                   # Saved model artifacts (.pkl, .index)
├── requirements.txt
├── Dockerfile
├── Makefile
└── README.md
```

## Technologies Used

**Data & ML:** pandas, numpy, scikit-learn, XGBoost, LightGBM, Prophet, statsmodels, SHAP  
**NLP:** sentence-transformers, UMAP, HDBSCAN, BERTopic, FAISS  
**Experimentation:** scipy, pingouin, EconML (Causal Forest)  
**Backend:** FastAPI, uvicorn, MLflow, Evidently AI  
**Frontend:** React 18, Vite, Tailwind CSS, Recharts, shadcn/ui, Framer Motion  
