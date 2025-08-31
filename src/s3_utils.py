import io
import pandas as pd
from .config import S3_ENDPOINT, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION

def s3_client():
    import boto3  # import when needed to avoid hard dependency in non-S3 paths
    session = boto3.session.Session()
    return session.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )

def read_excel_from_s3(bucket: str, key: str) -> pd.DataFrame:
    s3 = s3_client()
    obj = s3.get_object(Bucket=bucket, Key=key)
    data = obj["Body"].read()
    return pd.read_excel(io.BytesIO(data))

def write_parquet_to_s3(df: pd.DataFrame, bucket: str, key: str):
    import pyarrow as pa, pyarrow.parquet as pq
    buf = io.BytesIO()
    table = pa.Table.from_pandas(df)
    pq.write_table(table, buf)
    buf.seek(0)
    s3 = s3_client()
    s3.put_object(Bucket=bucket, Key=key, Body=buf.getvalue(), ContentType="application/octet-stream")