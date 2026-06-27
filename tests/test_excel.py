"""Tests des helpers Excel sans fichier lourd versionné."""

from pathlib import Path

import pytest

from py_iec.excel import find_column_name, read_prefixed_excel_sheets


def test_find_column_name_uses_strict_regex_first() -> None:
    """Vérifie la recherche stricte d'un nom de colonne dynamique."""
    columns = ["Identifiant document", "Revision", "Statut"]

    result = find_column_name(
        columns,
        strict_regex=r"^Identifiant document$",
        tolerant_regex=r"document",
    )

    assert result == "Identifiant document"


def test_find_column_name_uses_tolerant_regex_second() -> None:
    """Vérifie la recherche tolérante si le motif strict échoue."""
    columns = ["ID doc", "Revision", "Statut"]

    result = find_column_name(
        columns,
        strict_regex=r"^Identifiant document$",
        tolerant_regex=r"doc",
    )

    assert result == "ID doc"


def test_read_prefixed_excel_sheets_rejects_missing_file() -> None:
    """Vérifie la validation explicite de l'existence du classeur."""
    with pytest.raises(FileNotFoundError):
        read_prefixed_excel_sheets(Path("tests/fixtures/missing.xlsx"))
