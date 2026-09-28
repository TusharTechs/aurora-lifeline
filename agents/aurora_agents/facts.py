"""Facts payload from a district scenario (ARCHITECTURE §5, AI_AGENTS §2).

Every number an advisory or an Ask AURORA answer may show is built here, by code, with its
source row and a pre-formatted string per locale. Gemini only ever sees the fact IDs and what
each one means.
"""

from datetime import UTC, datetime, timedelta, timezone
from typing import Any

IST = timezone(timedelta(hours=5, minutes=30))
LANGS = ("en-IN", "te-IN", "hi-IN")
ORD = {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth"}

MONTHS = {
    "en-IN": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "te-IN": [
        "జనవరి",
        "ఫిబ్రవరి",
        "మార్చి",
        "ఏప్రిల్",
        "మే",
        "జూన్",
        "జూలై",
        "ఆగస్టు",
        "సెప్టెంబర్",
        "అక్టోబర్",
        "నవంబర్",
        "డిసెంబర్",
    ],
    "hi-IN": [
        "जनवरी",
        "फ़रवरी",
        "मार्च",
        "अप्रैल",
        "मई",
        "जून",
        "जुलाई",
        "अगस्त",
        "सितंबर",
        "अक्टूबर",
        "नवंबर",
        "दिसंबर",
    ],
}
LAKH = {"en-IN": "lakh", "te-IN": "లక్షలు", "hi-IN": "लाख"}
RANGE = {"en-IN": "{a} to {b}", "te-IN": "{a} నుండి {b} వరకు", "hi-IN": "{a} से {b} तक"}
DISTRICTS = {
    "Kakinada": {"te-IN": "కాకినాడ", "hi-IN": "काकीनाडा"},
    "Konaseema": {"te-IN": "కోనసీమ", "hi-IN": "कोनसीमा"},
    "East Godavari": {"te-IN": "తూర్పు గోదావరి", "hi-IN": "पूर्वी गोदावरी"},
    "West Godavari": {"te-IN": "పశ్చిమ గోదావరి", "hi-IN": "पश्चिमी गोदावरी"},
    "Eluru": {"te-IN": "ఏలూరు", "hi-IN": "एलुरु"},
    "Krishna district": {"te-IN": "కృష్ణా", "hi-IN": "कृष्णा"},
}
FACILITY_TYPES = {
    "district_hospital": {"en-IN": "District Hospital", "te-IN": "జిల్లా ఆసుపత్రి", "hi-IN": "ज़िला अस्पताल"},
    "sdh_area_hospital": {"en-IN": "Area Hospital", "te-IN": "ఏరియా ఆసుపత్రి", "hi-IN": "क्षेत्रीय अस्पताल"},
    "chc": {"en-IN": "CHC", "te-IN": "సామాజిక ఆరోగ్య కేంద్రం (CHC)", "hi-IN": "सामुदायिक स्वास्थ्य केंद्र (CHC)"},
    "phc": {"en-IN": "PHC", "te-IN": "ప్రాథమిక ఆరోగ్య కేంద్రం (PHC)", "hi-IN": "प्राथमिक स्वास्थ्य केंद्र (PHC)"},
    "shelter": {"en-IN": "cyclone shelter", "te-IN": "తుఫాను షెల్టర్", "hi-IN": "चक्रवात आश्रय"},
}  # fmt: skip
CROSSING = {
    "bridge": {"en-IN": "bridge", "te-IN": "వంతెన", "hi-IN": "पुल"},
    "culvert": {"en-IN": "culvert", "te-IN": "కల్వర్టు", "hi-IN": "पुलिया"},
    "ford": {"en-IN": "causeway", "te-IN": "కాజ్‌వే", "hi-IN": "रपटा"},
    None: {"en-IN": "road", "te-IN": "రహదారి", "hi-IN": "सड़क"},
}
NEAR = {
    "en-IN": "{what} near {place}",
    "te-IN": "{place} సమీపంలోని {what}",
    "hi-IN": "{place} के पास {what}",
}
ON_ROAD = {"en-IN": " on {road}", "te-IN": " ({road})", "hi-IN": " ({road})"}
BASIS = {
    "P10 closure - 6 h": {
        "en-IN": "6 h before the earliest likely closure (P10)",
        "te-IN": "అత్యంత ముందస్తు మూసివేత అంచనా (P10) కంటే 6 గంటల ముందు",
        "hi-IN": "सबसे जल्दी संभावित बंद होने (P10) से 6 घंटे पहले",
    },
    "IMD-track closure - 6 h": {
        "en-IN": "6 h before closure on the IMD track",
        "te-IN": "IMD ట్రాక్ ప్రకారం మూసివేతకు 6 గంటల ముందు",
        "hi-IN": "IMD ट्रैक के अनुसार बंद होने से 6 घंटे पहले",
    },
}


def indian_group(n: int) -> str:
    """334619 -> '3,34,619'."""
    s = str(abs(n))
    if len(s) <= 3:
        return ("-" if n < 0 else "") + s
    head, tail = s[:-3], s[-3:]
    parts: list[str] = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ("-" if n < 0 else "") + ",".join(parts) + "," + tail


def fmt_people(n: float, lang: str) -> str:
    """People counts: lakh with one decimal from 1 lakh; hundreds or tens below."""
    n = max(float(n), 0.0)
    if n >= 1e5:
        return f"{n / 1e5:.1f} {LAKH[lang]}"
    if n >= 1000:
        return indian_group(round(n / 100) * 100)
    if n >= 10:
        return str(round(n / 10) * 10)
    return str(round(n))


def fmt_prob(p: float) -> str:
    if p < 0.005:
        return "<1%"
    if p > 0.995:
        return ">99%"
    return f"{round(p * 100)}%"


def fmt_time(iso: str, lang: str, with_year: bool = False) -> str:
    t = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(IST)
    month = MONTHS[lang][t.month - 1]
    year = f" {t.year}" if with_year else ""
    return f"{t.day} {month}{year}, {t:%H:%M} IST"


def _per_lang(fn: Any) -> dict[str, str]:
    return {lang: fn(lang) for lang in LANGS}


def _fact(
    fid: str, kind: str, value: Any, unit: str | None, text: dict[str, str], table: str, row: str,
    required: bool = False, meaning: str = "",
) -> dict[str, Any]:  # fmt: skip
    return {
        "id": fid,
        "kind": kind,
        "value": value,
        "unit": unit,
        "required": required,
        "text": text,
        "source": {"table": table, "row_id": row},
        "meaning": meaning,
    }


def site_text(site: dict[str, Any] | None, lang: str) -> str:
    if not site:
        return CROSSING[None][lang]
    what = CROSSING.get(site.get("crossing_type"), CROSSING[None])[lang]
    near = site.get("near_place")
    if near:
        key = {"te-IN": "name_te", "hi-IN": "name_hi"}.get(lang)
        place = (near.get(key) if key else None) or near["name"]
        what = NEAR[lang].format(what=what, place=place)
    if site.get("road_name"):
        what += ON_ROAD[lang].format(road=site["road_name"])
    return what


def facility_text(f: dict[str, Any], lang: str) -> str:
    label = FACILITY_TYPES.get(f["type"], {}).get(lang, f["type"])
    name = f["name"] or label
    sim = " (SIMULATED)" if f.get("is_simulated") else ""
    return f"{name}{sim}" if lang == "en-IN" else f"{name} – {label}{sim}"


def build_facts(
    scenario: dict[str, Any], audience: str = "district_officer", n_facilities: int = 5,
    n_actions: int = 3,
) -> dict[str, Any]:  # fmt: skip
    """FactsPayload (schemas/facts_payload.json) plus a ``meaning`` per fact for the prompt."""
    prov = scenario["provenance"]
    ens = prov["mode"] == "ensemble"
    facts: list[dict[str, Any]] = []
    issued = prov["imd_issued_at_utc"]
    no = prov["imd_bulletin_no"]
    facts.append(_fact(
        "provenance", "provenance", f"IMD National Bulletin {no}", None,
        {"en-IN": f"IMD National Bulletin No. {no} issued {fmt_time(issued, 'en-IN', True)}",
         "te-IN": f"IMD జాతీయ బులెటిన్ నం. {no} ({fmt_time(issued, 'te-IN', True)})",
         "hi-IN": f"IMD राष्ट्रीय बुलेटिन सं. {no} ({fmt_time(issued, 'hi-IN', True)})"},
        "district_scenario.provenance", "imd_bulletin_no", True,
        "the official IMD bulletin this forecast is derived from",
    ))  # fmt: skip
    name = scenario["district_name"]
    facts.append(_fact(
        "district", "place", name, None,
        {lang: DISTRICTS.get(name, {}).get(lang, name) for lang in LANGS},
        "district_scenario", "district_name", True, "the district this advisory covers",
    ))  # fmt: skip
    facts.append(_fact(
        "landfall_window", "text", prov["landfall_window_text"], None,
        {lang: f"“{prov['landfall_window_text']}” (IMD)" for lang in LANGS},
        "district_scenario.provenance", "landfall_window_text", False,
        "IMD's own words for the expected landfall time (a quote, attributed to IMD)",
    ))  # fmt: skip
    members = sum(v for k, v in prov["members"].items() if k != "IMD")
    if ens:
        facts.append(_fact(
            "ensemble_size", "count", members, "members",
            {"en-IN": f"{indian_group(members)} storm futures (ECMWF and Google DeepMind WeatherNext, aligned to the IMD track)",
             "te-IN": f"{indian_group(members)} తుఫాను అంచనా మార్గాలు (ECMWF, Google DeepMind WeatherNext; IMD ట్రాక్‌కు అనుగుణంగా)",
             "hi-IN": f"{indian_group(members)} तूफ़ान पूर्वानुमान मार्ग (ECMWF, Google DeepMind WeatherNext; IMD ट्रैक से संरेखित)"},
            "district_scenario.provenance", "members", False,
            "how many storm futures the probabilities come from (not official; the uncertainty envelope)",
        ))  # fmt: skip
    head = scenario["headline"]
    pc = head["pop_cut_hospital"]
    if pc["p50"] is not None:
        facts.append(_fact(
            "pop_cut_p50", "count", pc["p50"], "people", _per_lang(lambda lang: fmt_people(pc["p50"], lang)),
            "district_scenario.headline", "pop_cut_hospital.p50", True,
            "median number of people cut off by road from every public hospital by landfall",
        ))  # fmt: skip
        if ens and pc["p10"] is not None:
            facts.append(_fact(
                "pop_cut_range", "count", [pc["p10"], pc["p90"]], "people",
                _per_lang(lambda lang: RANGE[lang].format(a=fmt_people(pc["p10"], lang), b=fmt_people(pc["p90"], lang))),
                "district_scenario.headline", "pop_cut_hospital.p10_p90", True,
                "likely range (tenth to ninetieth percentile) of people cut off by landfall",
            ))  # fmt: skip
    fr = head["facilities_at_risk"]
    if fr["p50"] is not None:
        facts.append(_fact(
            "fac_risk_p50", "count", fr["p50"], "facilities", {lang: str(fr["p50"]) for lang in LANGS},
            "district_scenario.headline", "facilities_at_risk.p50", False,
            "median number of health facilities cut off from referral care by landfall",
        ))  # fmt: skip
        if ens and fr["p10"] is not None:
            facts.append(_fact(
                "fac_risk_range", "count", [fr["p10"], fr["p90"]], "facilities",
                _per_lang(lambda lang: RANGE[lang].format(a=fr["p10"], b=fr["p90"])),
                "district_scenario.headline", "facilities_at_risk.p10_p90", False,
                "likely range (tenth to ninetieth percentile) of health facilities cut off by landfall",
            ))  # fmt: skip
    ranked = sorted(
        (f for f in scenario["facilities"] if f.get("p_isolated_by_landfall") is not None),
        key=lambda f: -f["p_isolated_by_landfall"],
    )[:n_facilities]
    for k, f in enumerate(ranked, start=1):
        fid, row = f"fac{k}", f["facility_id"]
        facts.append(_fact(
            f"{fid}_name", "place", f["name"], None, _per_lang(lambda lang, f=f: facility_text(f, lang)),
            "district_scenario.facilities", row, k == 1,
            f"the {ORD[k]} health facility by chance of losing road access to referral care",
        ))  # fmt: skip
        if ens:
            facts.append(_fact(
                f"{fid}_p", "probability", round(f["p_isolated_by_landfall"], 3), None,
                {lang: fmt_prob(f["p_isolated_by_landfall"]) for lang in LANGS},
                "district_scenario.facilities", row, k == 1,
                f"chance that the {ORD[k]} facility is cut off by landfall",
            ))  # fmt: skip
        if f.get("t10") and f.get("t90"):
            facts.append(_fact(
                f"{fid}_window", "time_window", [f["t10"], f["t90"]], None,
                _per_lang(lambda lang, f=f: RANGE[lang].format(a=fmt_time(f["t10"], lang), b=fmt_time(f["t90"], lang))),
                "district_scenario.facilities", row, k == 1,
                f"likely time window (tenth to ninetieth percentile) in which the {ORD[k]} facility loses road access",
            ))  # fmt: skip
    for k, a in enumerate(scenario["actions"][:n_actions], start=1):
        aid, row = f"act{k}", a["action_id"]
        facts.append(_fact(
            f"{aid}_site", "place", a["target_id"], None, _per_lang(lambda lang, a=a: site_text(a.get("site"), lang)),
            "district_scenario.actions", row, k == 1,
            f"where the {ORD[k]} action (pre-position road-clearing machinery) should happen",
        ))  # fmt: skip
        basis = BASIS.get(a["deadline_basis"], {lang: a["deadline_basis"] for lang in LANGS})
        facts.append(_fact(
            f"{aid}_deadline", "time", a["deadline_utc"], None,
            _per_lang(lambda lang, a=a, basis=basis: f"{fmt_time(a['deadline_utc'], lang)} ({basis[lang]})"),
            "district_scenario.actions", row, k == 1,
            f"deadline for the {ORD[k]} action, with its basis",
        ))  # fmt: skip
        facts.append(_fact(
            f"{aid}_people", "count", a["people_protected"], "people",
            _per_lang(lambda lang, a=a: fmt_people(a["people_protected"], lang)),
            "district_scenario.actions", row, False,
            f"expected people whose road access the {ORD[k]} action protects",
        ))  # fmt: skip
        if ens and a.get("p_event") is not None:
            facts.append(_fact(
                f"{aid}_p", "probability", a["p_event"], None, {lang: fmt_prob(a["p_event"]) for lang in LANGS},
                "district_scenario.actions", row, False, f"chance that the crossing for the {ORD[k]} action closes",
            ))  # fmt: skip
    return {
        "run_id": scenario["run_id"],
        "district_lgd": scenario["district_lgd"],
        "audience": audience,
        "langs": list(LANGS),
        "facts": facts,
    }


def schema_view(payload: dict[str, Any]) -> dict[str, Any]:
    """The payload without the ``meaning`` helper field (validates against facts_payload.json)."""
    return {
        **payload,
        "facts": [{k: v for k, v in f.items() if k != "meaning"} for f in payload["facts"]],
    }


def now_ist() -> str:
    """CAP-style IST timestamp without fractional seconds (YYYY-MM-DDThh:mm:ss+05:30)."""
    return datetime.now(UTC).astimezone(IST).replace(microsecond=0).isoformat()
