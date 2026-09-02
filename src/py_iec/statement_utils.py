"""Utilitaires de parcours des instructions IEC du modèle intermédiaire."""

from __future__ import annotations

from collections.abc import Iterable

from py_iec.model import (
    Assignment,
    CaseStatement,
    ForStatement,
    IfStatement,
    RepeatStatement,
    Statement,
    WhileStatement,
)


def iter_assignments(statements: Iterable[Statement]) -> tuple[Assignment, ...]:
    """Retourne toutes les affectations contenues dans des instructions.

    Args:
        statements: Instructions à parcourir récursivement.

    Returns:
        Tuple d'affectations trouvées, dans l'ordre de parcours.
    """
    assignments: list[Assignment] = []
    for statement in statements:
        if isinstance(statement, Assignment):
            assignments.append(statement)
        elif isinstance(statement, IfStatement):
            assignments.extend(iter_assignments(statement.then_statements))
            assignments.extend(iter_assignments(statement.else_statements))
        elif isinstance(statement, CaseStatement):
            for branch in statement.branches:
                assignments.extend(iter_assignments(branch.statements))
            assignments.extend(iter_assignments(statement.else_statements))
        elif isinstance(statement, (WhileStatement, RepeatStatement, ForStatement)):
            assignments.extend(iter_assignments(statement.statements))
    return tuple(assignments)
