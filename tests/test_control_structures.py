"""Tests des structures de contrôle Structured Text minimales."""

from py_iec.model import (
    CaseStatement,
    ForStatement,
    IfStatement,
    RepeatStatement,
    WhileStatement,
)
from py_iec.parser import parse_source


def test_parse_if_statement() -> None:
    """Vérifie le parsing d'une instruction IF simple."""
    program = parse_source(
        """FUNCTION_BLOCK Logic
VAR
    enabled : BOOL;
    result : BOOL;
END_VAR
IF enabled THEN
result := TRUE;
ELSE
result := FALSE;
END_IF
END_FUNCTION_BLOCK
"""
    )

    assert isinstance(program.function_blocks[0].statements[0], IfStatement)


def test_parse_case_statement() -> None:
    """Vérifie le parsing d'une instruction CASE simple."""
    program = parse_source(
        """FUNCTION_BLOCK Selector
VAR
    mode : INT;
    result : INT;
END_VAR
CASE mode OF
1: result := 10;
ELSE
result := 0;
END_CASE
END_FUNCTION_BLOCK
"""
    )

    assert isinstance(program.function_blocks[0].statements[0], CaseStatement)


def test_parse_loop_statements_without_validation() -> None:
    """Vérifie le parsing minimal des boucles Structured Text."""
    source = """FUNCTION_BLOCK Loops
VAR
    index : INT;
END_VAR
WHILE index < 3 DO
index := index + 1;
END_WHILE
REPEAT
index := index - 1;
UNTIL index = 0 END_REPEAT
FOR index := 0 TO 2 DO
index := index + 1;
END_FOR
END_FUNCTION_BLOCK
"""

    program = parse_source(source, validate=False)
    statements = program.function_blocks[0].statements

    assert isinstance(statements[0], WhileStatement)
    assert isinstance(statements[1], RepeatStatement)
    assert isinstance(statements[2], ForStatement)
