from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split

RAW_PATH = Path("data/raw/admission.csv")
OUT_DIR = Path("data/processed")

TARGET = "Chance of Admit"

def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(RAW_PATH)

    # Nettoyage noms de colonnes (le CSV a un espace en fin de "Chance of Admit ")
    df.columns = [c.strip() for c in df.columns]

    # Colonne inutile pour la modélisation
    if "Serial No." in df.columns:
        df = df.drop(columns=["Serial No."])

    # Sécurité
    if TARGET not in df.columns:
        raise ValueError(f"Target '{TARGET}' not found. Columns={df.columns.tolist()}")

    # Nettoyage basique
    df = df.dropna().reset_index(drop=True)

    X = df.drop(columns=[TARGET])
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    X_train.to_csv(OUT_DIR / "X_train.csv", index=False)
    X_test.to_csv(OUT_DIR / "X_test.csv", index=False)
    y_train.to_csv(OUT_DIR / "y_train.csv", index=False)
    y_test.to_csv(OUT_DIR / "y_test.csv", index=False)

    print("Saved files to data/processed:")
    for p in sorted(OUT_DIR.glob("*.csv")):
        print(" -", p.name, p.stat().st_size, "bytes")

if __name__ == "__main__":
    main()
