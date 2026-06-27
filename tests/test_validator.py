"""Tests de validation sémantique du modèle IEC."""

import pytest

from py_iec.errors import ValidationError
from py_iec.model import Assignment, FunctionBlock, Program, VariableDeclaration
from py_iec.parser import parse_source
from py_iec.validator import validate_program


def test_validate_program_accepts_declared_assignment_target() -> None:
    """Vérifie qu'une affectation vers une variable déclarée est acceptée."""
    block = FunctionBlock(
        name="Counter",
        variables=(VariableDeclaration(name="count", type_name="INT"),),
        assignments=(Assignment(target="count", expression="count + 1"),),
    )
    program = Program(function_blocks=(block,))

    validate_program(program)


def test_validate_program_rejects_undeclared_assignment_target() -> None:
    """Vérifie qu'une affectation vers une variable non déclarée est rejetée."""
    block = FunctionBlock(
        name="Counter",
        variables=(VariableDeclaration(name="count", type_name="INT"),),
        assignments=(Assignment(target="missing", expression="1"),),
    )
    program = Program(function_blocks=(block,))

    with pytest.raises(ValidationError):
        validate_program(program)


def test_parse_source_runs_semantic_validation_by_default() -> None:
    """Vérifie que le parseur active la validation sémantique par défaut."""
    source = """FUNCTION_BLOCK Counter
VAR
    count : INT;
END_VAR
missing := 1;
END_FUNCTION_BLOCK
"""

    with pytest.raises(ValidationError):
        parse_source(source)


def test_parse_source_can_skip_semantic_validation() -> None:
    """Vérifie qu'un appelant peut désactiver la validation si nécessaire."""
    source = """FUNCTION_BLOCK Counter
VAR
    count : INT;
END_VAR
missing := 1;
END_FUNCTION_BLOCK
"""

    program = parse_source(source, validate=False)

    assert program.function_blocks[0].assignments[0].target == "missing"
