import os

S3_BUCKET = os.getenv("S3_BUCKET", "telematics")
S3_KEY = os.getenv("S3_KEY", "raw/telematics_data.xlsx")
S3_ENDPOINT = os.getenv("S3_ENDPOINT")  # e.g. "http://minio:9000"
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
AWS_REGION = os.getenv("AWS_REGION","us-east-1")

# Domain assumptions
BATTERY_KWH = float(os.getenv("BATTERY_KWH", "250"))
SPEED_IDLE_THRESHOLD = float(os.getenv("SPEED_IDLE_THRESHOLD", "2.0"))

# Modeling
RESAMPLE_MIN = os.getenv("RESAMPLE_MIN", "1min")
HORIZON_MIN = int(os.getenv("HORIZON_MIN", "60"))
