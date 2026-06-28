import os
from rapidfuzz import fuzz
from typing import Optional, Tuple
from database import get_known_properties, save_known_property


def normalize(val: Optional[str]) -> str:
    if not val:
        return ""
    # Strip common German city suffixes so "Bernau bei Berlin" matches "Bernau"
    val = val.lower().strip()
    for suffix in [" bei berlin", " bei hamburg", " am rhein", " an der "]:
        val = val.split(suffix)[0]
    return val


def check_for_duplicate(
    incoming_street: Optional[str],
    incoming_city: str,
    threshold: float = 80,
) -> Tuple[bool, Optional[str]]:
    """
    Checks whether an incoming property address matches a known property.

    Edge case: if street is None (e.g. offer only names a city/district),
    we cannot do a reliable address match and log a warning rather than
    silently returning False. In production this would trigger a manual review flag.
    """
    if not incoming_street:
        # Known limitation: properties without a street address bypass duplicate
        # detection. This is flagged here so it's visible in logs.
        print(f"[matcher] WARNING: No street provided for city '{incoming_city}' — duplicate check skipped.")
        return False, None

    street_in = normalize(incoming_street)
    city_in = normalize(incoming_city)

    for record in get_known_properties():
        city_score = fuzz.ratio(city_in, normalize(record["city"]))
        if city_score >= 75:  # fuzzy city match first to narrow candidates
            street_score = fuzz.ratio(street_in, normalize(record["street"]))
            if street_score >= threshold:
                return True, record["street"]

    return False, None


def generate_rejection_email(broker_name: str, property_title: str, matched_address: str) -> str:
    return f"""Sehr geehrte(r) {broker_name or 'Damen und Herren'},

vielen Dank für die Zusendung Ihres Immobilienangebots „{property_title}".

Nach interner Überprüfung unserer Bestände müssen wir Ihnen mitteilen, dass uns das angebotene Objekt (Adressabgleich: {matched_address}) bereits bekannt ist.

Wir können dieses Angebot daher leider nicht als Erstangebot werten. Ein Provisionsanspruch besteht für dieses Objekt unsererseits nicht.

Wir bitten um Ihr Verständnis und verbleiben mit freundlichen Grüßen,
Investa Real Estate GmbH
"""