import os
import boto3

def get_s3():
    endpoint = os.getenv("AWS_S3_ENDPOINT", "https://s3.amazonaws.com").strip()
    region   = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    key      = os.getenv("AWS_ACCESS_KEY_ID")
    secret   = os.getenv("AWS_SECRET_ACCESS_KEY")

    if not key or not secret:
        raise RuntimeError("S3: credenciais não configuradas (AWS_ACCESS_KEY_ID/SECRET).")

    # Valida endpoint simples (evita o erro “Invalid endpoint: https://<sua-endpoint>”)
    if endpoint.startswith("https://<") or "<sua-endpoint>" in endpoint:
        raise RuntimeError("S3: endpoint inválido. Use 'https://s3.amazonaws.com' ou o da sua região.")

    session = boto3.session.Session()
    return session.client(
        "s3",
        region_name=region,
        aws_access_key_id=key,
        aws_secret_access_key=secret,
        endpoint_url=endpoint
    )

def upload_bytes(bucket: str, key: str, data: bytes, content_type="application/octet-stream"):
    s3 = get_s3()
    s3.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)
    return f"s3://{bucket}/{key}"
