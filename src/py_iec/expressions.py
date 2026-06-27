"""AST et parseur d'expressions Structured Text minimal."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass

from py_iec.errors import ParseError


class Expression:
    """Classe de base des expressions IEC."""


@dataclass(frozen=True)
class Literal(Expression):
    """Représente un littéral IEC.

    Args:
        value: Valeur Python du littéral.
        type_name: Type IEC inféré.
    """

    value: object
    type_name: str


@dataclass(frozen=True)
class VariableReference(Expression):
    """Représente une référence à une variable IEC.

    Args:
        name: Nom de variable référencée.
    """

    name: str


@dataclass(frozen=True)
class UnaryOperation(Expression):
    """Représente une opération unaire.

    Args:
        operator: Opérateur IEC.
        operand: Expression opérande.
    """

    operator: str
    operand: Expression


@dataclass(frozen=True)
class BinaryOperation(Expression):
    """Représente une opération binaire.

    Args:
        operator: Opérateur IEC.
        left: Expression gauche.
        right: Expression droite.
    """

    operator: str
    left: Expression
    right: Expression


@dataclass(frozen=True)
class FunctionCall(Expression):
    """Représente un appel de fonction IEC minimal.

    Args:
        name: Nom de fonction appelée.
        arguments: Arguments positionnels parsés.
    """

    name: str
    arguments: tuple[Expression, ...]


_TOKEN_RE = re.compile(
    r"\s*(?:(?P<real>\d+\.\d+)|(?P<int>\d+)|(?P<string>'[^']*')|"
    r"(?P<op><>|<=|>=|:=|[+\-*/(),=<>])|(?P<ident>[A-Za-z_][A-Za-z0-9_]*))",
    re.IGNORECASE,
)
_BINARY_PRECEDENCE = {
    "OR": 1,
    "XOR": 1,
    "AND": 2,
    "=": 3,
    "<>": 3,
    "<": 3,
    "<=": 3,
    ">": 3,
    ">=": 3,
    "+": 4,
    "-": 4,
    "*": 5,
    "/": 5,
}


@dataclass(frozen=True)
class Token:
    """Jeton lexical d'expression IEC.

    Args:
        kind: Catégorie du jeton.
        value: Valeur textuelle normalisée.
    """

    kind: str
    value: str


def parse_expression(source: str) -> Expression:
    """Parse une expression Structured Text minimale.

    Args:
        source: Expression IEC textuelle.

    Returns:
        AST d'expression typé.

    Raises:
        ParseError: Si l'expression est vide ou invalide.
    """
    tokens = _tokenize(source)
    if not tokens:
        raise ParseError("Expression vide.")
    parser = _ExpressionParser(tokens)
    expression = parser.parse_expression()
    if parser.peek() is not None:
        raise ParseError(f"Jeton inattendu dans l'expression: {parser.peek().value}")
    return expression


def expression_to_source(expression: Expression) -> str:
    """Convertit une expression AST en source Python simple.

    Args:
        expression: Expression IEC à convertir.

    Returns:
        Expression Python textuelle équivalente pour le sous-ensemble supporté.
    """
    if isinstance(expression, Literal):
        return repr(expression.value)
    if isinstance(expression, VariableReference):
        return f"self.{expression.name}"
    if isinstance(expression, UnaryOperation):
        operator = "not" if expression.operator == "NOT" else expression.operator
        return f"({operator} {expression_to_source(expression.operand)})"
    if isinstance(expression, BinaryOperation):
        operator = {"=": "==", "<>": "!=", "AND": "and", "OR": "or"}.get(
            expression.operator,
            expression.operator.lower(),
        )
        return (
            f"({expression_to_source(expression.left)} {operator} "
            f"{expression_to_source(expression.right)})"
        )
    if isinstance(expression, FunctionCall):
        args = ", ".join(expression_to_source(arg) for arg in expression.arguments)
        return f"{expression.name}({args})"
    raise TypeError(f"Expression non supportée: {type(expression).__name__}")


def iter_variable_references(expression: Expression) -> tuple[str, ...]:
    """Liste les variables référencées dans une expression.

    Args:
        expression: Expression à parcourir.

    Returns:
        Tuple des noms de variables référencées.
    """
    if isinstance(expression, VariableReference):
        return (expression.name,)
    if isinstance(expression, UnaryOperation):
        return iter_variable_references(expression.operand)
    if isinstance(expression, BinaryOperation):
        return iter_variable_references(expression.left) + iter_variable_references(
            expression.right
        )
    if isinstance(expression, FunctionCall):
        result: tuple[str, ...] = ()
        for argument in expression.arguments:
            result += iter_variable_references(argument)
        return result
    return ()


def _tokenize(source: str) -> tuple[Token, ...]:
    """Transforme une expression en jetons.

    Args:
        source: Expression brute.

    Returns:
        Tuple de jetons.

    Raises:
        ParseError: Si un caractère ne peut pas être consommé.
    """
    tokens: list[Token] = []
    position = 0
    while position < len(source):
        match = _TOKEN_RE.match(source, position)
        if match is None:
            raise ParseError(
                f"Caractère invalide dans l'expression: {source[position]}"
            )
        position = match.end()
        kind = match.lastgroup
        value = match.group(kind) if kind else ""
        if kind == "ident":
            keywords = set(_BINARY_PRECEDENCE) | {"NOT"}
            value = value.upper() if value.upper() in keywords else value
        tokens.append(Token(kind or "unknown", value))
    return tuple(tokens)


class _ExpressionParser:
    """Parseur Pratt minimal pour expressions IEC."""

    def __init__(self, tokens: tuple[Token, ...]) -> None:
        """Initialise le parseur avec une séquence de jetons.

        Args:
            tokens: Jetons issus de l'expression source.
        """
        self._tokens = tokens
        self._index = 0

    def peek(self) -> Token | None:
        """Retourne le jeton courant sans le consommer.

        Returns:
            Jeton courant ou ``None`` en fin d'expression.
        """
        if self._index >= len(self._tokens):
            return None
        return self._tokens[self._index]

    def parse_expression(self, min_precedence: int = 1) -> Expression:
        """Parse une expression en respectant la priorité des opérateurs.

        Args:
            min_precedence: Priorité minimale à consommer.

        Returns:
            Expression parsée.
        """
        left = self._parse_primary()
        while self.peek() is not None:
            operator = self.peek().value.upper()
            precedence = _BINARY_PRECEDENCE.get(operator)
            if precedence is None or precedence < min_precedence:
                break
            self._index += 1
            right = self.parse_expression(precedence + 1)
            left = BinaryOperation(operator=operator, left=left, right=right)
        return left

    def _parse_primary(self) -> Expression:
        """Parse une expression primaire.

        Returns:
            Expression primaire.

        Raises:
            ParseError: Si le jeton courant est invalide.
        """
        token = self.peek()
        if token is None:
            raise ParseError("Expression incomplète.")
        self._index += 1
        if token.kind == "int":
            return Literal(int(token.value), "INT")
        if token.kind == "real":
            return Literal(float(token.value), "REAL")
        if token.kind == "string":
            return Literal(ast.literal_eval(token.value), "STRING")
        if token.kind == "ident" and token.value.upper() in {"TRUE", "FALSE"}:
            return Literal(token.value.upper() == "TRUE", "BOOL")
        if token.kind == "ident" and token.value.upper() == "NOT":
            return UnaryOperation("NOT", self._parse_primary())
        if token.value == "(":
            expression = self.parse_expression()
            self._consume(")")
            return expression
        if token.kind == "ident":
            if self.peek() is not None and self.peek().value == "(":
                return self._parse_call(token.value)
            return VariableReference(token.value)
        raise ParseError(f"Jeton primaire invalide: {token.value}")

    def _parse_call(self, name: str) -> FunctionCall:
        """Parse un appel de fonction après lecture du nom.

        Args:
            name: Nom de fonction déjà consommé.

        Returns:
            Appel de fonction parsé.
        """
        self._consume("(")
        arguments: list[Expression] = []
        if self.peek() is not None and self.peek().value == ")":
            self._consume(")")
            return FunctionCall(name=name, arguments=())
        while True:
            arguments.append(self.parse_expression())
            if self.peek() is not None and self.peek().value == ",":
                self._consume(",")
                continue
            self._consume(")")
            return FunctionCall(name=name, arguments=tuple(arguments))

    def _consume(self, expected: str) -> None:
        """Consomme un jeton attendu.

        Args:
            expected: Valeur textuelle attendue.

        Raises:
            ParseError: Si le jeton courant ne correspond pas.
        """
        token = self.peek()
        if token is None or token.value != expected:
            raise ParseError(f"Jeton attendu: {expected}")
        self._index += 1
