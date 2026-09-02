"""Tests runtime des structures Structured Text supportées."""

from py_iec.parser import parse_source
from py_iec.runtime import execute_block


def test_runtime_executes_if_else_branch() -> None:
    """Vérifie l'exécution d'une instruction IF/ELSE."""
    program = parse_source(
        """FUNCTION_BLOCK Logic
VAR
    enabled : BOOL := TRUE;
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

    state = execute_block(program.function_blocks[0])

    assert state.values["result"] is True


def test_runtime_executes_case_branch() -> None:
    """Vérifie l'exécution d'une instruction CASE."""
    program = parse_source(
        """FUNCTION_BLOCK Selector
VAR
    mode : INT := 1;
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

    state = execute_block(program.function_blocks[0])

    assert state.values["result"] == 10


def test_runtime_executes_while_loop() -> None:
    """Vérifie l'exécution d'une boucle WHILE."""
    program = parse_source(
        """FUNCTION_BLOCK Loop
VAR
    count : INT := 0;
END_VAR
WHILE count < 3 DO
count := count + 1;
END_WHILE
END_FUNCTION_BLOCK
"""
    )

    state = execute_block(program.function_blocks[0])

    assert state.values["count"] == 3


def test_runtime_executes_repeat_loop() -> None:
    """Vérifie l'exécution d'une boucle REPEAT."""
    program = parse_source(
        """FUNCTION_BLOCK Loop
VAR
    count : INT := 0;
END_VAR
REPEAT
count := count + 1;
UNTIL count = 2 END_REPEAT
END_FUNCTION_BLOCK
"""
    )

    state = execute_block(program.function_blocks[0])

    assert state.values["count"] == 2


def test_runtime_executes_for_loop() -> None:
    """Vérifie l'exécution d'une boucle FOR."""
    program = parse_source(
        """FUNCTION_BLOCK Loop
VAR
    index : INT;
    total : INT := 0;
END_VAR
FOR index := 1 TO 3 DO
total := total + index;
END_FOR
END_FUNCTION_BLOCK
"""
    )

    state = execute_block(program.function_blocks[0])

    assert state.values["total"] == 6
