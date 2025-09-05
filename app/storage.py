import boto3
from botocore.client import Config
from .settings import settings

s3 = boto3.client(
    "s3",
    endpoint_url=settings.S3_ENDPOINT,
    region_name=settings.S3_REGION,
    aws_access_key_id=settings.S3_ACCESS_KEY_ID,
    aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
    config=Config(s3={"addressing_style": "virtual"})
)

def upload_bytes(key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    s3.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=data, ContentType=content_type)
    # URL pública depende de política; para segurança, prefira presigned:
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key},
        ExpiresIn=3600 * 24 * 7  # 7 dias
    )
    return url
