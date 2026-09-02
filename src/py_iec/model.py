"""Modèle intermédiaire typé pour un sous-ensemble IEC 61131-3."""

from __future__ import annotations

from dataclasses import dataclass, field

from py_iec.errors import ValidationError
from py_iec.expressions import Expression
from py_iec.types import IEC_TYPES, normalize_type

SUPPORTED_TYPES = set(IEC_TYPES)
SUPPORTED_VARIABLE_SCOPES = {"VAR", "VAR_INPUT", "VAR_OUTPUT"}


@dataclass(frozen=True)
class VariableDeclaration:
    """Décrit une variable déclarée dans un bloc de fonctions IEC.

    Args:
        name: Nom symbolique de la variable.
        type_name: Type IEC de la variable.
        initial_value: Valeur initiale optionnelle sous forme textuelle.
        scope: Section IEC dans laquelle la variable est déclarée.
    """

    name: str
    type_name: str
    initial_value: str | None = None
    scope: str = "VAR"

    def __post_init__(self) -> None:
        """Valide le nom et le type de la variable après instanciation.

        Raises:
            ValidationError: Si le nom est vide ou si le type n'est pas supporté.
        """
        if not self.name.strip():
            raise ValidationError("Le nom de variable ne peut pas être vide.")
        normalized_type = normalize_type(self.type_name)
        normalized_scope = self.scope.upper()
        if normalized_scope not in SUPPORTED_VARIABLE_SCOPES:
            raise ValidationError(f"Portée IEC non supportée: {self.scope}")
        object.__setattr__(self, "type_name", normalized_type)
        object.__setattr__(self, "scope", normalized_scope)


@dataclass(frozen=True)
class Assignment:
    """Représente une affectation Structured Text simple.

    Args:
        target: Variable cible à gauche de l'opérateur ``:=``.
        expression: Expression AST à droite de l'opérateur.
    """

    target: str
    expression: Expression

    def __post_init__(self) -> None:
        """Valide la présence d'une cible et d'une expression.

        Raises:
            ValidationError: Si la cible ou l'expression est vide.
        """
        if not self.target.strip():
            raise ValidationError("La cible d'affectation ne peut pas être vide.")
        if self.expression is None:
            raise ValidationError("L'expression d'affectation ne peut pas être vide.")


@dataclass(frozen=True)
class IfStatement:
    """Représente une structure IF Structured Text.

    Args:
        condition: Expression conditionnelle.
        then_statements: Instructions exécutées si la condition est vraie.
        else_statements: Instructions exécutées sinon.
    """

    condition: Expression
    then_statements: tuple[Assignment, ...] = field(default_factory=tuple)
    else_statements: tuple[Assignment, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CaseBranch:
    """Représente une branche CASE.

    Args:
        values: Valeurs textuelles de sélection.
        statements: Instructions associées à la branche.
    """

    values: tuple[str, ...]
    statements: tuple[Assignment, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CaseStatement:
    """Représente une structure CASE Structured Text.

    Args:
        selector: Expression de sélection.
        branches: Branches explicites.
        else_statements: Instructions par défaut.
    """

    selector: Expression
    branches: tuple[CaseBranch, ...] = field(default_factory=tuple)
    else_statements: tuple[Assignment, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class WhileStatement:
    """Représente une boucle WHILE minimale.

    Args:
        condition: Condition de boucle.
        statements: Corps de boucle.
    """

    condition: Expression
    statements: tuple[Assignment, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RepeatStatement:
    """Représente une boucle REPEAT minimale.

    Args:
        statements: Corps exécuté avant test.
        until: Condition d'arrêt.
    """

    statements: tuple[Assignment, ...] = field(default_factory=tuple)
    until: Expression | None = None


@dataclass(frozen=True)
class ForStatement:
    """Représente une boucle FOR minimale.

    Args:
        variable: Variable compteur.
        start: Expression de départ.
        stop: Expression de fin.
        step: Expression de pas optionnelle.
        statements: Corps de boucle.
    """

    variable: str
    start: Expression
    stop: Expression
    step: Expression | None = None
    statements: tuple[Assignment, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class FunctionBlock:
    """Contient les variables et instructions d'un FUNCTION_BLOCK IEC.

    Args:
        name: Nom du bloc de fonctions.
        variables: Déclarations de variables locales supportées.
        assignments: Affectations Structured Text simples.
    """

    name: str
    variables: tuple[VariableDeclaration, ...] = field(default_factory=tuple)
    assignments: tuple[Assignment, ...] = field(default_factory=tuple)
    statements: tuple[Statement, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Valide le nom du bloc et l'unicité des variables.

        Raises:
            ValidationError: Si le nom est vide ou si une variable est dupliquée.
        """
        if not self.name.strip():
            raise ValidationError("Le nom du FUNCTION_BLOCK ne peut pas être vide.")
        names = [variable.name.upper() for variable in self.variables]
        if len(names) != len(set(names)):
            raise ValidationError("Les noms de variables doivent être uniques.")


@dataclass(frozen=True)
class Program:
    """Racine du modèle intermédiaire IEC analysé.

    Args:
        function_blocks: Blocs de fonctions détectés dans la source.
    """

    function_blocks: tuple[FunctionBlock, ...]

    def __post_init__(self) -> None:
        """Valide la présence et l'unicité des blocs de fonctions.

        Raises:
            ValidationError: Si aucun bloc n'est présent ou si un nom est dupliqué.
        """
        if not self.function_blocks:
            raise ValidationError(
                "Le programme doit contenir au moins un FUNCTION_BLOCK."
            )
        names = [block.name.upper() for block in self.function_blocks]
        if len(names) != len(set(names)):
            raise ValidationError("Les noms de FUNCTION_BLOCK doivent être uniques.")


Statement = (
    Assignment
    | IfStatement
    | CaseStatement
    | WhileStatement
    | RepeatStatement
    | ForStatement
)
