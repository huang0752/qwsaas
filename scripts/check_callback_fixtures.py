from __future__ import annotations

import sys
from pathlib import Path

from qwsaas.callback_fixture_safety import scan_fixture_paths


def main(argv: list[str] | None = None) -> int:
    values = argv if argv is not None else sys.argv[1:]
    paths = [Path(value) for value in values] or [Path("tests/fixtures")]
    findings = scan_fixture_paths(paths)
    for finding in findings:
        print(f"{finding.file}:{finding.json_path}: {finding.reason}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
