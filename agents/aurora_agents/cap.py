"""CAP 1.2 output for the SDMA's authorised originator (AI_AGENTS §5.4; CLAUDE.md non-negotiable 3).

AURORA never publishes alerts. The XML it drafts is for an SDMA originator to review and send
through Sachet. Demo messages are ``status=Exercise`` and ``scope=Restricted`` with a mandatory
``<restriction>`` (the XSD does not enforce it, so ``validate`` does).
"""

import hashlib
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any

import xmlschema

from .paths import SCHEMAS_DIR

NS = "urn:oasis:names:tc:emergency:cap:1.2"
XSD = SCHEMAS_DIR / "cap" / "CAP-v1.2.xsd"
RESTRICTION = "For SDMA/DDMA control-room officials only; not for public dissemination"
SENDER = "aurora-lifeline.web.app"
TIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$")
IST_OFFSET = timedelta(hours=5, minutes=30)


def cap_time(iso_utc: str) -> str:
    """'2025-10-26T04:00:00Z' -> '2025-10-26T09:30:00+05:30' (no Z, no fractional seconds)."""
    t = datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))
    local = (t + IST_OFFSET).replace(tzinfo=None, microsecond=0)
    return local.isoformat() + "+05:30"


def polygon_text(ring_lonlat: list[list[float]]) -> str:
    """CAP polygon: space-separated 'lat,lon' pairs, latitude first, closed, at least 4 points."""
    ring = [(round(lat, 4), round(lon, 4)) for lon, lat in ring_lonlat]
    if ring[0] != ring[-1]:
        ring.append(ring[0])
    if len(ring) < 4:
        raise ValueError("a CAP polygon needs at least 4 points")
    return " ".join(f"{lat},{lon}" for lat, lon in ring)


def _sub(parent: ET.Element, tag: str, text: str | None = None) -> ET.Element:
    el = ET.SubElement(parent, f"{{{NS}}}{tag}")
    if text is not None:
        el.text = text
    return el


def build_alert(
    *,
    scenario: dict[str, Any],
    infos: list[dict[str, Any]],
    ring_lonlat: list[list[float]] | None,
    web_url: str,
    exercise: bool = True,
) -> str:
    """CAP XML. ``infos`` hold per-language rendered text and the draft's cap block."""
    prov = scenario["provenance"]
    sent = cap_time(scenario["time_axis"]["now_utc"])
    landfall = scenario["time_axis"].get("landfall_utc")
    ident_src = f"{scenario['run_id']}|{scenario['district_lgd']}|{sent}|" + "|".join(
        i["language"] + i["headline"] for i in infos
    )
    ident = (
        f"AURORA-{scenario['run_id']}-{scenario['district_lgd']}-"
        + hashlib.sha256(ident_src.encode()).hexdigest()[:10]
    )
    ET.register_namespace("", NS)
    alert = ET.Element(f"{{{NS}}}alert")
    _sub(alert, "identifier", ident)
    _sub(alert, "sender", SENDER)
    _sub(alert, "sent", sent)
    _sub(alert, "status", "Exercise" if exercise else "Actual")
    _sub(alert, "msgType", "Alert")
    _sub(
        alert,
        "source",
        f"AURORA Lifeline, derived from IMD National Bulletin No. {prov['imd_bulletin_no']}",
    )
    _sub(alert, "scope", "Restricted")
    _sub(alert, "restriction", RESTRICTION)
    if exercise:
        _sub(
            alert,
            "note",
            f"AURORA-DEMO {scenario['storm_id']} replay ({scenario['run_id']}); "
            "decision-support draft, not an official warning",
        )
    for info in infos:
        cap = info["cap"]
        el = _sub(alert, "info")
        _sub(el, "language", info["language"])
        _sub(el, "category", cap["category"])
        _sub(el, "event", cap["event"])
        _sub(el, "responseType", "Prepare")
        _sub(el, "urgency", cap["urgency"])
        _sub(el, "severity", cap["severity"])
        _sub(el, "certainty", cap["certainty"])
        _sub(el, "audience", "SDMA/DDMA control room")
        _sub(el, "effective", sent)
        if landfall:
            _sub(
                el,
                "expires",
                cap_time(
                    (
                        datetime.fromisoformat(landfall.replace("Z", "+00:00"))
                        + timedelta(hours=24)
                    ).isoformat()
                ),
            )
        _sub(el, "senderName", "AURORA Lifeline (decision support for SDMA/DDMA)")
        _sub(el, "headline", info["headline"])
        _sub(el, "description", info["description"])
        _sub(el, "instruction", info["instruction"])
        _sub(el, "web", web_url)
        param = _sub(el, "parameter")
        _sub(param, "valueName", "IMD_BULLETIN")
        _sub(param, "value", f"National Bulletin No. {prov['imd_bulletin_no']}")
        area = _sub(el, "area")
        _sub(area, "areaDesc", info.get("area_desc") or scenario["district_name"])
        if ring_lonlat:
            _sub(area, "polygon", polygon_text(ring_lonlat))
    ET.indent(alert)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(alert, encoding="unicode") + "\n"
    )


@lru_cache(maxsize=1)
def _schema() -> xmlschema.XMLSchema:
    return xmlschema.XMLSchema(str(XSD))


def validate(xml: str) -> list[str]:
    """XSD validation plus the rules the XSD cannot express. Empty list = valid."""
    problems = [str(e.reason or e)[:200] for e in _schema().iter_errors(xml)]
    root = ET.fromstring(xml.encode())
    ns = {"c": NS}
    if root.findtext("c:scope", namespaces=ns) == "Restricted" and not root.findtext(
        "c:restriction", namespaces=ns
    ):
        problems.append("scope=Restricted without <restriction>")
    for path in ("c:sent", "c:info/c:effective", "c:info/c:onset", "c:info/c:expires"):
        for el in root.findall(path, ns):
            if el.text and not TIME_RE.match(el.text):
                problems.append(f"{path}: {el.text} is not YYYY-MM-DDThh:mm:ss±hh:mm")
    for poly in root.findall("c:info/c:area/c:polygon", ns):
        pts = [tuple(float(v) for v in p.split(",")) for p in (poly.text or "").split()]
        if len(pts) < 4 or pts[0] != pts[-1]:
            problems.append("polygon must be closed with at least 4 points")
        if any(not (-90 <= lat <= 90) for lat, _ in pts):
            problems.append("polygon latitude out of range (axis order must be lat,lon)")
    return problems
