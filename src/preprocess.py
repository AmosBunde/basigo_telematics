import pandas as pd
import numpy as np
from typing import Tuple
from .config import SPEED_IDLE_THRESHOLD, RESAMPLE_MIN

def _haversine(lat1, lon1, lat2, lon2):
    from math import radians, cos, sin, asin, sqrt
    R = 6371.0
    dlat = radians(lat2 - lat1); dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

def enrich(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp","telematics_id"]).sort_values(["telematics_id","timestamp"])
    df["speed_km_h"] = df["speed_km_h"].fillna(0)
    df["lat_prev"] = df.groupby("telematics_id")["latitude"].shift(1)
    df["lon_prev"] = df.groupby("telematics_id")["longitude"].shift(1)
    mask = df[["latitude","longitude","lat_prev","lon_prev"]].notna().all(axis=1)
    step_km = np.zeros(len(df))
    step_km[mask.values] = [
        _haversine(a,b,c,d) for a,b,c,d in df.loc[mask, ["lat_prev","lon_prev","latitude","longitude"]].values
    ]
    df["step_km"] = step_km
    df["is_moving"] = df["speed_km_h"] > SPEED_IDLE_THRESHOLD
    return df

def resample_minutely(df: pd.DataFrame) -> pd.DataFrame:
    feats = []
    for vid, g in df.groupby("telematics_id"):
        g = g.set_index("timestamp").sort_index()
        r = g.resample(RESAMPLE_MIN).agg({
            "speed_km_h":["mean","max"],
            "step_km":"sum",
            "state_of_charge":"mean",
            "odometer_reading_kms":"max"
        })
        r.columns = ["speed_mean","speed_max","km_travelled","soc_mean","odometer_max"]
        r["telematics_id"] = vid
        r["km_15m"] = r["km_travelled"].rolling(15, min_periods=1).sum()
        r["speed_mean_15m"] = r["speed_mean"].rolling(15, min_periods=1).mean()
        r["soc_delta_15m"] = r["soc_mean"].diff(15)
        feats.append(r.reset_index(names="timestamp"))
    out = pd.concat(feats, ignore_index=True)
    return out.sort_values(["telematics_id","timestamp"])

def make_supervised(df_min: pd.DataFrame, horizon_min:int=60):
    df = df_min.copy()
    df["soc_future"] = df.groupby("telematics_id")["soc_mean"].shift(-horizon_min)
    df["y_soc_drop_next"] = df["soc_mean"] - df["soc_future"]
    df["will_drop_10pct"] = (df["y_soc_drop_next"] >= 10.0).astype(int)
    feature_cols = ["speed_mean","speed_max","km_travelled","km_15m","speed_mean_15m","soc_mean","soc_delta_15m"]
    df = df.dropna(subset=["y_soc_drop_next"] + feature_cols)
    X = df[feature_cols].astype(float)
    y_reg = df["y_soc_drop_next"].astype(float)
    y_clf = df["will_drop_10pct"].astype(int)
    meta = df[["telematics_id","timestamp"]]
    return X, y_reg, y_clf, meta, feature_cols