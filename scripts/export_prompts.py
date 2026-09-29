# ruff: noqa: E501 (prompt guidance strings)
"""Exports the agents' system instructions for the site's "Try it in Google AI Studio" section.

Usage: uv run --no-sync python scripts/export_prompts.py  (writes apps/web/src/data/prompts.json)
"""

import json
from pathlib import Path

from aurora_agents import advisory, ask, bulletin_reader

OUT = Path(__file__).resolve().parents[1] / "apps/web/src/data/prompts.json"

prompts = [
    {
        "agent": "Bulletin Reader",
        "version": bulletin_reader.PROMPT_VERSION,
        "system": bulletin_reader.SYSTEM,
        "try": "Attach any IMD national or RSMC cyclone bulletin PDF from rsmcnewdelhi.imd.gov.in and ask for the JSON reading.",
    },
    {
        "agent": "Advisory Writer",
        "version": advisory.PROMPT_VERSION,
        "system": advisory.SYSTEM,
        "try": "Paste a facts list (ids, meanings, required flags) and ask for a Telugu advisory; check that it writes only {{placeholders}}.",
    },
    {
        "agent": "Ask AURORA (ADK agent instruction)",
        "version": ask.PROMPT_VERSION,
        "system": ask.INSTRUCTION.replace("<<language_name>>", "English")
        .replace("<<run_id>>", "montha_2025_b21")
        .replace(
            "<<districts>>",
            "Kakinada, Konaseema, East Godavari, West Godavari, Eluru, Krishna district",
        ),
        "try": "In the product this runs with five read-only tools; in AI Studio, paste tool results as facts and ask a question.",
    },
]
OUT.write_text(json.dumps(prompts, indent=1, ensure_ascii=False) + "\n")
print(f"wrote {len(prompts)} prompts to {OUT}")
