import pandas as pd, numpy as np, json, joblib
from catboost import Pool

model = joblib.load("model.pkl")
features = json.load(open("features.json"))

X = pd.read_csv("test.csv")
X = X.reindex(columns=features)

cat_cols = [c for c in ["cat_id", "gender"] if c in X.columns]
num_cols = [c for c in X.columns if c not in cat_cols]

for c in cat_cols:
    X[c] = X[c].astype("string").fillna("na")

for c in num_cols:
    X[c] = pd.to_numeric(X[c], errors="coerce")
    med = float(X[c].median())
    X[c] = X[c].fillna(med)

pool = Pool(X, cat_features=cat_cols)
if hasattr(model, "predict_proba"):
    proba = model.predict_proba(pool)[:, 1]
else:
    proba = model.predict(pool).astype(float)

X["prediction"] = proba
X[["prediction"]].to_csv("submission.csv", index=False)
print("Предсказания сохранены в submission.csv")
