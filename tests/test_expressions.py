"""Tests du parseur d'expressions Structured Text."""

from py_iec.expressions import (
    BinaryOperation,
    Literal,
    VariableReference,
    parse_expression,
)


def test_parse_integer_literal() -> None:
    """Vérifie le parsing d'un littéral entier."""
    expression = parse_expression("42")

    assert expression == Literal(value=42, type_name="INT")


def test_parse_binary_expression_precedence() -> None:
    """Vérifie la priorité des opérateurs arithmétiques."""
    expression = parse_expression("count + 2 * step")

    assert isinstance(expression, BinaryOperation)
    assert expression.operator == "+"
    assert isinstance(expression.left, VariableReference)
