"""Utilitaires d'extraction de chaînes avec passe stricte puis tolérante."""

from __future__ import annotations

import re


def extract_with_fallback(
    value: str,
    strict_pattern: str | re.Pattern[str],
    tolerant_pattern: str | re.Pattern[str],
    fallback: str = "",
) -> str:
    """Extrait une valeur textuelle avec deux niveaux de tolérance.

    Args:
        value: Texte source à analyser.
        strict_pattern: Motif complet appliqué en première passe.
        tolerant_pattern: Motif partiel appliqué si la première passe échoue.
        fallback: Valeur retournée si aucun motif ne correspond.

    Returns:
        Première capture nommée ou positionnelle trouvée, sinon la correspondance
        complète, ou le fallback fourni.
    """
    for pattern in (strict_pattern, tolerant_pattern):
        match = re.search(pattern, value)
        if match is None:
            continue
        if match.groupdict():
            return next(iter(match.groupdict().values()))
        if match.groups():
            return match.group(1)
        return match.group(0)
    return fallback
