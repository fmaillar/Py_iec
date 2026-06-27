"""Parseur minimal pour un sous-ensemble textuel IEC 61131-3."""

from __future__ import annotations

import re

from py_iec.errors import ParseError, UnsupportedFeatureError
from py_iec.model import Assignment, FunctionBlock, Program, VariableDeclaration

_IDENTIFIER = r"[A-Za-z_][A-Za-z0-9_]*"
_BLOCK_RE = re.compile(
    rf"FUNCTION_BLOCK\s+(?P<name>{_IDENTIFIER})(?P<body>.*?)END_FUNCTION_BLOCK",
    re.IGNORECASE | re.DOTALL,
)
_VAR_SECTION_RE = re.compile(r"VAR(?P<body>.*?)END_VAR", re.IGNORECASE | re.DOTALL)
_STRICT_VAR_RE = re.compile(
    rf"^\s*(?P<name>{_IDENTIFIER})\s*:\s*(?P<type>{_IDENTIFIER})"
    r"(?:\s*:=\s*(?P<initial>[^;]+))?\s*;\s*$",
    re.IGNORECASE,
)
_TOLERANT_VAR_RE = re.compile(
    rf"(?P<name>{_IDENTIFIER})\s*:\s*(?P<type>{_IDENTIFIER})",
    re.IGNORECASE,
)
_ASSIGNMENT_RE = re.compile(
    rf"^\s*(?P<target>{_IDENTIFIER})\s*:=\s*(?P<expression>[^;]+)\s*;\s*$",
    re.IGNORECASE,
)
_UNSUPPORTED_TOKENS = ("PROGRAM", "FUNCTION ", "VAR_INPUT", "VAR_OUTPUT")


def parse_source(source: str) -> Program:
    """Analyse une source IEC et retourne un programme intermédiaire.

    Args:
        source: Texte IEC contenant au moins un ``FUNCTION_BLOCK``.

    Returns:
        Programme typé contenant les blocs, variables et affectations supportés.

    Raises:
        ParseError: Si la source est vide ou ne correspond pas à la grammaire minimale.
        UnsupportedFeatureError: Si une construction IEC connue est détectée mais
            non supportée.
    """
    if not source or not source.strip():
        raise ParseError("La source IEC est vide.")
    _detect_unsupported_features(source)
    blocks = tuple(_parse_function_block(match) for match in _BLOCK_RE.finditer(source))
    if not blocks:
        raise ParseError("Aucun FUNCTION_BLOCK complet n'a été trouvé.")
    return Program(function_blocks=blocks)


def _detect_unsupported_features(source: str) -> None:
    """Détecte les constructions IEC explicitement hors périmètre.

    Args:
        source: Texte IEC brut.

    Raises:
        UnsupportedFeatureError: Si une construction hors périmètre est trouvée.
    """
    normalized = source.upper()
    for token in _UNSUPPORTED_TOKENS:
        if token in normalized:
            raise UnsupportedFeatureError(
                f"Construction non supportée: {token.strip()}"
            )


def _parse_function_block(match: re.Match[str]) -> FunctionBlock:
    """Convertit une correspondance regex en bloc de fonctions typé.

    Args:
        match: Correspondance issue de ``_BLOCK_RE``.

    Returns:
        Bloc de fonctions validé.

    Raises:
        ParseError: Si une ligne du corps ne peut pas être analysée.
    """
    name = match.group("name")
    body = match.group("body")
    variables = _parse_variables(body)
    executable_body = _VAR_SECTION_RE.sub("", body)
    assignments = _parse_assignments(executable_body)
    return FunctionBlock(name=name, variables=variables, assignments=assignments)


def _parse_variables(body: str) -> tuple[VariableDeclaration, ...]:
    """Extrait les déclarations de variables avec deux passes de tolérance.

    Args:
        body: Corps d'un ``FUNCTION_BLOCK``.

    Returns:
        Tuple de déclarations de variables.

    Raises:
        ParseError: Si une déclaration non vide n'est pas reconnue.
    """
    variables: list[VariableDeclaration] = []
    for section in _VAR_SECTION_RE.finditer(body):
        for raw_line in section.group("body").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            strict = _STRICT_VAR_RE.match(line)
            if strict:
                variables.append(_variable_from_match(strict))
                continue
            tolerant = _TOLERANT_VAR_RE.search(line)
            if tolerant:
                variables.append(_variable_from_match(tolerant))
                continue
            raise ParseError(f"Déclaration de variable invalide: {line}")
    return tuple(variables)


def _variable_from_match(match: re.Match[str]) -> VariableDeclaration:
    """Construit une déclaration depuis une correspondance stricte ou tolérante.

    Args:
        match: Correspondance contenant au minimum ``name`` et ``type``.

    Returns:
        Déclaration de variable validée.
    """
    initial = match.groupdict().get("initial")
    return VariableDeclaration(
        name=match.group("name"),
        type_name=match.group("type"),
        initial_value=initial.strip() if initial else None,
    )


def _parse_assignments(body: str) -> tuple[Assignment, ...]:
    """Extrait les affectations Structured Text simples.

    Args:
        body: Corps exécutable sans sections ``VAR``.

    Returns:
        Tuple d'affectations validées.

    Raises:
        ParseError: Si une instruction non vide ne correspond pas à une affectation.
    """
    assignments: list[Assignment] = []
    for raw_statement in body.splitlines():
        statement = raw_statement.strip()
        if not statement:
            continue
        match = _ASSIGNMENT_RE.match(statement)
        if not match:
            raise ParseError(f"Instruction non supportée ou invalide: {statement}")
        assignments.append(
            Assignment(
                target=match.group("target"),
                expression=match.group("expression").strip(),
            )
        )
    return tuple(assignments)
