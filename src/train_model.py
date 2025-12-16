from pathlib import Path
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

import bentoml
from bentoml.sklearn import save_model

PROCESSED_DIR = Path("data/processed")

def main() -> None:
    X_train = pd.read_csv(PROCESSED_DIR / "X_train.csv")
    X_test = pd.read_csv(PROCESSED_DIR / "X_test.csv")

    y_train = pd.read_csv(PROCESSED_DIR / "y_train.csv").squeeze("columns")
    y_test = pd.read_csv(PROCESSED_DIR / "y_test.csv").squeeze("columns")

    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("model", LinearRegression()),
        ]
    )

    pipeline.fit(X_train, y_train)
    preds = pipeline.predict(X_test)

    r2 = r2_score(y_test, preds)
    mae = mean_absolute_error(y_test, preds)
    mse = mean_squared_error(y_test, preds)
    rmse = mse ** 0.5

    print(f"R2   : {r2:.4f}")
    print(f"MAE  : {mae:.4f}")
    print(f"RMSE : {rmse:.4f}")

    # Save in BentoML model store
    bento_model = save_model(
        name="admissions_lr",
        model=pipeline,
        signatures={"predict": {"batchable": True}},
        metadata={
            "features": list(X_train.columns),
            "metrics": {"r2": float(r2), "mae": float(mae), "rmse": float(rmse)},
        },
    )

    print("Saved BentoML model:", bento_model.tag)

if __name__ == "__main__":
    main()
