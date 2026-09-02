from __future__ import annotations

import json
import math
import re
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlparse

_SENSITIVE_KEY = re.compile(
    r"(?:aes[_-]?key|auth[_-]?key|auth[_-]?cookies?|authorization|cookie|secret|signature|token)",
    re.IGNORECASE,
)
_IDENTITY_KEY = re.compile(
    r"(?:sender|receiver|roomid|room_id|user_id|wxid|sender_name|sendername|nickname|real_name|inviteId)$",
    re.IGNORECASE,
)
_REAL_ID = re.compile(r"(?:168|788|10)\d{8,}")
_PLACEHOLDER = re.compile(
    r"(?:REDACTED|(?:ACCOUNT|CONTACT|ROOM|USER|APPINFO|GUID|ASID)_[A-Z0-9_]+|0)"
)
_APPROVED_HOSTS = {
    "example.invalid",
    "imunion.weixin.qq.com",
    "wework.apifox.cn",
    "wework.qpic.cn",
    "wwcdn.weixin.qq.com",
}
_APPROVED_HOST_SUFFIXES = (".qpic.cn",)


@dataclass(frozen=True)
class FixtureSafetyFinding:
    file: str
    json_path: str
    reason: str


def scan_fixture_paths(paths: Iterable[Path | str]) -> list[FixtureSafetyFinding]:
    findings: list[FixtureSafetyFinding] = []
    for path_value in paths:
        path = Path(path_value)
        files = sorted(path.rglob("*.json")) if path.is_dir() else [path]
        for file_path in files:
            try:
                payload = json.loads(file_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                findings.append(FixtureSafetyFinding(str(file_path), "$", "invalid_json"))
                continue
            _scan_value(
                payload,
                file_path=file_path,
                json_path="$",
                key=None,
                is_public="apifox" in file_path.parts,
                findings=findings,
            )
    return findings


def _scan_value(
    value: Any,
    *,
    file_path: Path,
    json_path: str,
    key: str | None,
    is_public: bool,
    findings: list[FixtureSafetyFinding],
) -> None:
    if isinstance(value, Mapping):
        for child_key, child in value.items():
            name = str(child_key)
            _scan_value(
                child,
                file_path=file_path,
                json_path=f"{json_path}.{name}",
                key=name,
                is_public=is_public,
                findings=findings,
            )
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _scan_value(
                child,
                file_path=file_path,
                json_path=f"{json_path}[{index}]",
                key=key,
                is_public=is_public,
                findings=findings,
            )
        return
    if not isinstance(value, str):
        return

    def add(reason: str) -> None:
        findings.append(FixtureSafetyFinding(str(file_path), json_path, reason))

    if key and _SENSITIVE_KEY.search(key) and value != "REDACTED":
        add("sensitive_value")
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        hostname = (parsed.hostname or "").lower()
        if hostname not in _APPROVED_HOSTS and not hostname.endswith(_APPROVED_HOST_SUFFIXES):
            add("unapproved_host")
        if any(query_value != "REDACTED" for _, query_value in parse_qsl(parsed.query, keep_blank_values=True)):
            add("url_query_value")
        return
    if not is_public and key and _IDENTITY_KEY.search(key) and not _PLACEHOLDER.fullmatch(value):
        add("identity_not_placeholder")
    if not is_public and _REAL_ID.search(value):
        add("real_id_pattern")
    if (
        not is_public
        and len(value) >= 24
        and not _PLACEHOLDER.fullmatch(value)
        and _entropy(value) >= 4.0
    ):
        add("high_entropy_string")


def _entropy(value: str) -> float:
    counts = Counter(value)
    length = len(value)
    return -sum((count / length) * math.log2(count / length) for count in counts.values())
