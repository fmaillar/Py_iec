"""Lecture robuste de classeurs Excel pour données de certification IEC."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

DEFAULT_ALLOWED_SHEETS = ("Liste_documentaire", "Liste_Documentaire")


def read_prefixed_excel_sheets(
    workbook_path: Path,
    allowed_sheets: tuple[str, ...] = DEFAULT_ALLOWED_SHEETS,
) -> dict[str, Any]:
    """Lit les feuilles Excel dont le nom correspond exactement à la liste admise.

    Args:
        workbook_path: Chemin vers un fichier `.xlsx` ou `.xlsm` existant.
        allowed_sheets: Noms de feuilles acceptés par correspondance exacte.

    Returns:
        Dictionnaire associant chaque nom de feuille retenu à son DataFrame pandas.

    Raises:
        FileNotFoundError: Si le fichier n'existe pas.
        ValueError: Si le chemin n'est pas un fichier Excel valide ou si aucune
            feuille attendue n'est trouvée.
    """
    _validate_workbook_path(workbook_path)

    import pandas as pd

    workbook = pd.ExcelFile(workbook_path, engine="openpyxl")
    selected_sheets = [name for name in workbook.sheet_names if name in allowed_sheets]
    if not selected_sheets:
        raise ValueError(
            "Aucune feuille attendue trouvée. Feuilles acceptées: "
            f"{', '.join(allowed_sheets)}"
        )
    return {
        sheet_name: pd.read_excel(workbook, sheet_name=sheet_name, engine="openpyxl")
        for sheet_name in selected_sheets
    }


def find_column_name(columns: list[str], strict_regex: str, tolerant_regex: str) -> str:
    """Recherche un nom de colonne avec une passe stricte puis tolérante.

    Args:
        columns: Noms de colonnes disponibles dans la feuille.
        strict_regex: Motif regex complet utilisé en première passe.
        tolerant_regex: Motif regex partiel utilisé en seconde passe.

    Returns:
        Nom de colonne correspondant.

    Raises:
        ValueError: Si aucune colonne ne correspond aux motifs fournis.
    """
    for pattern in (strict_regex, tolerant_regex):
        compiled = re.compile(pattern, re.IGNORECASE)
        for column in columns:
            if compiled.fullmatch(column.strip()) or compiled.search(column.strip()):
                return column
    raise ValueError("Aucune colonne ne correspond aux motifs fournis.")


def _validate_workbook_path(workbook_path: Path) -> None:
    """Valide l'existence et l'extension d'un classeur Excel.

    Args:
        workbook_path: Chemin à valider.

    Raises:
        FileNotFoundError: Si le chemin n'existe pas ou n'est pas un fichier.
        ValueError: Si l'extension n'est pas supportée.
    """
    if not workbook_path.is_file():
        raise FileNotFoundError(f"Classeur Excel introuvable: {workbook_path}")
    if workbook_path.suffix.lower() not in {".xlsx", ".xlsm"}:
        raise ValueError("Le classeur doit être au format .xlsx ou .xlsm.")
