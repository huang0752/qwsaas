from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import mimetypes
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlparse
import uuid

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError

from .exceptions import QwSaasStorageConfigError, QwSaasStorageError


@dataclass(frozen=True)
class StorageConfig:
    endpoint_url: str
    bucket: str
    access_key: str
    secret_key: str
    region: str | None = None
    prefix: str = "qwsaas-temp"
    addressing_style: str = "virtual"
    url_expires_seconds: int = 3600

    @classmethod
    def from_env(cls, prefix: str = "QWSAAS_STORAGE_") -> "StorageConfig":
        env = os.environ

        def required(name: str) -> str:
            key = f"{prefix}{name}"
            value = env.get(key, "").strip()
            if not value:
                raise QwSaasStorageConfigError(f"{key} is required")
            return value

        expires_text = env.get(f"{prefix}URL_EXPIRES_SECONDS", "").strip()
        expires = int(expires_text) if expires_text else 3600
        if expires <= 0:
            raise QwSaasStorageConfigError(f"{prefix}URL_EXPIRES_SECONDS must be > 0")

        addressing_style = env.get(f"{prefix}ADDRESSING_STYLE", "virtual").strip() or "virtual"
        if addressing_style not in {"path", "virtual", "auto"}:
            raise QwSaasStorageConfigError(f"{prefix}ADDRESSING_STYLE must be path, virtual, or auto")

        return cls(
            endpoint_url=required("ENDPOINT_URL"),
            bucket=required("BUCKET"),
            access_key=required("ACCESS_KEY"),
            secret_key=required("SECRET_KEY"),
            region=env.get(f"{prefix}REGION") or None,
            prefix=env.get(f"{prefix}PREFIX", "qwsaas-temp").strip() or "qwsaas-temp",
            addressing_style=addressing_style,
            url_expires_seconds=expires,
        )


@dataclass(frozen=True)
class StoredObject:
    bucket: str
    key: str
    url: str
    content_type: str | None = None
    size: int | None = None


class S3ObjectStorage:
    def __init__(self, config: StorageConfig) -> None:
        self.config = config
        self._cached_client: Any | None = None

    @classmethod
    def from_env(cls, prefix: str = "QWSAAS_STORAGE_") -> "S3ObjectStorage":
        return cls(StorageConfig.from_env(prefix=prefix))

    def _client(self) -> Any:
        if self._cached_client is None:
            self._cached_client = boto3.client(
                "s3",
                endpoint_url=self.config.endpoint_url,
                aws_access_key_id=self.config.access_key,
                aws_secret_access_key=self.config.secret_key,
                region_name=self.config.region,
                config=BotoConfig(
                    signature_version="s3v4",
                    s3={"addressing_style": self.config.addressing_style},
                ),
            )
        return self._cached_client

    def upload_file(self, path: str | Path, *, object_key: str | None = None) -> StoredObject:
        file_path = Path(path)
        if not file_path.is_file():
            raise QwSaasStorageConfigError(f"file does not exist: {file_path}")

        key = self._normalize_object_key(object_key, file_path.name)
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        extra_args = {"ContentType": content_type}
        try:
            self._client().upload_file(str(file_path), self.config.bucket, key, ExtraArgs=extra_args)
        except (BotoCoreError, ClientError, OSError) as exc:
            raise QwSaasStorageError(f"upload object failed: {exc}") from exc

        return StoredObject(
            bucket=self.config.bucket,
            key=key,
            url=self._object_url(self.config.bucket, key),
            content_type=content_type,
            size=file_path.stat().st_size,
        )

    def presign_get_url(
        self,
        bucket: str,
        key: str,
        *,
        expires_seconds: int | None = None,
    ) -> str:
        expires = int(expires_seconds or self.config.url_expires_seconds)
        if expires <= 0:
            raise QwSaasStorageConfigError("expires_seconds must be > 0")
        try:
            return str(
                self._client().generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket, "Key": key},
                    ExpiresIn=expires,
                )
            )
        except (BotoCoreError, ClientError) as exc:
            raise QwSaasStorageError(f"presign object failed: {exc}") from exc

    def delete_object(self, bucket: str, key: str) -> None:
        try:
            self._client().delete_object(Bucket=bucket, Key=key)
        except (BotoCoreError, ClientError) as exc:
            raise QwSaasStorageError(f"delete object failed: {exc}") from exc

    def parse_object_url(self, object_url: str) -> tuple[str, str]:
        parsed = urlparse(str(object_url or "").strip())
        if not parsed.scheme or not parsed.netloc:
            raise QwSaasStorageConfigError("object_url must be an absolute URL")

        path_parts = [unquote(part) for part in parsed.path.split("/") if part]
        endpoint_host = urlparse(self.config.endpoint_url).netloc.lower()
        host = parsed.netloc.lower()

        if host == endpoint_host and len(path_parts) >= 2:
            return path_parts[0], "/".join(path_parts[1:])

        if "." in host:
            bucket = host.split(".", 1)[0]
            if bucket and path_parts:
                return bucket, "/".join(path_parts)

        if len(path_parts) >= 2:
            return path_parts[0], "/".join(path_parts[1:])

        raise QwSaasStorageConfigError("could not parse bucket/key from object_url")

    def _normalize_object_key(self, object_key: str | None, file_name: str) -> str:
        if object_key:
            return str(object_key).strip().lstrip("/")
        safe_name = Path(file_name).name or "attachment"
        today = datetime.now(UTC).strftime("%Y/%m/%d")
        prefix = self.config.prefix.strip("/")
        return f"{prefix}/{today}/{uuid.uuid4().hex}-{safe_name}"

    def _object_url(self, bucket: str, key: str) -> str:
        endpoint = self.config.endpoint_url.rstrip("/")
        quoted_key = quote(key, safe="/")
        if self.config.addressing_style == "path":
            return f"{endpoint}/{bucket}/{quoted_key}"

        parsed = urlparse(endpoint)
        if parsed.netloc and parsed.scheme:
            return f"{parsed.scheme}://{bucket}.{parsed.netloc}/{quoted_key}"
        return f"{endpoint}/{bucket}/{quoted_key}"
