.PHONY: setup data clean features train api frontend test monitor all

# ─── Environment ───────────────────────────────────────────
setup:
	python -m venv venv
	venv\Scripts\pip install -r requirements.txt

# ─── Data Pipeline ─────────────────────────────────────────
data-audit:
	python -m src.data.audit

clean:
	python -m src.data.clean

features:
	python -m src.features.engineer

merge:
	python -m src.data.merge_longitudinal

# ─── Models ────────────────────────────────────────────────
segment:
	python -m src.models.segmentation

churn:
	python -m src.models.churn_model

career-value:
	python -m src.models.career_value

forecast:
	python -m src.models.forecast

nlp:
	python -m src.nlp.pipeline

retrieval-index:
	python -m src.nlp.retrieval

experiment:
	python -m src.models.experiment

# ─── API & Frontend ───────────────────────────────────────
api:
	uvicorn src.api.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

# ─── Tracking & Monitoring ────────────────────────────────
mlflow:
	mlflow ui --port 5000

monitor:
	python -m src.api.monitoring

# ─── Testing ──────────────────────────────────────────────
test:
	pytest tests/ -v --tb=short

test-api:
	pytest tests/test_api.py -v

# ─── Full Pipeline ────────────────────────────────────────
pipeline: clean features segment churn career-value forecast nlp retrieval-index experiment
	@echo "Full pipeline complete."

all: setup pipeline
	@echo "Setup + pipeline complete."
