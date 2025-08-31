import os, boto3
from botocore.client import Config

S3_ENDPOINT = os.getenv("S3_ENDPOINT","http://localhost:9000")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID","minioadmin")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY","minioadmin")
BUCKET = os.getenv("S3_BUCKET","telematics")
KEY = os.getenv("S3_KEY","raw/telematics_data.xlsx")
LOCAL = os.getenv("LOCAL_FILE","./telematics_data.xlsx")

s3 = boto3.client("s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1"
)

try:
    s3.create_bucket(Bucket=BUCKET)
except Exception:
    pass

with open(LOCAL, "rb") as f:
    s3.put_object(Bucket=BUCKET, Key=KEY, Body=f,
                  ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
print(f"Uploaded {LOCAL} to {BUCKET}/{KEY} via {S3_ENDPOINT}")
