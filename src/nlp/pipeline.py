"""
NLP Pipeline Module.

- Create synthetic text profiles from structured survey data
- Generate sentence-transformer embeddings
- UMAP + HDBSCAN on embeddings
- BERTopic topic modeling
- Save embeddings and topics

Usage:
    python -m src.nlp.pipeline
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FEATURES_DIR = PROJECT_ROOT / "data" / "features"
MODELS_DIR = PROJECT_ROOT / "models"


def generate_text_profile(row: pd.Series) -> str:
    """Convert a structured survey row into a natural-language profile string.

    This synthesized text enables embedding-based similarity search and
    topic modeling over structured developer data.

    Parameters
    ----------
    row:
        A single row from the feature-engineered DataFrame.

    Returns
    -------
    A descriptive paragraph about the developer.
    """
    parts: list[str] = []

    # Career
    career_stage = row.get("career_stage", "unknown")
    yrs = row.get("years_code_pro_num", 0)
    if pd.notna(yrs) and yrs > 0:
        parts.append(f"A {career_stage} developer with {int(yrs)} years of professional experience.")
    else:
        parts.append(f"A {career_stage} developer.")

    # Education
    ed = row.get("ed_level_num", 0)
    if pd.notna(ed):
        ed_map = {1: "primary", 2: "secondary", 3: "some college",
                  4: "associate", 5: "bachelor's", 6: "master's", 7: "professional/PhD"}
        ed_str = ed_map.get(int(ed), "")
        if ed_str:
            parts.append(f"Education: {ed_str} degree.")

    # Tech stack
    lang_count = row.get("lang_count", 0)
    db_count = row.get("db_count", 0)
    if lang_count > 0 or db_count > 0:
        parts.append(f"Works with {int(lang_count)} languages and {int(db_count)} databases.")

    uses_python = row.get("uses_python", 0)
    uses_js = row.get("uses_javascript", 0)
    uses_cloud = row.get("uses_cloud", 0)
    uses_ai = row.get("uses_ai_tools", 0)

    tech_notes: list[str] = []
    if uses_python:
        tech_notes.append("Python")
    if uses_js:
        tech_notes.append("JavaScript")
    if uses_cloud:
        tech_notes.append("cloud platforms")
    if uses_ai:
        tech_notes.append("AI development tools")
    if tech_notes:
        parts.append(f"Key technologies: {', '.join(tech_notes)}.")

    # Work context
    remote = row.get("is_remote", 0)
    large_org = row.get("is_large_org", 0)
    if remote:
        parts.append("Works remotely.")
    if large_org:
        parts.append("Employed at a large organization.")

    # Learning
    learning_div = row.get("learning_diversity", 0)
    if learning_div > 5:
        parts.append("Highly active learner with diverse learning sources.")
    elif learning_div > 2:
        parts.append("Moderate learner using several sources.")

    # Satisfaction
    sat = row.get("job_sat_score", 3)
    if pd.notna(sat):
        sat_map = {1: "very dissatisfied", 2: "dissatisfied", 3: "neutral",
                   4: "satisfied", 5: "very satisfied"}
        sat_str = sat_map.get(int(sat), "neutral")
        parts.append(f"Job satisfaction: {sat_str}.")

    # AI sentiment
    ai_sent = row.get("ai_sentiment_score", 3)
    if pd.notna(ai_sent) and ai_sent >= 4:
        parts.append("Favorable attitude toward AI tools.")
    elif pd.notna(ai_sent) and ai_sent <= 1:
        parts.append("Skeptical of AI tools.")

    # Country / region
    continent = row.get("continent", "Unknown")
    if continent != "Unknown":
        parts.append(f"Based in {continent}.")

    return " ".join(parts)


def generate_embeddings(
    texts: list[str],
    model_name: str = "all-MiniLM-L6-v2",
    batch_size: int = 64,
) -> np.ndarray:
    """Generate sentence-transformer embeddings.

    Parameters
    ----------
    texts:
        List of text strings.
    model_name:
        HuggingFace model name.
    batch_size:
        Encoding batch size.

    Returns
    -------
    2D numpy array of shape (n_texts, embedding_dim).
    """
    try:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading sentence-transformer model '%s'...", model_name)
        model = SentenceTransformer(model_name)

        logger.info("Encoding %d texts (batch_size=%d)...", len(texts), batch_size)
        embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=True)
        return np.array(embeddings)
    except ImportError:
        logger.warning(
            "sentence-transformers not installed. "
            "Falling back to TF-IDF embeddings."
        )
        return _fallback_tfidf_embeddings(texts)


def _fallback_tfidf_embeddings(texts: list[str], n_components: int = 64) -> np.ndarray:
    """Generate TF-IDF + SVD embeddings as a fallback."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import TruncatedSVD

    vectorizer = TfidfVectorizer(max_features=5000, stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(texts)

    n_comp = min(n_components, tfidf_matrix.shape[1] - 1, tfidf_matrix.shape[0] - 1)
    svd = TruncatedSVD(n_components=n_comp, random_state=42)
    embeddings = svd.fit_transform(tfidf_matrix)
    return embeddings


def run_embedding_clustering(
    embeddings: np.ndarray,
    n_components: int = 2,
    min_cluster_size: int = 30,
) -> tuple[np.ndarray, np.ndarray]:
    """Run UMAP + HDBSCAN on embeddings.

    Returns
    -------
    Tuple of (umap_embedding_2d, cluster_labels).
    """
    try:
        import umap
        import hdbscan
    except ImportError:
        logger.error("umap-learn / hdbscan not installed.")
        raise

    logger.info("Running UMAP on %d embeddings...", len(embeddings))
    reducer = umap.UMAP(
        n_components=n_components,
        n_neighbors=15,
        min_dist=0.1,
        metric="cosine",
        random_state=42,
    )
    umap_emb = reducer.fit_transform(embeddings)

    logger.info("Running HDBSCAN...")
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        metric="euclidean",
    )
    labels = clusterer.fit_predict(umap_emb)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    logger.info("Found %d embedding clusters", n_clusters)

    return umap_emb, labels


