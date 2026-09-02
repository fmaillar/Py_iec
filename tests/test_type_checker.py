"""Tests de vérification de types IEC."""

import pytest

from py_iec.errors import ValidationError
from py_iec.expressions import parse_expression
from py_iec.model import Assignment, FunctionBlock, Program, VariableDeclaration
from py_iec.validator import validate_program


def test_validate_assignment_type_accepts_integer_expression() -> None:
    """Vérifie une affectation entière compatible."""
    block = FunctionBlock(
        name="Counter",
        variables=(VariableDeclaration(name="count", type_name="INT"),),
        assignments=(Assignment("count", parse_expression("1 + 2")),),
    )

    validate_program(Program((block,)))


def test_validate_assignment_type_rejects_boolean_to_integer() -> None:
    """Vérifie le rejet d'une affectation booléenne vers un entier."""
    block = FunctionBlock(
        name="Counter",
        variables=(VariableDeclaration(name="count", type_name="INT"),),
        assignments=(Assignment("count", parse_expression("TRUE")),),
    )

    with pytest.raises(ValidationError):
        validate_program(Program((block,)))
