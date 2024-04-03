import argparse
import time
from io import BytesIO

import pandas as pd
from minio import Minio


def run_simple_workload(
    run_time: int,
    minio_host: str,
    minio_access_key: str,
    minio_secret_key: str,
    source_bucket: str,
    target_bucket: str,
    dataset_name: str,
) -> None:
    print("Connecting...")

    client = Minio(
        minio_host,
        access_key=minio_access_key,
        secret_key=minio_secret_key,
        secure=False,
    )

    print("Connected")
    print("Running")

    timeout = time.time() + run_time
    ascending = True

    while True:
        print(".", end="", flush=True)

        if time.time() > timeout:
            break

        # Read the dataset from the source bucket
        try:
            response = client.get_object(source_bucket, dataset_name)
            buffer = BytesIO(response.read())
            df = pd.read_csv(buffer, header=None)
        finally:
            response.close()
            response.release_conn()

        # Sort the dataset
        df_sorted = df.sort_values(by=df.columns[0], ascending=ascending)
        output_data = BytesIO()
        df_sorted.to_csv(output_data, index=False)
        ascending = not ascending

        # Write the dataset to the target bucket
        output_data.seek(0)
        client.put_object(
            target_bucket,
            dataset_name,
            output_data,
            length=output_data.getbuffer().nbytes,
        )

    print("\nSuccessfully completed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple workload.")

    parser.add_argument("time", type=int, help="Duration of work, sec.")
    parser.add_argument("minio_host", type=str, help="Minio host address")
    parser.add_argument("minio_access_key", type=str, help="Minio access key")
    parser.add_argument("minio_secret_key", type=str, help="Minio secret key")
    parser.add_argument("source_bucket", type=str, help="Name of a source bucket")
    parser.add_argument("target_bucket", type=str, help="Name of a target bucket")
    parser.add_argument("dataset_name", type=str, help="Name of a dataset file")

    args = parser.parse_args()

    run_simple_workload(
        args.time,
        args.minio_host,
        args.minio_access_key,
        args.minio_secret_key,
        args.source_bucket,
        args.target_bucket,
        args.dataset_name,
    )
