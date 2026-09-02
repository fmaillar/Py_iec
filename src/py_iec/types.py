"""Définition des types IEC scalaires supportés par Py_iec."""

from __future__ import annotations

from dataclasses import dataclass

from py_iec.errors import ValidationError


@dataclass(frozen=True)
class IecType:
    """Décrit un type scalaire IEC supporté.

    Args:
        name: Nom IEC normalisé.
        category: Catégorie logique du type.
        default: Valeur Python par défaut associée au type.
    """

    name: str
    category: str
    default: object


IEC_TYPES: dict[str, IecType] = {
    "BOOL": IecType("BOOL", "boolean", False),
    "SINT": IecType("SINT", "integer", 0),
    "USINT": IecType("USINT", "integer", 0),
    "INT": IecType("INT", "integer", 0),
    "UINT": IecType("UINT", "integer", 0),
    "DINT": IecType("DINT", "integer", 0),
    "UDINT": IecType("UDINT", "integer", 0),
    "LINT": IecType("LINT", "integer", 0),
    "ULINT": IecType("ULINT", "integer", 0),
    "REAL": IecType("REAL", "real", 0.0),
    "LREAL": IecType("LREAL", "real", 0.0),
    "STRING": IecType("STRING", "string", ""),
    "TIME": IecType("TIME", "time", "T#0s"),
    "DATE": IecType("DATE", "date", "D#1970-01-01"),
    "TIME_OF_DAY": IecType("TIME_OF_DAY", "time_of_day", "TOD#00:00:00"),
    "DATE_AND_TIME": IecType("DATE_AND_TIME", "date_time", "DT#1970-01-01-00:00:00"),
}


def normalize_type(type_name: str) -> str:
    """Normalise et valide un nom de type IEC.

    Args:
        type_name: Nom de type fourni par la source IEC.

    Returns:
        Nom de type IEC normalisé.

    Raises:
        ValidationError: Si le type n'est pas supporté.
    """
    normalized = type_name.upper()
    if normalized not in IEC_TYPES:
        raise ValidationError(f"Type IEC non supporté: {type_name}")
    return normalized


def default_value_for(type_name: str) -> object:
    """Retourne la valeur par défaut Python associée à un type IEC.

    Args:
        type_name: Nom de type IEC à résoudre.

    Returns:
        Valeur par défaut du type demandé.
    """
    return IEC_TYPES[normalize_type(type_name)].default


def are_types_compatible(target_type: str, expression_type: str) -> bool:
    """Indique si une expression peut être affectée à une cible typée.

    Args:
        target_type: Type IEC de la variable cible.
        expression_type: Type IEC inféré pour l'expression.

    Returns:
        ``True`` si l'affectation est autorisée, sinon ``False``.
    """
    target = IEC_TYPES[normalize_type(target_type)]
    expression = IEC_TYPES[normalize_type(expression_type)]
    if target.name == expression.name:
        return True
    return target.category == expression.category and target.category in {
        "integer",
        "real",
    }
