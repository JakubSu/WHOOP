from __future__ import annotations


PAIN_OR_INJURY_TERMS = {
    "ache",
    "aches",
    "aching",
    "hurt",
    "hurts",
    "injured",
    "injury",
    "pain",
    "painful",
    "sharp pain",
    "sore",
    "strain",
}


def detect_safety_flags(message: str) -> list[str]:
    normalized = message.lower()
    if any(term in normalized for term in PAIN_OR_INJURY_TERMS):
        return ["pain_or_injury_mentioned"]
    return []
