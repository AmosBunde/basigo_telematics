import os, json, numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier, BaggingRegressor, BaggingClassifier
from sklearn.metrics import mean_absolute_error, r2_score, roc_auc_score, average_precision_score
import joblib

from .preprocess import enrich, resample_minutely, make_supervised
from .config import HORIZON_MIN
from .data_ingest import load_raw

def train_models(from_s3:bool=True, local_path:str|None=None, out_dir:str="src/models"):
    raw = load_raw(from_s3=from_s3, local_path=local_path)
    raw = enrich(raw)
    df_min = resample_minutely(raw)
    X, y_reg, y_clf, meta, feature_cols = make_supervised(df_min, horizon_min=HORIZON_MIN)

    n = len(X); cut = int(0.7*n)
    Xtr, Xte = X.iloc[:cut], X.iloc[cut:]
    ytr_r, yte_r = y_reg.iloc[:cut], y_reg.iloc[cut:]
    ytr_c, yte_c = y_clf.iloc[:cut], y_clf.iloc[cut:]

    # Regression
    hgb_reg = HistGradientBoostingRegressor(max_depth=6, learning_rate=0.1, max_iter=200)
    bag_reg = BaggingRegressor(n_estimators=50, random_state=42)
    hgb_reg.fit(Xtr, ytr_r); bag_reg.fit(Xtr, ytr_r)

    # Classification
    hgb_clf = HistGradientBoostingClassifier(max_depth=6, learning_rate=0.1, max_iter=200)
    bag_clf = BaggingClassifier(n_estimators=50, random_state=42)
    hgb_clf.fit(Xtr, ytr_c); bag_clf.fit(Xtr, ytr_c)

    evals = {
        "regression": {
            "HistGB": {"MAE": float(mean_absolute_error(yte_r, hgb_reg.predict(Xte))),
                       "R2": float(r2_score(yte_r, hgb_reg.predict(Xte)))},
            "Bagging": {"MAE": float(mean_absolute_error(yte_r, bag_reg.predict(Xte))),
                        "R2": float(r2_score(yte_r, bag_reg.predict(Xte)))},
        },
        "classification": {
            "HistGB": {"ROC_AUC": float(roc_auc_score(yte_c, hgb_clf.predict_proba(Xte)[:,1])),
                       "PR_AUC": float(average_precision_score(yte_c, hgb_clf.predict_proba(Xte)[:,1]))},
            "Bagging": {"ROC_AUC": float(roc_auc_score(yte_c, bag_clf.predict_proba(Xte)[:,1])),
                        "PR_AUC": float(average_precision_score(yte_c, bag_clf.predict_proba(Xte)[:,1]))},
        },
        "feature_cols": feature_cols
    }

    os.makedirs(out_dir, exist_ok=True)
    joblib.dump(hgb_reg, os.path.join(out_dir, "soc_drop_regressor_histgb.joblib"))
    joblib.dump(bag_reg, os.path.join(out_dir, "soc_drop_regressor_bagging.joblib"))
    joblib.dump(hgb_clf, os.path.join(out_dir, "soc_drop_classifier_histgb.joblib"))
    joblib.dump(bag_clf, os.path.join(out_dir, "soc_drop_classifier_bagging.joblib"))
    with open(os.path.join(out_dir, "eval_metrics.json"), "w") as f:
        json.dump(evals, f, indent=2)
    return evals

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--from_s3", action="store_true")
    p.add_argument("--local", default="data/telematics_data.xlsx")
    p.add_argument("--out_dir", default="src/models")
    args = p.parse_args()
    m = train_models(from_s3=args.from_s3, local_path=args.local, out_dir=args.out_dir)
    print(json.dumps(m, indent=2))
