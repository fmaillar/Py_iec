"""Génération de code Python depuis le modèle intermédiaire IEC."""

from __future__ import annotations

from py_iec.expressions import expression_to_source
from py_iec.model import FunctionBlock
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
    if not block.assignments:
        lines.append("        pass")
    for assignment in block.assignments:
        lines.append(
            f"        self.{assignment.target} = "
            f"{expression_to_source(assignment.expression)}"
        )
    return "\n".join(lines) + "\n"
