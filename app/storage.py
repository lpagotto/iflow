# app/storage.py
import boto3
from .settings import settings

def _s3():
    kwargs = {}
    if settings.AWS_S3_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.AWS_S3_ENDPOINT_URL
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        **kwargs
    )

def upload_bytes(key: str, data: bytes, content_type="application/octet-stream"):
    s3 = _s3()
    s3.put_object(Bucket=settings.AWS_S3_BUCKET, Key=key, Body=data, ContentType=content_type)
    return key

def presigned_url(key: str, expires=3600):
    s3 = _s3()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.AWS_S3_BUCKET, "Key": key},
        ExpiresIn=expires,
    )
