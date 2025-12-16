import os
import time
from typing import Dict, Any, List, Optional

import jwt
import pandas as pd
import numpy as np

import bentoml


# =========================
# Configuration
# =========================

MODEL_TAG = os.getenv("BENTO_MODEL_TAG", "admissions_lr:latest")

JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret_change_me")
JWT_ALGO = "HS256"
JWT_EXP_SECONDS = int(os.getenv("JWT_EXP_SECONDS", "3600"))

API_USER = os.getenv("API_USER", "admin")
API_PASS = os.getenv("API_PASS", "admin123")


# =========================
# JWT helpers
# =========================

def _create_token(username: str) -> str:
    now = int(time.time())
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + JWT_EXP_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def _verify_token(auth_header: Optional[str]) -> None:
    if not auth_header or not auth_header.startswith("Bearer "):
        raise PermissionError("Missing Authorization header")

    token = auth_header.split(" ", 1)[1]
    jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])


# =========================
# BentoML Service
# =========================

@bentoml.service(name="admissions_service")
class AdmissionsService:
    def __init__(self) -> None:
        # Récupérer l'objet BentoML Model (pour les metadata)
        model_ref = bentoml.models.get(MODEL_TAG)

        # Charger le modèle sklearn réel
        self.model = bentoml.sklearn.load_model(model_ref.tag)

        # Features attendues (ordre strict)
        self.features: List[str] = model_ref.info.metadata.get("features", [])

        if not self.features:
            raise RuntimeError(
                "Model metadata does not contain feature list. "
                "You must save features during training."
            )

    # -------------------------
    # LOGIN
    # -------------------------
    @bentoml.api
    def login(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        username = payload.get("username")
        password = payload.get("password")

        if username != API_USER or password != API_PASS:
            return {"error": "Invalid credentials", "status": 401}

        token = _create_token(username)

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": JWT_EXP_SECONDS,
        }

    # -------------------------
    # PREDICT
    # -------------------------
    @bentoml.api
    def predict(self, payload: Dict[str, Any], ctx) -> Dict[str, Any]:
        # Auth
        try:
            _verify_token(ctx.request.headers.get("authorization"))
        except Exception:
            return {"error": "Unauthorized", "status": 401}

        # Payload handling
        if isinstance(payload, dict) and "instances" in payload:
            rows = payload["instances"]
            if not isinstance(rows, list) or not rows:
                return {"error": "instances must be a non-empty list", "status": 400}
        else:
            rows = [payload]

        # DataFrame + validation
        try:
            df = pd.DataFrame(rows)
            missing = [c for c in self.features if c not in df.columns]
            if missing:
                return {"error": f"Missing columns: {missing}", "status": 400}

            df = df[self.features]
        except Exception as e:
            return {"error": f"Invalid payload: {e}", "status": 400}

        # Prediction
        preds = self.model.predict(df)
        preds = [float(x) for x in np.asarray(preds).ravel()]

        return {"predictions": preds}

