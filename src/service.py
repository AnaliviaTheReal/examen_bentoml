import os
import time
from typing import Dict, Any, List, Optional, Tuple
import jwt
import pandas as pd
import numpy as np
import bentoml


# =========================
# Configuration
# =========================

MODEL_TAG = os.getenv("BENTO_MODEL_TAG", "admissions_lr:le2t6ww2qsz6scsl")
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


def _verify_token(auth_header: Optional[str]) -> Tuple[bool, str]:
    """Return (ok, message). Never raise (important for BentoML)."""
    if not auth_header or not auth_header.startswith("Bearer "):
        return False, "Unauthorized"

    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        return False, "Unauthorized"

    try:
        jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return True, "OK"
    except jwt.ExpiredSignatureError:
        return False, "Token expired"
    except jwt.InvalidTokenError:
        return False, "Unauthorized"
    except Exception:
        return False, "Unauthorized"


# =========================
# BentoML Service
# =========================

@bentoml.service(name="admissions_service")
class AdmissionsService:
    def __init__(self) -> None:
        model_ref = bentoml.models.get(MODEL_TAG)
        self.model = bentoml.sklearn.load_model(model_ref.tag)

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
    def login(self, payload: Dict[str, Any], ctx) -> Dict[str, Any]:
        if isinstance(payload, dict) and "payload" in payload:
            payload = payload["payload"]

        username = payload.get("username")
        password = payload.get("password")

        if username != API_USER or password != API_PASS:
            ctx.response.status_code = 401
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
        auth_header = None
        try:
            auth_header = ctx.request.headers.get("authorization")
        except Exception:
            auth_header = None

        ok, msg = _verify_token(auth_header)
        if not ok:
            ctx.response.status_code = 401
            return {"error": msg, "status": 401}

        if isinstance(payload, dict) and "payload" in payload:
            payload = payload["payload"]

        if isinstance(payload, dict) and "instances" in payload:
            rows = payload["instances"]
            if not isinstance(rows, list) or not rows:
                ctx.response.status_code = 400
                return {"error": "instances must be a non-empty list", "status": 400}
        else:
            rows = [payload]

        try:
            df = pd.DataFrame(rows)

            missing = [c for c in self.features if c not in df.columns]
            if missing:
                ctx.response.status_code = 400
                return {"error": f"Missing columns: {missing}", "status": 400}

            df = df[self.features]

            for col in self.features:
                df[col] = pd.to_numeric(df[col], errors="raise")

        except Exception as e:
            ctx.response.status_code = 422
            return {"error": f"Invalid payload: {e}", "status": 422}

        # Prediction
        preds = self.model.predict(df)
        preds = [float(x) for x in np.asarray(preds).ravel()]
        return {"predictions": preds}
