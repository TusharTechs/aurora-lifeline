"""Generates Pydantic v2 models from schemas/*.json into aurora_agents.contracts (make schemas)."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
OUT = ROOT / "agents" / "aurora_agents" / "contracts"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    names = sorted(p.stem for p in SCHEMAS.glob("*.json"))
    for name in names:
        title = json.loads((SCHEMAS / f"{name}.json").read_text())["title"]
        subprocess.run(
            [
                "datamodel-codegen",
                "--input",
                str(SCHEMAS / f"{name}.json"),
                "--input-file-type",
                "jsonschema",
                "--output",
                str(OUT / f"{name}.py"),
                "--output-model-type",
                "pydantic_v2.BaseModel",
                "--target-python-version",
                "3.12",
                "--class-name",
                title,
                "--use-standard-collections",
                "--use-union-operator",
                "--use-annotated",
                "--field-constraints",
                "--enum-field-as-literal",
                "all",
                "--use-double-quotes",
                "--disable-timestamp",
                "--custom-file-header",
                "# Generated from schemas/" + name + ".json by `make schemas`. Do not edit.",
            ],
            check=True,
        )
    exports = "\n".join(
        f"from .{n} import {json.loads((SCHEMAS / f'{n}.json').read_text())['title']}"
        for n in names
    )
    titles = [json.loads((SCHEMAS / f"{n}.json").read_text())["title"] for n in names]
    (OUT / "__init__.py").write_text(
        '"""Contract models generated from schemas/ (make schemas)."""\n\n'
        + exports
        + "\n\n__all__ = "
        + json.dumps(titles)
        .replace('", "', '",\n    "')
        .replace('["', '[\n    "')
        .replace('"]', '",\n]')
        + "\n"
    )
    print(f"generated {len(names)} models into {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
