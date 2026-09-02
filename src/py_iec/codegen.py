"""Génération de code Python depuis le modèle intermédiaire IEC."""

from __future__ import annotations

from py_iec.expressions import expression_to_source
from py_iec.model import (
    Assignment,
    CaseStatement,
    ForStatement,
    FunctionBlock,
    IfStatement,
    RepeatStatement,
    Statement,
    WhileStatement,
)
from py_iec.types import default_value_for


def generate_python_class(block: FunctionBlock) -> str:
    """Génère une classe Python simple pour un bloc de fonctions.

    Args:
        block: Bloc IEC à convertir.

    Returns:
        Source Python générée.
    """
    lines = [f"class {block.name}:", "    def __init__(self) -> None:"]
    if not block.variables:
        lines.append("        pass")
    for variable in block.variables:
        initial = variable.initial_value
        value = (
            repr(default_value_for(variable.type_name)) if initial is None else initial
        )
        lines.append(f"        self.{variable.name} = {value}")
    lines.append("")
    lines.append("    def execute(self) -> None:")
    if not block.statements:
        lines.append("        pass")
    for statement in block.statements:
        lines.extend(_generate_statement(statement, indent=8))
    return "\n".join(lines) + "\n"


def _generate_statement(statement: Statement, indent: int) -> list[str]:
    """Génère le code Python d'une instruction.

    Args:
        statement: Instruction IEC à convertir.
        indent: Nombre d'espaces d'indentation.

    Returns:
        Lignes Python générées.
    """
    prefix = " " * indent
    if isinstance(statement, Assignment):
        return [
            f"{prefix}self.{statement.target} = "
            f"{expression_to_source(statement.expression)}"
        ]
    if isinstance(statement, IfStatement):
        return _generate_if(statement, indent)
    if isinstance(statement, CaseStatement):
        return _generate_case(statement, indent)
    if isinstance(statement, WhileStatement):
        return _generate_while(statement, indent)
    if isinstance(statement, RepeatStatement):
        return _generate_repeat(statement, indent)
    if isinstance(statement, ForStatement):
        return _generate_for(statement, indent)
    raise TypeError(f"Instruction non générable: {type(statement).__name__}")


def _generate_if(statement: IfStatement, indent: int) -> list[str]:
    """Génère le code Python d'une instruction IF.

    Args:
        statement: Instruction IF.
        indent: Indentation de base.

    Returns:
        Lignes Python générées.
    """
    prefix = " " * indent
    lines = [f"{prefix}if {expression_to_source(statement.condition)}:"]
    lines.extend(_generate_block(statement.then_statements, indent + 4))
    if statement.else_statements:
        lines.append(f"{prefix}else:")
        lines.extend(_generate_block(statement.else_statements, indent + 4))
    return lines


def _generate_case(statement: CaseStatement, indent: int) -> list[str]:
    """Génère le code Python d'une instruction CASE.

    Args:
        statement: Instruction CASE.
        indent: Indentation de base.

    Returns:
        Lignes Python générées.
    """
    prefix = " " * indent
    selector = expression_to_source(statement.selector)
    lines: list[str] = []
    for index, branch in enumerate(statement.branches):
        keyword = "if" if index == 0 else "elif"
        values = ", ".join(repr(value) for value in branch.values)
        lines.append(f"{prefix}{keyword} str({selector}) in {{{values}}}:")
        lines.extend(_generate_block(branch.statements, indent + 4))
    if statement.else_statements:
        lines.append(f"{prefix}else:")
        lines.extend(_generate_block(statement.else_statements, indent + 4))
    if not lines:
        lines.append(f"{prefix}pass")
    return lines


def _generate_while(statement: WhileStatement, indent: int) -> list[str]:
    """Génère le code Python d'une boucle WHILE.

    Args:
        statement: Boucle WHILE.
        indent: Indentation de base.

    Returns:
        Lignes Python générées.
    """
    prefix = " " * indent
    lines = [f"{prefix}while {expression_to_source(statement.condition)}:"]
    lines.extend(_generate_block(statement.statements, indent + 4))
    return lines


def _generate_repeat(statement: RepeatStatement, indent: int) -> list[str]:
    """Génère le code Python d'une boucle REPEAT.

    Args:
        statement: Boucle REPEAT.
        indent: Indentation de base.

    Returns:
        Lignes Python générées.
    """
    prefix = " " * indent
    condition = "False"
    if statement.until is not None:
        condition = expression_to_source(statement.until)
    lines = [f"{prefix}while True:"]
    lines.extend(_generate_block(statement.statements, indent + 4))
    lines.append(f"{prefix}    if {condition}:")
    lines.append(f"{prefix}        break")
    return lines


def _generate_for(statement: ForStatement, indent: int) -> list[str]:
    """Génère le code Python d'une boucle FOR.

    Args:
        statement: Boucle FOR.
        indent: Indentation de base.

    Returns:
        Lignes Python générées.
    """
    prefix = " " * indent
    start = expression_to_source(statement.start)
    stop = expression_to_source(statement.stop)
    step = expression_to_source(statement.step) if statement.step else "1"
    lines = [
        f"{prefix}for self.{statement.variable} in "
        f"range(int({start}), int({stop}) + 1, int({step})):"
    ]
    lines.extend(_generate_block(statement.statements, indent + 4))
    return lines


def _generate_block(statements: tuple[Assignment, ...], indent: int) -> list[str]:
    """Génère un bloc Python ou ``pass`` s'il est vide.

    Args:
        statements: Affectations du bloc.
        indent: Indentation du bloc.

    Returns:
        Lignes Python générées.
    """
    if not statements:
        return [f"{' ' * indent}pass"]
    lines: list[str] = []
    for child in statements:
        lines.extend(_generate_statement(child, indent))
    return lines
