# 📊 BasiGo PAYD – Telematics Analytics & ML Platform

This repository implements a **complete workflow** for analyzing, modeling, and presenting electric bus telematics data in support of **Pay-As-You-Drive (PAYD)**. It goes from **raw data ingestion** all the way to **machine learning predictions**, **dashboards**, and **production deployment**.

---

## 🚍 Business Context

BasiGo’s **PAYD model** allows bus operators to avoid the high upfront costs of EV buses by paying based on kilometers driven. To make PAYD reliable and scalable, operators need:

- **Transparent KPIs**: distance, utilization, charging sessions, SOC (State of Charge).  
- **Predictive insights**: Will the battery drop too low in the next 60 minutes? Should this bus divert to charge?  
- **Automated pipelines**: ingest raw telematics, generate dashboards, and deliver ML-driven alerts in real time.  

This repo demonstrates exactly that.

---

## 🔄 Workflow Overview

1. **Raw Data Ingestion**  
   - Input: `telematics_data.xlsx` (real telematics dump).  
   - Stored in **S3** (or MinIO locally).  
   - Schema: `timestamp`, `telematics_id`, `latitude`, `longitude`, `speed_km_h`, `odometer_reading_kms`, `state_of_charge`.

2. **Data Transformation**  
   - Clean timestamps, fill missing speed values with 0.  
   - Compute **distance travelled** (Haversine formula on GPS points).  
   - Flag **moving vs idle** states (speed > 2 km/h).  
   - Resample to **1-minute aggregates**:  
     - mean/max speed, km travelled, rolling distance (15m), SOC deltas.  
   - Export **Daily KPIs**: distance, utilization hours, SOC start/end, charging events.  

3. **Modeling**  
   - **Regression**: Forecast SOC drop over the next 60 minutes.  
   - **Classification**: Probability SOC will drop ≥10% in the next 60 minutes.  
   - Algorithms: **HistGradientBoosting** (like XGBoost but native in sklearn) + **Bagging**.  
   - Artifacts saved in `src/models/`.  

4. **Presentation**  
   - **Backend API**: FastAPI `/predict` endpoint serving ML outputs.  
   - **WebApp (Dashboard)**: D3.js UI showing KPIs and daily distances by vehicle.  
   - **Warehouse DDL**: SQL schemas to store raw, minutely aggregates, KPIs, and predictions.  

---

## 📐 Why the Warehouse Schema?

The warehouse DDL (`schemas/warehouse_schemas.sql`) was designed for **business-facing analytics**:

- **vehicles** → Master data (VIN, battery capacity, fleet).  
- **telematics_raw** → Truth store for ingestion.  
- **vehicle_minutely** → Pre-aggregated metrics for speed.  
- **daily_kpis** → KPIs per bus per day (distance, utilization, SOC ranges).  
- **predictions_minutely** → ML outputs (risk forecasts, SOC drops).  

This schema supports both **dashboards** (KPIs) and **predictive alerts** (ML).

---

## ☁️ Scaling on AWS

While MinIO simulates S3 locally, the architecture is AWS-native:

- **Ingestion** → IoT Core / Kinesis → **S3** (`s3://telematics/raw/…`).  
- **Transformation** → AWS Glue or Spark → store as Parquet.  
- **Training** → Nightly retrains, save models to `s3://models/`.  
- **Serving** → FastAPI container on ECS/EKS pulling models from S3.  
- **Dashboard** → Static webapp hosted on **S3 + CloudFront** or served via backend.  

---

## 🖼️ Architecture Diagrams

### 1. End-to-End AWS Architecture
```flowchart TD

  %% Devices
  subgraph Devices
    A[EV Bus Telematics Units]
  end

  %% Ingestion
  subgraph Ingestion
    B[AWS IoT Core / MQTT]
    C[Kinesis Firehose]
  end

  %% Storage
  subgraph Storage
    D[S3 Data Lake (Raw)]
  end

  %% Processing
  subgraph Processing
    E[AWS Glue / Spark ETL]
    F[Vehicle Minutely Table]
    G[Daily KPIs Table]
  end

  %% ML
  subgraph ML
    H[Training Jobs (SageMaker / ECS)]
    I[S3 Model Registry]
  end

  %% Serving
  subgraph Serving
    J[FastAPI Prediction API (ECS/EKS)]
    K[Customer Alerts / PAYD Integration]
  end

  %% Presentation
  subgraph Presentation
    L[Dashboard (S3 + CloudFront / React/D3.js)]
  end

  %% Connections (no chained arrows; one edge per line)
  A --> B
  B --> C
  C --> D

  D --> E
  E --> F
  E --> G

  F --> H
  G --> H
  H --> I

  I --> J
  J --> K

  G --> L
  J --> L
```

---

## 🐳 Deployment (Docker)

### 1. Backend API
```bash
docker build -f docker/Dockerfile -t basigo-api .
docker run -p 8000:8000 basigo-api
```

Test:
```bash
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json"   -d '{"speed_mean":20,"speed_max":40,"km_travelled":0.5,"km_15m":7,"speed_mean_15m":22,"soc_mean":54,"soc_delta_15m":-2}'
```

### 2. WebApp (Dashboard)
```bash
python -m http.server 8080 -d webapp
# open http://localhost:8080
```

Containerized option:
```dockerfile
FROM nginx:alpine
COPY webapp/ /usr/share/nginx/html/
```
```bash
docker build -t basigo-dashboard .
docker run -p 8080:80 basigo-dashboard
```

### 3. Full Stack with MinIO
```bash
docker compose up --build
```

Runs:
- **MinIO** (ports 9000/9001) – S3 simulation.  
- **FastAPI** backend (port 8000).  

---

## 📊 Model Presentation to Stakeholders

- **Daily KPIs**: “Yesterday, Bus 61EFCD47 drove 212 km, with 6.6 moving hours. SOC dropped from 31% to 26%.”  
- **Predictive Alerts**: “78% chance this bus will lose more than 10% SOC in the next 60 minutes.”  
- **Dashboard**: One-page fleet summary.  
- **API**: Integrates directly with PAYD billing and driver/operator apps.  

---

## 🚀 Reproduce Locally

```bash
# Setup environment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Train models
python -m src.train --local telematics_data.xlsx

# Generate KPIs for dashboard
python src/export_kpis.py --local telematics_data.xlsx --out webapp/metrics.json

# Serve API
uvicorn src.serve_api:app --reload

# Serve dashboard
python -m http.server 8080 -d webapp
```

---

## 🛤️ Next Steps

- **Enhance Models** → Range prediction, anomaly detection, charger ETA.  
- **Automate Retraining** → Airflow / MWAA DAG.  
- **Observability** → Monitor model drift and accuracy.  
- **Scaling** → Rollout across 1000+ buses via AWS ECS/EKS.  

---

## 📌 Key Takeaways for Stakeholders

- **Transparency**: KPIs give operators confidence in PAYD.  
- **Predictive Power**: Models reduce risk of service interruptions.  
- **Scalability**: AWS-native design works for 5 or 5,000 buses.  
- **Flexibility**: Lightweight dashboard + API-first backend ensures fast rollout.  

---
