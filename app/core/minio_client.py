from minio import Minio
from app.core.config import get_settings

settings = get_settings()

# Initialize the stateless MinIO client instance using global configurations
minio_client = Minio(
    endpoint=settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=settings.minio_secure,
)


def init_minio_storage() -> None:
    """
    Idempotent lifecycle hook to guarantee the existence of target 
    storage layers (Bronze Bucket) before the server begins processing payloads.
    """
    bucket_name = settings.minio_bucket_name
    try:
        # Check if the baseline ingestion bucket already exists
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            print(f"[MinIO] Successfully initialized storage bucket: '{bucket_name}'")
        else:
            print(f"[MinIO] Storage bucket '{bucket_name}' verified. Skipping initialization.")
    except Exception as e:
        print(f"[MinIO Crisis] Failed to programmatically verify/create storage assets: {str(e)}")
        raise e