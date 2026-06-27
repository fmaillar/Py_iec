"""Validation sémantique du modèle intermédiaire IEC."""

from __future__ import annotations

from py_iec.errors import ValidationError
from py_iec.model import FunctionBlock, Program


def validate_program(program: Program) -> None:
    """Valide les règles sémantiques transverses d'un programme IEC.

    Args:
        program: Programme intermédiaire à contrôler.

    Returns:
        Aucune valeur. La fonction se termine silencieusement si le programme est
        valide.

    Raises:
        ValidationError: Si une règle sémantique du sous-ensemble supporté échoue.
    """
    for block in program.function_blocks:
        validate_function_block(block)


def validate_function_block(block: FunctionBlock) -> None:
    """Valide les règles sémantiques d'un bloc de fonctions IEC.

    Args:
        block: Bloc de fonctions à contrôler.

    Returns:
        Aucune valeur. La fonction se termine silencieusement si le bloc est valide.

    Raises:
        ValidationError: Si une affectation cible une variable non déclarée.
    """
    declared_names = {variable.name.upper() for variable in block.variables}
    for assignment in block.assignments:
        if assignment.target.upper() not in declared_names:
            raise ValidationError(
                f"Variable affectée non déclarée dans {block.name}: "
                f"{assignment.target}"
            )
