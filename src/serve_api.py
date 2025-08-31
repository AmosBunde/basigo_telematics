from fastapi import FastAPI
from pydantic import BaseModel
import joblib, os, pandas as pd

app = FastAPI(title="BasiGo Telematics ML API")

MODEL_DIR = os.getenv("MODEL_DIR","src/models")
REG_PATH = os.path.join(MODEL_DIR, "soc_drop_regressor_histgb.joblib")
CLF_PATH = os.path.join(MODEL_DIR, "soc_drop_classifier_histgb.joblib")

reg = joblib.load(REG_PATH) if os.path.exists(REG_PATH) else None
clf = joblib.load(CLF_PATH) if os.path.exists(CLF_PATH) else None
FEATURE_COLS = ["speed_mean","speed_max","km_travelled","km_15m","speed_mean_15m","soc_mean","soc_delta_15m"]

class MinuteFeature(BaseModel):
    speed_mean: float
    speed_max: float
    km_travelled: float
    km_15m: float
    speed_mean_15m: float
    soc_mean: float
    soc_delta_15m: float

@app.post("/predict")
def predict(feat: MinuteFeature):
    X = pd.DataFrame([feat.model_dump()])[FEATURE_COLS]
    y_drop = float(reg.predict(X)[0]) if reg else None
    p_high_drop = float(clf.predict_proba(X)[0,1]) if clf else None
    return {"pred_soc_drop_next_60min_pct": y_drop, "prob_drop_ge_10pct_60min": p_high_drop}
