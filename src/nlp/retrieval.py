"""
NLP Retrieval Module.

- Build FAISS index from text embeddings
- Search: query text → top-10 similar developer profiles
- Save/load index to ``models/faiss.index``

Usage:
    python -m src.nlp.retrieval
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = PROJECT_ROOT / "models"


class ProfileSearchEngine:
    """FAISS-powered developer profile similarity search engine.

    Attributes
    ----------
    index:
        FAISS index (L2 or inner product).
    profiles:
        List of text profiles corresponding to index rows.
    embeddings:
        Raw embedding matrix.
    """

    def __init__(
        self,
        embeddings: np.ndarray | None = None,
        profiles: list[str] | None = None,
    ) -> None:
        self.index: Any = None
        self.embeddings: np.ndarray | None = embeddings
        self.profiles: list[str] = profiles or []
        self._faiss = None

    def _get_faiss(self) -> Any:
        """Import faiss lazily."""
        if self._faiss is None:
            try:
                import faiss
                self._faiss = faiss
            except ImportError:
                raise ImportError(
                    "faiss-cpu is required. Install with: pip install faiss-cpu"
                )
        return self._faiss

    def build_index(
        self,
        embeddings: np.ndarray | None = None,
        profiles: list[str] | None = None,
        normalize: bool = True,
    ) -> None:
        """Build FAISS index from embeddings.

        Parameters
        ----------
        embeddings:
            Matrix of shape (n, dim). If None, uses self.embeddings.
        profiles:
            Corresponding text profiles.
        normalize:
            Whether to L2-normalize for cosine similarity.
        """
        faiss = self._get_faiss()

        if embeddings is not None:
            self.embeddings = embeddings
        if profiles is not None:
            self.profiles = profiles

        if self.embeddings is None:
            raise ValueError("No embeddings provided.")

        emb = self.embeddings.astype(np.float32)
        if normalize:
            norms = np.linalg.norm(emb, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            emb = emb / norms

        dim = emb.shape[1]
        self.index = faiss.IndexFlatIP(dim)  # inner product = cosine on normalized vectors
        self.index.add(emb)

        logger.info("Built FAISS index: %d vectors, dim=%d", self.index.ntotal, dim)

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        normalize: bool = True,
    ) -> list[dict[str, Any]]:
        """Search for similar profiles.

        Parameters
        ----------
        query_embedding:
            Query vector of shape (dim,) or (1, dim).
        top_k:
            Number of results to return.
        normalize:
            Whether to L2-normalize the query.

        Returns
        -------
        List of dicts with keys: rank, score, profile_text, index.
        """
        if self.index is None:
            raise RuntimeError("Index not built. Call build_index() first.")

        query = query_embedding.astype(np.float32)
        if query.ndim == 1:
            query = query.reshape(1, -1)

        if normalize:
            norm = np.linalg.norm(query)
            if norm > 0:
                query = query / norm

        distances, indices = self.index.search(query, top_k)

        results: list[dict[str, Any]] = []
        for rank, (score, idx) in enumerate(zip(distances[0], indices[0])):
            if idx == -1:
                continue
            result: dict[str, Any] = {
                "rank": rank + 1,
                "score": round(float(score), 4),
                "index": int(idx),
            }
            if idx < len(self.profiles):
                result["profile_text"] = self.profiles[idx]
            results.append(result)

        return results

    def search_by_text(
        self,
        query_text: str,
        top_k: int = 10,
        model_name: str = "all-MiniLM-L6-v2",
    ) -> list[dict[str, Any]]:
        """Search by text query — encodes the query and searches.

        Parameters
        ----------
        query_text:
            Free-text query.
        top_k:
            Number of results.
        model_name:
            Sentence-transformer model for encoding the query.

        Returns
        -------
        List of result dicts.
        """
        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(model_name)
            query_emb = model.encode([query_text])[0]
        except ImportError:
            # Fallback: use TF-IDF vector (rough approximation)
            logger.warning(
                "sentence-transformers not available. "
                "Using random vector as fallback (results will be meaningless)."
            )
            dim = self.embeddings.shape[1] if self.embeddings is not None else 384
            query_emb = np.random.randn(dim).astype(np.float32)

        return self.search(query_emb, top_k=top_k)

    def save(self, models_dir: Path | None = None) -> Path:
        """Save the FAISS index to disk.

        Returns the path to the saved index file.
        """
        faiss = self._get_faiss()
        models_dir = models_dir or MODELS_DIR
        models_dir.mkdir(parents=True, exist_ok=True)

        index_path = models_dir / "faiss.index"
        faiss.write_index(self.index, str(index_path))
        logger.info("Saved FAISS index to %s", index_path)
        return index_path

    @classmethod
    def load(
        cls,
        models_dir: Path | None = None,
    ) -> "ProfileSearchEngine":
        """Load a saved FAISS index and associated data.

        Parameters
        ----------
        models_dir:
            Directory containing ``faiss.index``, ``text_embeddings.npy``,
            and ``text_profiles.json``.

        Returns
        -------
        Initialized ProfileSearchEngine.
        """
        try:
            import faiss as faiss_mod
        except ImportError:
            raise ImportError("faiss-cpu is required.")

        models_dir = models_dir or MODELS_DIR

        index_path = models_dir / "faiss.index"
        if not index_path.exists():
            raise FileNotFoundError(f"FAISS index not found at {index_path}")

        engine = cls()
        engine._faiss = faiss_mod
        engine.index = faiss_mod.read_index(str(index_path))

        # Load embeddings
        emb_path = models_dir / "text_embeddings.npy"
        if emb_path.exists():
            engine.embeddings = np.load(emb_path)

        # Load profiles
        profiles_path = models_dir / "text_profiles.json"
        if profiles_path.exists():
            with open(profiles_path, encoding="utf-8") as f:
                engine.profiles = json.load(f)

        logger.info("Loaded FAISS index (%d vectors)", engine.index.ntotal)
        return engine


def build_and_save_index(
    models_dir: Path | None = None,
) -> ProfileSearchEngine:
    """Build FAISS index from saved embeddings and profiles.

    Parameters
    ----------
    models_dir:
        Directory containing ``text_embeddings.npy`` and ``text_profiles.json``.

    Returns
    -------
    Initialized and saved ProfileSearchEngine.
    """
    models_dir = models_dir or MODELS_DIR

    emb_path = models_dir / "text_embeddings.npy"
    if not emb_path.exists():
        raise FileNotFoundError(
            f"Embeddings not found at {emb_path}. Run NLP pipeline first."
        )

    embeddings = np.load(emb_path)

    profiles: list[str] = []
    profiles_path = models_dir / "text_profiles.json"
    if profiles_path.exists():
        with open(profiles_path, encoding="utf-8") as f:
            profiles = json.load(f)

    engine = ProfileSearchEngine(embeddings=embeddings, profiles=profiles)
    engine.build_index()
    engine.save(models_dir)

    return engine


# ── CLI ───────────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    try:
        engine = build_and_save_index()
        print(f"\n✅  FAISS index built — {engine.index.ntotal} vectors")

        # Demo search
        results = engine.search_by_text("experienced Python developer using AI tools")
        print("\n🔍 Demo search: 'experienced Python developer using AI tools'")
        for r in results[:3]:
            print(f"   [{r['rank']}] score={r['score']:.3f}  {r.get('profile_text', '')[:80]}...")
    except FileNotFoundError as exc:
        print(f"\n❌  {exc}")


if __name__ == "__main__":
    main()
