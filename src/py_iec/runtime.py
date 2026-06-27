"""Runtime d'exécution minimal du modèle intermédiaire IEC."""

from __future__ import annotations

from dataclasses import dataclass

from py_iec.expressions import (
    BinaryOperation,
    Expression,
    Literal,
    UnaryOperation,
    VariableReference,
)
from py_iec.model import FunctionBlock
from py_iec.types import default_value_for


@dataclass
class RuntimeState:
    """État mutable d'un bloc de fonctions exécuté.

    Args:
        values: Valeurs courantes indexées par nom de variable.
    """

    values: dict[str, object]


def initialize_state(block: FunctionBlock) -> RuntimeState:
    """Initialise l'état runtime d'un bloc de fonctions.

    Args:
        block: Bloc de fonctions à instancier.

    Returns:
        État initial contenant les valeurs par défaut des variables.
    """
    values = {
        variable.name: default_value_for(variable.type_name)
        for variable in block.variables
    }
    for variable in block.variables:
        if variable.initial_value is not None:
            values[variable.name] = _parse_initial_value(variable.initial_value)
    return RuntimeState(values=values)


def execute_block(
    block: FunctionBlock, state: RuntimeState | None = None
) -> RuntimeState:
    """Exécute les affectations de premier niveau d'un bloc.

    Args:
        block: Bloc à exécuter.
        state: État existant optionnel.

    Returns:
        État mis à jour.
    """
    current = state or initialize_state(block)
    for assignment in block.assignments:
        current.values[assignment.target] = evaluate_expression(
            assignment.expression, current
        )
    return current


def evaluate_expression(expression: Expression, state: RuntimeState) -> object:
    """Évalue une expression avec l'état courant.

    Args:
        expression: Expression à évaluer.
        state: État contenant les variables.

    Returns:
        Valeur évaluée.
    """
    if isinstance(expression, Literal):
        return expression.value
    if isinstance(expression, VariableReference):
        return state.values[expression.name]
    if isinstance(expression, UnaryOperation):
        value = evaluate_expression(expression.operand, state)
        return not value if expression.operator == "NOT" else value
    if isinstance(expression, BinaryOperation):
        return _evaluate_binary(expression, state)
    raise TypeError(f"Expression non exécutable: {type(expression).__name__}")


def _parse_initial_value(value: str) -> object:
    """Convertit une valeur initiale IEC simple en valeur Python.

    Args:
        value: Valeur textuelle issue de la déclaration.

    Returns:
        Valeur Python convertie si possible.
    """
    normalized = value.strip()
    if normalized.upper() == "TRUE":
        return True
    if normalized.upper() == "FALSE":
        return False
    if normalized.startswith("'") and normalized.endswith("'"):
        return normalized[1:-1]
    if "." in normalized:
        return float(normalized)
    return int(normalized)


def _evaluate_binary(expression: BinaryOperation, state: RuntimeState) -> object:
    """Évalue une opération binaire.

    Args:
        expression: Opération binaire à évaluer.
        state: État courant.

    Returns:
        Résultat Python.
    """
    left = evaluate_expression(expression.left, state)
    right = evaluate_expression(expression.right, state)
    return {
        "+": left + right,
        "-": left - right,
        "*": left * right,
        "/": left / right,
        "=": left == right,
        "<>": left != right,
        "<": left < right,
        "<=": left <= right,
        ">": left > right,
        ">=": left >= right,
        "AND": bool(left) and bool(right),
        "OR": bool(left) or bool(right),
        "XOR": bool(left) ^ bool(right),
    }[expression.operator]
