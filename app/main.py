from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY, CONTENT_TYPE_LATEST

import numpy as np
import pickle
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import List
from threading import Lock

# ---------------- Logging setup ----------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ml-inference")

# ---------------- Environment configuration ----------------
MODEL_PATH = os.getenv("MODEL_PATH")
FEATURES_N = int(os.getenv("FEATURES_N", "20"))
ZSCORE_THRESHOLD = float(os.getenv("ZSCORE_THRESHOLD", "3.0"))
PROBA_THRESHOLD = float(os.getenv("PROBA_THRESHOLD", "0.5"))

# ---------------- Prometheus metrics (with registry) ----------------
prediction_counter = Counter(
    "predictions_total",
    "Total number of predictions",
    registry=REGISTRY
)

prediction_latency = Histogram(
    "prediction_latency_seconds",
    "Prediction latency in seconds",
    registry=REGISTRY
)

drift_counter = Counter(
    "drift_detected_total",
    "Total number of detected drifts",
    registry=REGISTRY
)

# ---------------- App initialization ----------------
app = FastAPI(title="ML Inference Service")

# ---------------- Global state ----------------
model = None
feature_stats = None
_state_lock = Lock()
_drift_events = 0


# ---------------- Request/Response models ----------------
class PredictionRequest(BaseModel):
    features: List[float]


class PredictionResponse(BaseModel):
    prediction: int
    probability: float
    drift_detected: bool
    timestamp: str


# ---------------- Model loading ----------------
def load_model() -> None:
    """Load model from disk and reset feature statistics."""
    global model, feature_stats

    base_dir = Path(__file__).resolve().parent
    default_model_path = base_dir / "models" / "model.pkl"
    model_path = Path(MODEL_PATH) if MODEL_PATH else default_model_path

    try:
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        logger.info(f"Model loaded from: {model_path}")

        with _state_lock:
            feature_stats = {
                "mean": np.zeros(FEATURES_N, dtype=np.float32),
                "std": np.ones(FEATURES_N, dtype=np.float32),
                "count": 0,
            }

        logger.info(
            f"Z-score drift detection enabled | FEATURES_N={FEATURES_N} | z_threshold={ZSCORE_THRESHOLD}"
        )
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise


@app.on_event("startup")
async def startup_event():
    load_model()


# ---------------- Input validation ----------------
def _quick_sanity(x: np.ndarray) -> None:
    """Raise an error if input data is invalid."""
    if x.ndim != 2 or x.shape[1] != FEATURES_N:
        raise ValueError(f"Expected {FEATURES_N} features, got {x.shape[1] if x.ndim == 2 else 'not 2D'}")
    if not np.all(np.isfinite(x)):
        raise ValueError("Input features contain NaN/Inf values.")


# ---------------- Drift detection: Z-score ----------------
def detect_drift(features: np.ndarray) -> bool:
    global feature_stats, _drift_events

    with _state_lock:
        # initialization
        if feature_stats["count"] == 0:
            feature_stats["mean"] = features.astype(np.float32).copy()
            feature_stats["std"] = np.ones_like(features, dtype=np.float32)
        else:
            alpha = 0.1
            feature_stats["mean"] = (1 - alpha) * feature_stats["mean"] + alpha * features
            feature_stats["std"] = (1 - alpha) * feature_stats["std"] + alpha * np.abs(features - feature_stats["mean"])

        feature_stats["count"] += 1
        z_scores = np.abs((features - feature_stats["mean"]) / (feature_stats["std"] + 1e-6))
        zscore_drift = bool(np.any(z_scores > ZSCORE_THRESHOLD))

    if zscore_drift:
        with _state_lock:
            _drift_events += 1
        drift_counter.inc()
        logger.warning(f"Drift detected: max_z={float(np.max(z_scores)):.2f}, threshold_z={ZSCORE_THRESHOLD}")

    return zscore_drift


# ---------------- Prediction ----------------
def _predict_impl(features: List[float]) -> dict:
    X = np.array(features, dtype=np.float32).reshape(1, -1)
    _quick_sanity(X)

    # Classification
    if hasattr(model, "predict_proba"):
        proba = float(model.predict_proba(X)[0][1])
        y_pred = int(proba > PROBA_THRESHOLD)
    else:
        y_pred = int(model.predict(X)[0])
        proba = 1.0

    drift = detect_drift(X[0])
    return {"prediction": y_pred, "probability": proba, "drift_detected": drift}


# ---------------- Routes ----------------
@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    logger.info(f"Received request with {len(request.features)} features")
    with prediction_latency.time():
        try:
            result = _predict_impl(request.features)
            prediction_counter.inc()
        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    resp = PredictionResponse(
        prediction=result["prediction"],
        probability=result["probability"],
        drift_detected=result["drift_detected"],
        timestamp=datetime.now().isoformat(),
    )
    logger.info(
        f"Response: class={resp.prediction}, probability={resp.probability:.3f}, drift={resp.drift_detected}"
    )
    return resp


@app.get("/metrics")
async def metrics():
    """Expose Prometheus metrics."""
    return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
async def health():
    with _state_lock:
        stats = None if feature_stats is None else {"count": feature_stats["count"]}
    return {
        "status": "running",
        "model_loaded": bool(model is not None),
        "features_n": FEATURES_N,
        "zscore_threshold": ZSCORE_THRESHOLD,
        "proba_threshold": PROBA_THRESHOLD,
        "drift_events": _drift_events,
        "feature_stats": stats,
    }


@app.get("/")
async def root():
    return {
        "service": "ML Inference API",
        "version": "2.4.1",
        "description": "Machine Learning inference service with Z-score drift detection (EMA + 3σ).",
        "endpoints": ["/predict", "/metrics", "/health"],
    }