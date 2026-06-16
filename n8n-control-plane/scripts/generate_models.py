#!/usr/bin/env python3
"""Generate typed Pydantic models from the n8n OpenAPI spec.

Wraps `datamodel-code-generator`. The output (src/n8n_cp/generated/models.py) is
generated code and must never be hand-edited — re-run this when the API version
changes.

Usage:
    pip install datamodel-code-generator
    python3 scripts/generate_models.py
    python3 scripts/generate_models.py --input openapi/n8n-openapi.json
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_INPUT = os.path.join(ROOT, "openapi", "n8n-openapi.json")
OUTPUT = os.path.join(ROOT, "src", "n8n_cp", "generated", "models.py")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=DEFAULT_INPUT)
    ap.add_argument("--output", default=OUTPUT)
    a = ap.parse_args()

    if not os.path.exists(a.input):
        sys.exit(f"OpenAPI spec not found: {a.input}\n"
                 f"Place your instance spec there (see openapi/README.md).")

    try:
        import datamodel_code_generator  # noqa: F401
    except ImportError:
        sys.exit("datamodel-code-generator is not installed.\n"
                 "  pip install datamodel-code-generator")

    os.makedirs(os.path.dirname(a.output), exist_ok=True)
    cmd = [
        sys.executable, "-m", "datamodel_code_generator",
        "--input", a.input,
        "--input-file-type", "openapi",
        "--output", a.output,
        "--output-model-type", "pydantic_v2.BaseModel",
        "--target-python-version", "3.10",
        "--use-schema-description",
        "--field-constraints",
        "--snake-case-field",
    ]
    print("Running:", " ".join(cmd))
    rc = subprocess.call(cmd)
    if rc == 0:
        print(f"Generated {a.output}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
