"""Location of the shared JSON Schemas and CAP XSD (repo schemas/, or AURORA_SCHEMAS_DIR)."""

import os
from pathlib import Path

SCHEMAS_DIR = Path(
    os.environ.get("AURORA_SCHEMAS_DIR") or Path(__file__).resolve().parents[2] / "schemas"
)
