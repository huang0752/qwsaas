from __future__ import annotations

import os
from typing import Any

import pytest

from qwsaas import QwSaasClient, S3ObjectStorage, StorageConfig

AUTHORIZED_DM_USER_ID = "7881301849355071"


def require_real_tests() -> None:
    if os.environ.get("QWSAAS_REAL_TESTS") != "1":
        pytest.skip("set QWSAAS_REAL_TESTS=1 to run real integration tests")


def require_real_send_tests() -> None:
    require_real_tests()
    if os.environ.get("QWSAAS_REAL_SEND_TESTS") != "1":
        pytest.skip("set QWSAAS_REAL_SEND_TESTS=1 to run real send tests")


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        pytest.skip(f"{name} is required")
    return value


def first_env(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return None


def target_dm_user_id() -> str:
    conversation_id = first_env("QWSAAS_TEST_DM_CONVERSATION_ID")
    if conversation_id and conversation_id.upper().startswith("S:"):
        return conversation_id.split(":", 1)[1]
    return first_env("QWSAAS_TEST_DM_USER_ID", "JUHE_TEST_USER_ID") or AUTHORIZED_DM_USER_ID


def target_dm_conversation_id() -> str:
    conversation_id = first_env("QWSAAS_TEST_DM_CONVERSATION_ID")
    if conversation_id:
        return conversation_id if conversation_id.upper().startswith("S:") else f"S:{conversation_id}"
    return f"S:{target_dm_user_id()}"


def target_room_id() -> str | None:
    room_id = first_env("QWSAAS_TEST_ROOM_ID", "JUHE_TEST_ROOM_ID")
    if room_id:
        return room_id.split(":", 1)[1] if room_id.upper().startswith("R:") else room_id
    conversation_id = first_env("QWSAAS_TEST_ROOM_CONVERSATION_ID")
    if conversation_id and conversation_id.upper().startswith("R:"):
        return conversation_id.split(":", 1)[1]
    return None


def build_real_storage() -> S3ObjectStorage:
    require_real_tests()
    if first_env("QWSAAS_STORAGE_ENDPOINT_URL"):
        return S3ObjectStorage.from_env()

    endpoint_url = required_env("JUHE_S3_ENDPOINT_URL")
    bucket = required_env("JUHE_S3_BUCKET")
    access_key = required_env("JUHE_S3_ACCESS_KEY")
    secret_key = required_env("JUHE_S3_SECRET_KEY")
    region = first_env("JUHE_S3_REGION") or "us-east-1"
    prefix = first_env("JUHE_S3_PREFIX") or "qwsaas-real-test"
    addressing_style = (
        first_env("JUHE_S3_ADDRESSING_STYLE", "JUHE_INBOUND_S3_ADDRESSING_STYLE")
        or "path"
    )
    expires = int(first_env("JUHE_S3_URL_EXPIRES_SECONDS") or "900")
    return S3ObjectStorage(
        StorageConfig(
            endpoint_url=endpoint_url,
            bucket=bucket,
            access_key=access_key,
            secret_key=secret_key,
            region=region,
            prefix=prefix,
            addressing_style=addressing_style,
            url_expires_seconds=expires,
        )
    )


def build_real_client(*, storage: S3ObjectStorage | None = None) -> QwSaasClient:
    require_real_tests()
    return QwSaasClient(
        app_key=required_env("JUHE_APP_KEY"),
        app_secret=required_env("JUHE_APP_SECRET"),
        guid=required_env("JUHE_GUID"),
        public_base_url=first_env("JUHE_BASE_URL", "QWSAAS_PUBLIC_BASE_URL"),
        private_base_url=first_env("JUHE_PRIVATE_BASE_URL", "QWSAAS_PRIVATE_BASE_URL"),
        storage=storage,
    )


def compact_response(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"type": type(value).__name__}
    data = value.get("data") if isinstance(value.get("data"), dict) else None
    return {
        "keys": sorted(str(key) for key in value.keys())[:12],
        "data_keys": sorted(str(key) for key in data.keys())[:12] if data else None,
        "error_code": value.get("error_code"),
        "base_ret": value.get("baseResponse", {}).get("ret")
        if isinstance(value.get("baseResponse"), dict)
        else None,
    }
