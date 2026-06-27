"""Tests des utilitaires d'extraction textuelle."""

from py_iec.extraction import extract_with_fallback


def test_extract_with_strict_pattern_first() -> None:
    """Vérifie que le motif strict est prioritaire."""
    result = extract_with_fallback(
        "DOC-IEC-001 rév A",
        strict_pattern=r"(?P<code>DOC-IEC-\d{3})\s+rév\s+[A-Z]",
        tolerant_pattern=r"(IEC-\d+)",
        fallback="UNKNOWN",
    )

    assert result == "DOC-IEC-001"


def test_extract_with_tolerant_pattern_second() -> None:
    """Vérifie que la seconde passe récupère une valeur partielle."""
    result = extract_with_fallback(
        "référence IEC-42 sans préfixe documentaire",
        strict_pattern=r"(?P<code>DOC-IEC-\d{3})",
        tolerant_pattern=r"(IEC-\d+)",
        fallback="UNKNOWN",
    )

    assert result == "IEC-42"


def test_extract_with_fallback_when_no_pattern_matches() -> None:
    """Vérifie le fallback lorsqu'aucun motif ne correspond."""
    result = extract_with_fallback(
        "aucune référence",
        strict_pattern=r"DOC-IEC-\d{3}",
        tolerant_pattern=r"IEC-\d+",
        fallback="UNKNOWN",
    )

    assert result == "UNKNOWN"
