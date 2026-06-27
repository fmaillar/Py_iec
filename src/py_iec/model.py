"""Modèle intermédiaire typé pour un sous-ensemble IEC 61131-3."""

from dataclasses import dataclass, field

from py_iec.errors import ValidationError

SUPPORTED_TYPES = {"BOOL", "INT", "DINT", "REAL", "STRING"}


@dataclass(frozen=True)
class VariableDeclaration:
    """Décrit une variable déclarée dans un bloc de fonctions IEC.

    Args:
        name: Nom symbolique de la variable.
        type_name: Type IEC de la variable.
        initial_value: Valeur initiale optionnelle sous forme textuelle.
    """

    name: str
    type_name: str
    initial_value: str | None = None

    def __post_init__(self) -> None:
        """Valide le nom et le type de la variable après instanciation.

        Raises:
            ValidationError: Si le nom est vide ou si le type n'est pas supporté.
        """
        if not self.name.strip():
            raise ValidationError("Le nom de variable ne peut pas être vide.")
        normalized_type = self.type_name.upper()
        if normalized_type not in SUPPORTED_TYPES:
            raise ValidationError(f"Type IEC non supporté: {self.type_name}")
        object.__setattr__(self, "type_name", normalized_type)


@dataclass(frozen=True)
class Assignment:
    """Représente une affectation Structured Text simple.

    Args:
        target: Variable cible à gauche de l'opérateur ``:=``.
        expression: Expression textuelle à droite de l'opérateur.
    """

    target: str
    expression: str

    def __post_init__(self) -> None:
        """Valide la présence d'une cible et d'une expression.

        Raises:
            ValidationError: Si la cible ou l'expression est vide.
        """
        if not self.target.strip():
            raise ValidationError("La cible d'affectation ne peut pas être vide.")
        if not self.expression.strip():
            raise ValidationError("L'expression d'affectation ne peut pas être vide.")


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
