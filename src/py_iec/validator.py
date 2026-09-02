"""Validation sémantique du modèle intermédiaire IEC."""

from __future__ import annotations

from py_iec.errors import ValidationError
from py_iec.expressions import iter_variable_references
from py_iec.model import (
    Assignment,
    CaseStatement,
    ForStatement,
    FunctionBlock,
    IfStatement,
    Program,
    RepeatStatement,
    Statement,
    VariableDeclaration,
    WhileStatement,
)
from py_iec.type_checker import infer_expression_type, validate_assignment_type


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
    statements = block.statements or block.assignments
    for statement in statements:
        _validate_statement(block, statement, declared_names)


def _validate_statement(
    block: FunctionBlock,
    statement: Statement,
    declared_names: dict[str, VariableDeclaration],
) -> None:
    """Valide récursivement une instruction.

    Args:
        block: Bloc contenant l'instruction.
        statement: Instruction à contrôler.
        declared_names: Variables déclarées indexées en majuscules.

    Raises:
        ValidationError: Si l'instruction viole les règles supportées.
    """
    if isinstance(statement, Assignment):
        _validate_assignment(block, statement, declared_names)
        return
    if isinstance(statement, IfStatement):
        _validate_boolean_expression(statement.condition, block)
        for child in statement.then_statements + statement.else_statements:
            _validate_statement(block, child, declared_names)
        return
    if isinstance(statement, CaseStatement):
        _validate_expression_references(statement.selector, declared_names)
        for branch in statement.branches:
            for child in branch.statements:
                _validate_statement(block, child, declared_names)
        for child in statement.else_statements:
            _validate_statement(block, child, declared_names)
        return
    if isinstance(statement, WhileStatement):
        _validate_boolean_expression(statement.condition, block)
        for child in statement.statements:
            _validate_statement(block, child, declared_names)
        return
    if isinstance(statement, RepeatStatement):
        if statement.until is None:
            raise ValidationError("Condition UNTIL absente.")
        _validate_boolean_expression(statement.until, block)
        for child in statement.statements:
            _validate_statement(block, child, declared_names)
        return
    if isinstance(statement, ForStatement):
        if statement.variable.upper() not in declared_names:
            raise ValidationError(f"Compteur FOR non déclaré: {statement.variable}")
        _validate_expression_references(statement.start, declared_names)
        _validate_expression_references(statement.stop, declared_names)
        if statement.step is not None:
            _validate_expression_references(statement.step, declared_names)
        for child in statement.statements:
            _validate_statement(block, child, declared_names)


def _validate_assignment(
    block: FunctionBlock,
    assignment: Assignment,
    declared_names: dict[str, VariableDeclaration],
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
    _validate_expression_references(assignment.expression, declared_names)
    validate_assignment_type(target.type_name, assignment.expression, block)


def _validate_expression_references(
    expression: object, declared_names: dict[str, VariableDeclaration]
) -> None:
    """Valide les références de variables d'une expression.

    Args:
        expression: Expression IEC à parcourir.
        declared_names: Variables déclarées indexées en majuscules.

    Raises:
        ValidationError: Si une référence est inconnue.
    """
    for reference in iter_variable_references(expression):
        if reference.upper() not in declared_names:
            raise ValidationError(f"Variable référencée non déclarée: {reference}")


def _validate_boolean_expression(expression: object, block: FunctionBlock) -> None:
    """Valide qu'une expression est booléenne.

    Args:
        expression: Expression à contrôler.
        block: Bloc contenant les déclarations.

    Raises:
        ValidationError: Si l'expression n'est pas typée BOOL.
    """
    if infer_expression_type(expression, block) != "BOOL":
        raise ValidationError("Une condition doit être de type BOOL.")
