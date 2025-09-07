import os
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

# Leemos la configuración de MinIO desde las variables de entorno
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")

# Creamos el cliente de S3, configurado para apuntar a nuestro MinIO
s3_client = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    config=Config(signature_version="s3v4")
)

def create_bucket_if_not_exists(bucket_name: str):
    """Crea un bucket en MinIO si no existe ya."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' ya existe.")
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            s3_client.create_bucket(Bucket=bucket_name)
            print(f"Bucket '{bucket_name}' creado exitosamente.")
        else:
            raise

def upload_file(bucket_name: str, file_path: str, object_name: str):
    """Sube un archivo a un bucket de MinIO."""
    try:
        s3_client.upload_file(file_path, bucket_name, object_name)
        print(f"Archivo '{file_path}' subido a '{bucket_name}/{object_name}'.")
    except ClientError as e:
        print(f"Error al subir archivo a MinIO: {e}")
        raise

def download_file(bucket_name: str, object_name: str, file_path: str):
    """Descarga un archivo desde un bucket de MinIO."""
    try:
        s3_client.download_file(bucket_name, object_name, file_path)
        print(f"Archivo '{bucket_name}/{object_name}' descargado a '{file_path}'.")
    except ClientError as e:
        print(f"Error al descargar archivo desde MinIO: {e}")
        raise