def run_topic_model(
    texts: list[str],
    embeddings: np.ndarray | None = None,
    n_topics: int | None = None,
) -> dict[str, Any]:
    """Run BERTopic topic modeling.

    Parameters
    ----------
    texts:
        List of text profiles.
    embeddings:
        Precomputed embeddings (optional, BERTopic will compute if missing).
    n_topics:
        Number of topics (None for automatic).

    Returns
    -------
    Dict with topics, topic_info, and representative docs.
    """
    try:
        from bertopic import BERTopic
    except ImportError:
        logger.warning("BERTopic not installed — skipping topic modeling.")
        return {"topics": [], "n_topics": 0}

    logger.info("Running BERTopic on %d documents...", len(texts))

    try:
        topic_model = BERTopic(
            nr_topics=n_topics,
            verbose=False,
            calculate_probabilities=False,
        )

        if embeddings is not None:
            topics, _ = topic_model.fit_transform(texts, embeddings=embeddings)
        else:
            topics, _ = topic_model.fit_transform(texts)

        topic_info = topic_model.get_topic_info()
        topic_info_records = topic_info.to_dict(orient="records")

        # Get representative keywords per topic
        topic_keywords: dict[int, list[str]] = {}
        for tid in set(topics):
            if tid == -1:
                continue
            try:
                words = topic_model.get_topic(tid)
                topic_keywords[tid] = [w[0] for w in words[:10]]
            except Exception:
                pass

        return {
            "topics": [int(t) for t in topics],
            "n_topics": len(set(topics)) - (1 if -1 in topics else 0),
            "topic_info": topic_info_records,
            "topic_keywords": {str(k): v for k, v in topic_keywords.items()},
        }
    except Exception as exc:
        logger.error("BERTopic failed: %s", exc)
        return {"topics": [], "n_topics": 0, "error": str(exc)}


def run_nlp_pipeline(
    features_dir: Path | None = None,
    models_dir: Path | None = None,
    max_rows: int = 5000,
) -> dict[str, Any]:
    """Run the full NLP pipeline.

    Parameters
    ----------
    features_dir:
        Feature data directory.
    models_dir:
        Where to save outputs.
    max_rows:
        Maximum rows to process (for speed).

    Returns
    -------
    Dict with embedding info, cluster info, and topic info.
    """
    features_dir = features_dir or FEATURES_DIR
    models_dir = models_dir or MODELS_DIR
    models_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    parquet_files = sorted(features_dir.glob("*_features.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No feature files in {features_dir}")

    dfs = [pd.read_parquet(f) for f in parquet_files]
    df = pd.concat(dfs, ignore_index=True)

    if len(df) > max_rows:
        df = df.sample(n=max_rows, random_state=42).reset_index(drop=True)
        logger.info("Sampled to %d rows for NLP pipeline", max_rows)

    # 1. Generate text profiles
    logger.info("Generating text profiles...")
    texts = [generate_text_profile(row) for _, row in df.iterrows()]

    # 2. Embeddings
    embeddings = generate_embeddings(texts)

    # Save embeddings
    emb_path = models_dir / "text_embeddings.npy"
    np.save(emb_path, embeddings)
    logger.info("Saved embeddings to %s (shape: %s)", emb_path, embeddings.shape)

    # Save texts for retrieval
    texts_path = models_dir / "text_profiles.json"
    with open(texts_path, "w", encoding="utf-8") as f:
        json.dump(texts, f)

    # 3. UMAP + HDBSCAN on embeddings
    try:
        umap_emb, nlp_labels = run_embedding_clustering(embeddings)

        nlp_clusters_path = models_dir / "nlp_clusters.parquet"
        cluster_df = pd.DataFrame({
            "umap_x": umap_emb[:, 0],
            "umap_y": umap_emb[:, 1],
            "nlp_cluster": nlp_labels,
        })
        cluster_df.to_parquet(nlp_clusters_path, index=False)
    except Exception as exc:
        logger.warning("Embedding clustering failed: %s", exc)
        nlp_labels = np.zeros(len(texts), dtype=int)

    # 4. Topic modeling
    topic_result = run_topic_model(texts, embeddings)

    # Save topics
    topics_path = models_dir / "topics.json"
    with open(topics_path, "w", encoding="utf-8") as f:
        json.dump(topic_result, f, indent=2, default=str)

    return {
        "n_profiles": len(texts),
        "embedding_shape": list(embeddings.shape),
        "n_nlp_clusters": len(set(nlp_labels)) - (1 if -1 in nlp_labels else 0),
        "n_topics": topic_result.get("n_topics", 0),
    }


# ── CLI ───────────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    try:
        result = run_nlp_pipeline()
        print(f"\n✅  NLP pipeline complete.")
        print(f"   Profiles: {result['n_profiles']}")
        print(f"   Embedding shape: {result['embedding_shape']}")
        print(f"   Topics: {result['n_topics']}")
    except FileNotFoundError as exc:
        print(f"\n❌  {exc}")


if __name__ == "__main__":
    main()
