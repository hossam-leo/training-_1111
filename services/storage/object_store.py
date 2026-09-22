import os
import time
from dataclasses import dataclass


@dataclass
class ObjectRef:
    bucket: str
    key: str
    etag: str | None = None


class MinioObjectStore:
    def __init__(
        self,
        endpoint=None,
        access_key=None,
        secret_key=None,
        bucket=None,
        secure=False
    ):
        try:
            import boto3
            from botocore.client import Config
        except ImportError as exc:
            raise RuntimeError(
                "Install boto3 to enable MinIO/S3 storage"
            ) from exc

        self.bucket = bucket or os.getenv(
            "MINIO_BUCKET",
            "proctorstream-private"
        )

        endpoint = endpoint or os.getenv(
            "MINIO_ENDPOINT",
            "localhost:9000"
        )

        endpoint = (
            "http://" if not endpoint.startswith("http") else ""
        ) + endpoint

        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key or os.getenv(
                "MINIO_ACCESS_KEY",
                "minioadmin"
            ),
            aws_secret_access_key=secret_key or os.getenv(
                "MINIO_SECRET_KEY",
                "minioadmin"
            ),
            config=Config(signature_version="s3v4"),
            use_ssl=secure
        )

    def ensure_bucket(self):
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except Exception:
            self.client.create_bucket(Bucket=self.bucket)

    def put(
        self,
        key,
        content,
        content_type="application/octet-stream",
        metadata=None,
        retries=3
    ):
        self.ensure_bucket()

        for attempt in range(retries):
            try:
                put_kwargs = {
                    "Bucket": self.bucket,
                    "Key": key,
                    "Body": content,
                    "ContentType": content_type,
                    "Metadata": metadata or {},
                }

                # Enable server-side encryption only when explicitly configured.
                # This avoids requiring KMS in the GitHub Actions MinIO container.
                if os.getenv(
                    "PROCTORSTREAM_S3_SSE",
                    ""
                ).lower() == "aes256":
                    put_kwargs["ServerSideEncryption"] = "AES256"

                response = self.client.put_object(**put_kwargs)

                return ObjectRef(
                    bucket=self.bucket,
                    key=key,
                    etag=response.get("ETag")
                )

            except Exception:
                if attempt == retries - 1:
                    raise

                time.sleep(2 ** attempt)

    def get(self, key):
        return self.client.get_object(
            Bucket=self.bucket,
            Key=key
        )["Body"].read()

    def delete(self, key):
        return self.client.delete_object(
            Bucket=self.bucket,
            Key=key
        )

    def signed_url(self, key, expires=300):
        return self.client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": key
            },
            ExpiresIn=expires
        )
