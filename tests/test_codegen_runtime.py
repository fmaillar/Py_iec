"""Tests de génération Python et runtime minimal."""

from py_iec.codegen import generate_python_class
from py_iec.parser import parse_source
from py_iec.runtime import execute_block


def test_generate_python_class_contains_execute_assignment() -> None:
    """Vérifie que le générateur produit une méthode execute."""
    program = parse_source(
        """FUNCTION_BLOCK Counter
VAR
    count : INT := 0;
END_VAR
count := count + 1;
END_FUNCTION_BLOCK
"""
    )

    source = generate_python_class(program.function_blocks[0])

    assert "def execute" in source
    assert "self.count" in source


def test_runtime_executes_simple_assignment() -> None:
    """Vérifie l'exécution d'une affectation arithmétique simple."""
    program = parse_source(
        """FUNCTION_BLOCK Counter
VAR
    count : INT := 0;
END_VAR
count := count + 1;
END_FUNCTION_BLOCK
"""
    )

    state = execute_block(program.function_blocks[0])

    assert state.values["count"] == 1
