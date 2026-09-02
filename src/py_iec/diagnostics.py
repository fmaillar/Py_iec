"""Diagnostics structurés pour erreurs de parsing et validation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Diagnostic:
    """Décrit un diagnostic stable associé à une source IEC.

    Args:
        code: Code machine stable du diagnostic.
        message: Message lisible par un utilisateur.
        severity: Sévérité du diagnostic.
        line: Ligne 1-indexée si connue.
        column: Colonne 1-indexée si connue.
    """

    code: str
    message: str
    severity: str = "error"
    line: int | None = None
    column: int | None = None

    def format(self) -> str:
        """Formate le diagnostic pour un affichage CLI compact.

        Returns:
            Texte contenant code, position optionnelle et message.
        """
        location = ""
        if self.line is not None and self.column is not None:
            location = f" L{self.line}:C{self.column}"
        return f"{self.severity.upper()} {self.code}{location}: {self.message}"
