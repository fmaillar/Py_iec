"""Tests du modèle intermédiaire Py_iec."""

import pytest

from py_iec.errors import ValidationError
from py_iec.model import FunctionBlock, Program, VariableDeclaration


def test_program_requires_function_block() -> None:
    """Vérifie qu'un programme vide est refusé."""
    with pytest.raises(ValidationError):
        Program(function_blocks=())


def test_variable_type_is_normalized() -> None:
    """Vérifie la normalisation des types IEC en majuscules."""
    variable = VariableDeclaration(name="speed", type_name="real")

    assert variable.type_name == "REAL"


def test_duplicate_variables_are_rejected() -> None:
    """Vérifie que deux variables du même bloc ne partagent pas un nom."""
    variable = VariableDeclaration(name="count", type_name="INT")

    with pytest.raises(ValidationError):
        FunctionBlock(name="Counter", variables=(variable, variable))


def test_variable_scope_is_normalized() -> None:
    """Vérifie la normalisation de la portée déclarative IEC."""
    variable = VariableDeclaration(name="start", type_name="BOOL", scope="var_input")

    assert variable.scope == "VAR_INPUT"


def test_invalid_variable_scope_is_rejected() -> None:
    """Vérifie qu'une portée de variable inconnue est refusée."""
    with pytest.raises(ValidationError):
        VariableDeclaration(name="start", type_name="BOOL", scope="VAR_TEMP")
