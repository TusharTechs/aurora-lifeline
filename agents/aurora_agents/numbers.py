"""Number safety for drafting and answering agents (AI_AGENTS §2).

Gemini never writes an AURORA number. It refers to engine facts only as ``{{fact_id}}``
placeholders. ``check`` rejects any digit (ASCII or any Unicode script, such as Telugu or
Devanagari digits), any English number word, any percent sign outside a placeholder, unknown fact
IDs and missing required facts. ``render`` substitutes the engine's pre-formatted strings and
confirms that every digit in the output came from a substituted fact.
"""

import re
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

PLACEHOLDER = re.compile(r"\{\{\s*([a-z0-9_]+)\s*\}\}")
# "one" is left out: "no one", "one of the" are not quantities and would cause false rejections.
NUMBER_WORDS = re.compile(
    r"\b(?:zero|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|"
    r"fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|"
    r"eighty|ninety|hundreds?|thousands?|lakhs?|crores?|millions?|billions?|percent|per\s+cent|"
    r"dozens?|half)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    problems: list[str]
    used: set[str]


def _strip_placeholders(text: str) -> str:
    return PLACEHOLDER.sub(" ", text)


def digits_outside_placeholders(text: str) -> list[str]:
    """Characters of Unicode category Nd (decimal digits in any script) outside placeholders."""
    return [ch for ch in _strip_placeholders(text) if unicodedata.category(ch) == "Nd"]


def check(
    texts: Mapping[str, str], allowed: Iterable[str], required: Iterable[str] = ()
) -> CheckResult:
    """Checks every field in ``texts`` (field name -> text) against the facts payload."""
    allowed_set, problems, used = set(allowed), [], set()
    for field, text in texts.items():
        digits = digits_outside_placeholders(text)
        if digits:
            problems.append(f"{field}: digits outside placeholders ({''.join(digits[:10])})")
        bare = _strip_placeholders(text)
        words = NUMBER_WORDS.findall(bare)
        if words:
            problems.append(f"{field}: number words outside placeholders ({', '.join(words[:5])})")
        if "%" in bare:
            problems.append(f"{field}: percent sign outside a placeholder")
        for fid in PLACEHOLDER.findall(text):
            used.add(fid)
            if fid not in allowed_set:
                problems.append(f"{field}: unknown fact id {{{{{fid}}}}}")
        if "{{" in bare or "}}" in bare:
            problems.append(f"{field}: malformed placeholder")
    missing = sorted(set(required) - used)
    if missing:
        problems.append("missing required facts: " + ", ".join(missing))
    return CheckResult(not problems, problems, used)


def render(text: str, strings: Mapping[str, str]) -> str:
    """Substitutes placeholders with engine strings; raises if a digit has any other origin."""
    out, pos, spans = [], 0, []
    for m in PLACEHOLDER.finditer(text):
        out.append(text[pos : m.start()])
        value = strings[m.group(1)]
        start = sum(len(s) for s in out)
        out.append(value)
        spans.append((start, start + len(value)))
        pos = m.end()
    out.append(text[pos:])
    rendered = "".join(out)
    for i, ch in enumerate(rendered):
        if unicodedata.category(ch) == "Nd" and not any(a <= i < b for a, b in spans):
            raise ValueError(f"digit {ch!r} at {i} does not come from a fact")
    return rendered
