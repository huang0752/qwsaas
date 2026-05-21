from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from qwsaas.exceptions import QwSaasStorageConfigError
from qwsaas.storage import S3ObjectStorage, StorageConfig


def test_storage_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QWSAAS_STORAGE_ENDPOINT_URL", "http://127.0.0.1:9000")
    monkeypatch.setenv("QWSAAS_STORAGE_BUCKET", "wework")
    monkeypatch.setenv("QWSAAS_STORAGE_ACCESS_KEY", "ak")
    monkeypatch.setenv("QWSAAS_STORAGE_SECRET_KEY", "sk")
    monkeypatch.setenv("QWSAAS_STORAGE_REGION", "us-east-1")
    monkeypatch.setenv("QWSAAS_STORAGE_PREFIX", "qwsaas-temp")
    monkeypatch.setenv("QWSAAS_STORAGE_ADDRESSING_STYLE", "path")
    monkeypatch.setenv("QWSAAS_STORAGE_URL_EXPIRES_SECONDS", "900")

    config = StorageConfig.from_env()

    assert config.endpoint_url == "http://127.0.0.1:9000"
    assert config.bucket == "wework"
    assert config.addressing_style == "path"
    assert config.url_expires_seconds == 900


def test_storage_config_requires_core_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QWSAAS_STORAGE_ENDPOINT_URL", "http://127.0.0.1:9000")

    with pytest.raises(QwSaasStorageConfigError, match="QWSAAS_STORAGE_BUCKET"):
        StorageConfig.from_env()


class FakeS3Client:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def upload_file(self, filename: str, bucket: str, key: str, ExtraArgs: dict[str, Any]) -> None:
        self.calls.append(
            (
                "upload_file",
                {
                    "filename": filename,
                    "bucket": bucket,
                    "key": key,
                    "ExtraArgs": ExtraArgs,
                },
            )
        )

    def generate_presigned_url(
        self,
        client_method: str,
        Params: dict[str, Any],
        ExpiresIn: int,
    ) -> str:
        self.calls.append(
            (
                "generate_presigned_url",
                {"client_method": client_method, "Params": Params, "ExpiresIn": ExpiresIn},
            )
        )
        return f"https://signed.example/{Params['Bucket']}/{Params['Key']}?e={ExpiresIn}"

    def delete_object(self, Bucket: str, Key: str) -> None:
        self.calls.append(("delete_object", {"Bucket": Bucket, "Key": Key}))


def test_storage_upload_presign_and_delete(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_client = FakeS3Client()
    monkeypatch.setattr("qwsaas.storage.boto3.client", lambda *args, **kwargs: fake_client)
    path = tmp_path / "report.txt"
    path.write_text("hello", encoding="utf-8")
    storage = S3ObjectStorage(
        StorageConfig(
            endpoint_url="http://127.0.0.1:9000",
            bucket="wework",
            access_key="ak",
            secret_key="sk",
            region="us-east-1",
            prefix="tests",
            addressing_style="path",
            url_expires_seconds=900,
        )
    )

    stored = storage.upload_file(path, object_key="tests/report.txt")
    signed = storage.presign_get_url(stored.bucket, stored.key)
    storage.delete_object(stored.bucket, stored.key)

    assert stored.bucket == "wework"
    assert stored.key == "tests/report.txt"
    assert stored.content_type == "text/plain"
    assert stored.size == 5
    assert stored.url == "http://127.0.0.1:9000/wework/tests/report.txt"
    assert signed == "https://signed.example/wework/tests/report.txt?e=900"
    assert fake_client.calls[0] == (
        "upload_file",
        {
            "filename": str(path),
            "bucket": "wework",
            "key": "tests/report.txt",
            "ExtraArgs": {"ContentType": "text/plain"},
        },
    )
    assert fake_client.calls[-1] == ("delete_object", {"Bucket": "wework", "Key": "tests/report.txt"})


def test_storage_parse_path_and_virtual_hosted_urls() -> None:
    storage = S3ObjectStorage(
        StorageConfig(
            endpoint_url="http://127.0.0.1:9000",
            bucket="wework",
            access_key="ak",
            secret_key="sk",
            addressing_style="path",
        )
    )

    assert storage.parse_object_url("http://127.0.0.1:9000/wework/a/b.txt") == ("wework", "a/b.txt")
    assert storage.parse_object_url("https://wework.s3.example.com/a/b.txt") == ("wework", "a/b.txt")
