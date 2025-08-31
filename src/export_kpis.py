import json, argparse, pandas as pd, numpy as np

def haversine(lat1, lon1, lat2, lon2):
    from math import radians, cos, sin, asin, sqrt
    R = 6371.0
    dlat = radians(lat2 - lat1); dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

def main(local_path, out_json):
    df = pd.read_excel(local_path, parse_dates=["timestamp"]).sort_values(["telematics_id","timestamp"])
    df["lat_prev"] = df.groupby("telematics_id")["latitude"].shift(1)
    df["lon_prev"] = df.groupby("telematics_id")["longitude"].shift(1)
    mask = df[["latitude","longitude","lat_prev","lon_prev"]].notna().all(axis=1)
    distances = np.zeros(len(df))
    distances[mask.values] = [
        haversine(a,b,c,d) for a,b,c,d in df.loc[mask, ["lat_prev","lon_prev","latitude","longitude"]].values
    ]
    df["step_km"] = distances
    df["speed_km_h_filled"] = df["speed_km_h"].fillna(0)
    rows=[]
    for vid,g in df.groupby("telematics_id"):
        g=g.sort_values("timestamp")
        total_km=float(g["step_km"].sum())
        moving_hours=float((g["speed_km_h_filled"]>2).sum()/3600.0)
        idle_hours=float(len(g)/3600.0 - moving_hours)
        avg_mv=float(g.loc[g["speed_km_h_filled"]>2,"speed_km_h_filled"].mean() if (g["speed_km_h_filled"]>2).any() else 0.0)
        soc_start=float(g["state_of_charge"].dropna().iloc[0]) if g["state_of_charge"].notna().any() else None
        soc_end=float(g["state_of_charge"].dropna().iloc[-1]) if g["state_of_charge"].notna().any() else None
        rows.append({
            "telematics_id": str(vid),
            "total_km_haversine": round(total_km,2),
            "moving_hours": round(moving_hours,2),
            "idle_hours": round(idle_hours,2),
            "avg_speed_when_moving_km_h": round(avg_mv,2),
            "soc_start_%": round(soc_start,1) if soc_start is not None else None,
            "soc_end_%": round(soc_end,1) if soc_end is not None else None,
            "charging_sessions_est": 0
        })
    with open(out_json, "w") as f:
        json.dump(rows, f, indent=2)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--local", required=True, help="Path to telematics_data.xlsx")
    ap.add_argument("--out", default="webapp/metrics.json")
    a=ap.parse_args()
    main(a.local, a.out)