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

MAX_LOOP_ITERATIONS = 10000


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
    """Exécute les instructions d'un bloc.

    Args:
        block: Bloc à exécuter.
        state: État existant optionnel.

    Returns:
        État mis à jour.
    """
    current = state or initialize_state(block)
    _execute_statements(block.statements, current)
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


def _execute_statements(statements: tuple[Statement, ...], state: RuntimeState) -> None:
    """Exécute une séquence d'instructions.

    Args:
        statements: Instructions à exécuter.
        state: État mutable.
    """
    for statement in statements:
        _execute_statement(statement, state)


def _execute_statement(statement: Statement, state: RuntimeState) -> None:
    """Exécute une instruction individuelle.

    Args:
        statement: Instruction à exécuter.
        state: État mutable.

    Raises:
        RuntimeError: Si une boucle dépasse la limite de sûreté.
    """
    if isinstance(statement, Assignment):
        state.values[statement.target] = evaluate_expression(
            statement.expression, state
        )
        return
    if isinstance(statement, IfStatement):
        branch = statement.then_statements
        if not bool(evaluate_expression(statement.condition, state)):
            branch = statement.else_statements
        _execute_statements(branch, state)
        return
    if isinstance(statement, CaseStatement):
        _execute_case(statement, state)
        return
    if isinstance(statement, WhileStatement):
        _execute_while(statement, state)
        return
    if isinstance(statement, RepeatStatement):
        _execute_repeat(statement, state)
        return
    if isinstance(statement, ForStatement):
        _execute_for(statement, state)


def _execute_case(statement: CaseStatement, state: RuntimeState) -> None:
    """Exécute une instruction CASE.

    Args:
        statement: Instruction CASE.
        state: État mutable.
    """
    selector = evaluate_expression(statement.selector, state)
    for branch in statement.branches:
        if str(selector) in branch.values:
            _execute_statements(branch.statements, state)
            return
    _execute_statements(statement.else_statements, state)


def _execute_while(statement: WhileStatement, state: RuntimeState) -> None:
    """Exécute une boucle WHILE avec limite de sûreté.

    Args:
        statement: Boucle WHILE.
        state: État mutable.

    Raises:
        RuntimeError: Si la boucle dépasse la limite de sûreté.
    """
    iterations = 0
    while bool(evaluate_expression(statement.condition, state)):
        if iterations >= MAX_LOOP_ITERATIONS:
            raise RuntimeError("Limite d'itérations WHILE dépassée.")
        _execute_statements(statement.statements, state)
        iterations += 1


def _execute_repeat(statement: RepeatStatement, state: RuntimeState) -> None:
    """Exécute une boucle REPEAT avec limite de sûreté.

    Args:
        statement: Boucle REPEAT.
        state: État mutable.

    Raises:
        RuntimeError: Si la boucle dépasse la limite de sûreté.
    """
    iterations = 0
    while True:
        if iterations >= MAX_LOOP_ITERATIONS:
            raise RuntimeError("Limite d'itérations REPEAT dépassée.")
        _execute_statements(statement.statements, state)
        iterations += 1
        if statement.until is not None and bool(
            evaluate_expression(statement.until, state)
        ):
            return


def _execute_for(statement: ForStatement, state: RuntimeState) -> None:
    """Exécute une boucle FOR avec bornes entières.

    Args:
        statement: Boucle FOR.
        state: État mutable.
    """
    start = int(evaluate_expression(statement.start, state))
    stop = int(evaluate_expression(statement.stop, state))
    step = int(evaluate_expression(statement.step, state)) if statement.step else 1
    if step == 0:
        raise RuntimeError("Le pas d'une boucle FOR ne peut pas être nul.")
    current = start
    while (step > 0 and current <= stop) or (step < 0 and current >= stop):
        state.values[statement.variable] = current
        _execute_statements(statement.statements, state)
        current += step


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
