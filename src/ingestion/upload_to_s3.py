from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError


BUCKET_NAME = "stats-canada-grocery-data"
YEAR = 2026

FILES = {
    "average-price": Path(
        rf"D:/github/statcan-food-prices/data/loading/average-price/average-price_{YEAR}.csv"
    ),
    "cpi": Path(
        rf"D:/github/statcan-food-prices/data/loading/province-wise/provience-price_{YEAR}.csv"
    ),
}


s3_client = boto3.client("s3")


def upload_to_s3(local_file: Path, dataset_name: str, year: int):
    if not local_file.exists():
        raise FileNotFoundError(f"File not found: {local_file}")

    s3_key = f"landing/{dataset_name}/year={year}/{local_file.name}"

    try:
        s3_client.upload_file(
            Filename=str(local_file),
            Bucket=BUCKET_NAME,
            Key=s3_key
        )

        print(f"Uploaded: {local_file.name}")
        print(f"S3 location: s3://{BUCKET_NAME}/{s3_key}")

    except (ClientError, BotoCoreError) as error:
        print(f"Upload failed for {local_file.name}")
        print(error)
        raise


if __name__ == "__main__":
    for dataset_name, local_file in FILES.items():
        upload_to_s3(
            local_file=local_file,
            dataset_name=dataset_name,
            year=YEAR
        )