"""Validation sémantique du modèle intermédiaire IEC."""

from __future__ import annotations

from py_iec.errors import ValidationError
from py_iec.expressions import iter_variable_references
from py_iec.model import Assignment, FunctionBlock, Program
from py_iec.type_checker import validate_assignment_type


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
        ValidationError: Si une affectation cible une variable non déclarée ou si
            une expression référence une variable inconnue.
    """
    declared_names = {variable.name.upper(): variable for variable in block.variables}
    for assignment in block.assignments:
        _validate_assignment(block, assignment, declared_names)


def _validate_assignment(
    block: FunctionBlock,
    assignment: Assignment,
    declared_names: dict[str, object],
) -> None:
    """Valide une affectation individuelle.

    Args:
        block: Bloc contenant l'affectation.
        assignment: Affectation à contrôler.
        declared_names: Variables déclarées indexées en majuscules.

    Raises:
        ValidationError: Si la cible ou une référence est invalide.
    """
    target = declared_names.get(assignment.target.upper())
    if target is None:
        raise ValidationError(
            f"Variable affectée non déclarée dans {block.name}: {assignment.target}"
        )
    if target.scope == "VAR_INPUT":
        raise ValidationError(f"Écriture interdite sur VAR_INPUT: {assignment.target}")
    for reference in iter_variable_references(assignment.expression):
        if reference.upper() not in declared_names:
            raise ValidationError(f"Variable référencée non déclarée: {reference}")
    validate_assignment_type(target.type_name, assignment.expression, block)
