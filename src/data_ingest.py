import pandas as pd
from .config import S3_BUCKET, S3_KEY
from .s3_utils import read_excel_from_s3

def load_raw(from_s3: bool = True, local_path: str | None = None) -> pd.DataFrame:
    if from_s3:
        return read_excel_from_s3(S3_BUCKET, S3_KEY)
    if not local_path:
        raise ValueError("Provide local_path when from_s3=False")
    return pd.read_excel(local_path, parse_dates=["timestamp"])
