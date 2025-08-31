CREATE TABLE IF NOT EXISTS vehicles (
  vehicle_id VARCHAR PRIMARY KEY,
  vin VARCHAR,
  battery_kwh NUMERIC,
  fleet VARCHAR,
  model VARCHAR,
  commissioned_date DATE
);

CREATE TABLE IF NOT EXISTS telematics_raw (
  vehicle_id VARCHAR,
  ts TIMESTAMP,
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  speed_km_h DOUBLE PRECISION,
  odometer_km DOUBLE PRECISION,
  soc_pct DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS vehicle_minutely (
  vehicle_id VARCHAR,
  ts TIMESTAMP,
  speed_mean DOUBLE PRECISION,
  speed_max DOUBLE PRECISION,
  km_travelled DOUBLE PRECISION,
  soc_mean DOUBLE PRECISION,
  km_15m DOUBLE PRECISION,
  speed_mean_15m DOUBLE PRECISION,
  soc_delta_15m DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS daily_kpis (
  vehicle_id VARCHAR,
  day DATE,
  total_km DOUBLE PRECISION,
  moving_hours DOUBLE PRECISION,
  idle_hours DOUBLE PRECISION,
  avg_speed_when_moving DOUBLE PRECISION,
  soc_start DOUBLE PRECISION,
  soc_end DOUBLE PRECISION,
  charges INT
);

CREATE TABLE IF NOT EXISTS predictions_minutely (
  vehicle_id VARCHAR,
  ts TIMESTAMP,
  pred_soc_drop_60min DOUBLE PRECISION,
  prob_drop_ge_10pct_60min DOUBLE PRECISION
);