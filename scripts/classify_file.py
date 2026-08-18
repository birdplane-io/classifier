#!/usr/bin/env python3
"""Submit transcript text from a file to the classifier API."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib import error, request


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send file contents to the classifier endpoint for manual testing.",
    )
    parser.add_argument(
        "file",
        type=Path,
        help="Path to a UTF-8 text file to classify.",
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000/v1/classify",
        help="Classifier endpoint URL (default: %(default)s)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="HTTP timeout in seconds (default: %(default)s)",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print the response body without JSON pretty printing.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        text = args.file.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Error reading file '{args.file}': {exc}")
        return 1

    payload = json.dumps({"text": text}).encode("utf-8")
    req = request.Request(
        args.url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=args.timeout) as resp:
            status = resp.status
            body = resp.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code}: {body}")
        return 1
    except error.URLError as exc:
        print(f"Request failed: {exc.reason}")
        return 1

    print(f"HTTP {status}")
    if args.raw:
        print(body)
        return 0

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        print(body)
        return 0

    print(json.dumps(parsed, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())