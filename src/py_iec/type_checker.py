"""Inférence et vérification de types IEC pour le sous-ensemble supporté."""

from __future__ import annotations

from py_iec.errors import ValidationError
from py_iec.expressions import (
    BinaryOperation,
    Expression,
    Literal,
    UnaryOperation,
    VariableReference,
)
from py_iec.model import FunctionBlock
from py_iec.types import IEC_TYPES, are_types_compatible, normalize_type


def infer_expression_type(expression: Expression, block: FunctionBlock) -> str:
    """Infère le type IEC d'une expression.

    Args:
        expression: Expression à analyser.
        block: Bloc contenant les déclarations disponibles.

    Returns:
        Nom de type IEC inféré.

    Raises:
        ValidationError: Si le type ne peut pas être inféré.
    """
    variables = {
        variable.name.upper(): variable.type_name for variable in block.variables
    }
    if isinstance(expression, Literal):
        return normalize_type(expression.type_name)
    if isinstance(expression, VariableReference):
        try:
            return variables[expression.name.upper()]
        except KeyError as exc:
            raise ValidationError(f"Variable non déclarée: {expression.name}") from exc
    if isinstance(expression, UnaryOperation):
        operand_type = infer_expression_type(expression.operand, block)
        if (
            expression.operator == "NOT"
            and IEC_TYPES[operand_type].category == "boolean"
        ):
            return "BOOL"
        raise ValidationError(f"Opération unaire non typable: {expression.operator}")
    if isinstance(expression, BinaryOperation):
        return _infer_binary_type(expression, block)
    raise ValidationError(f"Expression non typable: {type(expression).__name__}")


def validate_assignment_type(
    target_type: str, expression: Expression, block: FunctionBlock
) -> None:
    """Valide la compatibilité de type d'une affectation.

    Args:
        target_type: Type IEC attendu par la cible.
        expression: Expression affectée.
        block: Bloc contenant les déclarations disponibles.

    Raises:
        ValidationError: Si les types sont incompatibles.
    """
    expression_type = infer_expression_type(expression, block)
    if not are_types_compatible(target_type, expression_type):
        raise ValidationError(
            f"Type incompatible: cible {target_type}, expression {expression_type}"
        )


def _infer_binary_type(expression: BinaryOperation, block: FunctionBlock) -> str:
    """Infère le type d'une opération binaire.

    Args:
        expression: Opération binaire.
        block: Bloc contenant les déclarations disponibles.

    Returns:
        Type IEC inféré.

    Raises:
        ValidationError: Si l'opérateur est incompatible avec les opérandes.
    """
    left_type = infer_expression_type(expression.left, block)
    right_type = infer_expression_type(expression.right, block)
    left_category = IEC_TYPES[left_type].category
    right_category = IEC_TYPES[right_type].category
    if expression.operator in {"=", "<>", "<", "<=", ">", ">="}:
        if left_category == right_category:
            return "BOOL"
    if expression.operator in {"AND", "OR", "XOR"}:
        if left_category == right_category == "boolean":
            return "BOOL"
    if expression.operator in {"+", "-", "*", "/"}:
        if left_category in {"integer", "real"} and right_category in {
            "integer",
            "real",
        }:
            return "REAL" if "real" in {left_category, right_category} else "INT"
    raise ValidationError(
        f"Opération incompatible: {left_type} {expression.operator} {right_type}"
    )
