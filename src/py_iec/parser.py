"""Parseur minimal pour un sous-ensemble textuel IEC 61131-3."""

from __future__ import annotations

import re

from py_iec.errors import ParseError, UnsupportedFeatureError
from py_iec.expressions import parse_expression
from py_iec.model import (
    Assignment,
    CaseBranch,
    CaseStatement,
    ForStatement,
    FunctionBlock,
    IfStatement,
    Program,
    RepeatStatement,
    Statement,
    VariableDeclaration,
    WhileStatement,
)
from py_iec.validator import validate_program

_IDENTIFIER = r"[A-Za-z_][A-Za-z0-9_]*"
_BLOCK_RE = re.compile(
    rf"FUNCTION_BLOCK\s+(?P<name>{_IDENTIFIER})(?P<body>.*?)END_FUNCTION_BLOCK",
    re.IGNORECASE | re.DOTALL,
)
_VAR_SECTION_RE = re.compile(
    r"(?P<header>VAR(?:_INPUT|_OUTPUT)?)(?P<body>.*?)END_VAR",
    re.IGNORECASE | re.DOTALL,
)
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
_UNSUPPORTED_TOKENS = ("PROGRAM", "FUNCTION ")


def parse_source(source: str, validate: bool = True) -> Program:
    """Analyse une source IEC et retourne un programme intermédiaire.

    Args:
        source: Texte IEC contenant au moins un ``FUNCTION_BLOCK``.
        validate: Active la validation sémantique après le parsing.

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
    program = Program(function_blocks=blocks)
    if validate:
        validate_program(program)
    return program


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
    statements = _parse_statements(executable_body)
    assignments = tuple(
        statement for statement in statements if isinstance(statement, Assignment)
    )
    return FunctionBlock(
        name=name, variables=variables, assignments=assignments, statements=statements
    )


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
            scope = section.group("header").upper()
            if strict:
                variables.append(_variable_from_match(strict, scope))
                continue
            tolerant = _TOLERANT_VAR_RE.search(line)
            if tolerant:
                variables.append(_variable_from_match(tolerant, scope))
                continue
            raise ParseError(f"Déclaration de variable invalide: {line}")
    return tuple(variables)


def _variable_from_match(match: re.Match[str], scope: str) -> VariableDeclaration:
    """Construit une déclaration depuis une correspondance stricte ou tolérante.

    Args:
        match: Correspondance contenant au minimum ``name`` et ``type``.
        scope: Section IEC déclarative d'origine.

    Returns:
        Déclaration de variable validée.
    """
    initial = match.groupdict().get("initial")
    return VariableDeclaration(
        name=match.group("name"),
        type_name=match.group("type"),
        initial_value=initial.strip() if initial else None,
        scope=scope,
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
                expression=parse_expression(match.group("expression").strip()),
            )
        )
    return tuple(assignments)


def _parse_statements(body: str) -> tuple[Statement, ...]:
    """Extrait les instructions Structured Text du corps exécutable.

    Args:
        body: Corps exécutable sans sections déclaratives.

    Returns:
        Tuple d'instructions supportées.

    Raises:
        ParseError: Si une instruction structurée est incomplète.
    """
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    statements: list[Statement] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        upper = line.upper()
        if upper.startswith("IF "):
            statement, index = _parse_if_statement(lines, index)
            statements.append(statement)
            continue
        if upper.startswith("CASE "):
            statement, index = _parse_case_statement(lines, index)
            statements.append(statement)
            continue
        if upper.startswith("WHILE "):
            statement, index = _parse_while_statement(lines, index)
            statements.append(statement)
            continue
        if upper.startswith("REPEAT"):
            statement, index = _parse_repeat_statement(lines, index)
            statements.append(statement)
            continue
        if upper.startswith("FOR "):
            statement, index = _parse_for_statement(lines, index)
            statements.append(statement)
            continue
        statements.extend(_parse_assignments(line))
        index += 1
    return tuple(statements)


def _parse_if_statement(lines: list[str], start: int) -> tuple[IfStatement, int]:
    """Parse une instruction IF non imbriquée.

    Args:
        lines: Lignes exécutables.
        start: Index de la ligne ``IF``.

    Returns:
        Instruction IF et index suivant.
    """
    header = lines[start]
    match = re.match(r"IF\s+(?P<condition>.*?)\s+THEN\s*$", header, re.IGNORECASE)
    if match is None:
        raise ParseError(f"Instruction IF invalide: {header}")
    then_lines: list[str] = []
    else_lines: list[str] = []
    target = then_lines
    index = start + 1
    while index < len(lines):
        upper = lines[index].upper()
        if upper == "ELSE":
            target = else_lines
            index += 1
            continue
        if upper == "END_IF":
            return (
                IfStatement(
                    condition=parse_expression(match.group("condition")),
                    then_statements=_parse_assignments("\n".join(then_lines)),
                    else_statements=_parse_assignments("\n".join(else_lines)),
                ),
                index + 1,
            )
        target.append(lines[index])
        index += 1
    raise ParseError("Instruction IF sans END_IF.")


def _parse_case_statement(lines: list[str], start: int) -> tuple[CaseStatement, int]:
    """Parse une instruction CASE non imbriquée.

    Args:
        lines: Lignes exécutables.
        start: Index de la ligne ``CASE``.

    Returns:
        Instruction CASE et index suivant.
    """
    header = lines[start]
    match = re.match(r"CASE\s+(?P<selector>.*?)\s+OF\s*$", header, re.IGNORECASE)
    if match is None:
        raise ParseError(f"Instruction CASE invalide: {header}")
    branches: list[CaseBranch] = []
    else_lines: list[str] = []
    index = start + 1
    while index < len(lines):
        line = lines[index]
        upper = line.upper()
        if upper == "END_CASE":
            return (
                CaseStatement(
                    selector=parse_expression(match.group("selector")),
                    branches=tuple(branches),
                    else_statements=_parse_assignments("\n".join(else_lines)),
                ),
                index + 1,
            )
        if upper == "ELSE":
            index += 1
            while index < len(lines) and lines[index].upper() != "END_CASE":
                else_lines.append(lines[index])
                index += 1
            continue
        branch_match = re.match(r"(?P<values>[^:]+):\s*(?P<body>.*)$", line)
        if branch_match is None:
            raise ParseError(f"Branche CASE invalide: {line}")
        values = tuple(
            value.strip() for value in branch_match.group("values").split(",")
        )
        branches.append(
            CaseBranch(
                values=values,
                statements=_parse_assignments(branch_match.group("body")),
            )
        )
        index += 1
    raise ParseError("Instruction CASE sans END_CASE.")


def _parse_while_statement(lines: list[str], start: int) -> tuple[WhileStatement, int]:
    """Parse une boucle WHILE non imbriquée.

    Args:
        lines: Lignes exécutables.
        start: Index de la ligne ``WHILE``.

    Returns:
        Boucle WHILE et index suivant.
    """
    match = re.match(
        r"WHILE\s+(?P<condition>.*?)\s+DO\s*$",
        lines[start],
        re.IGNORECASE,
    )
    if match is None:
        raise ParseError(f"Instruction WHILE invalide: {lines[start]}")
    body_lines, next_index = _collect_until(lines, start + 1, "END_WHILE")
    return (
        WhileStatement(
            condition=parse_expression(match.group("condition")),
            statements=_parse_assignments("\n".join(body_lines)),
        ),
        next_index,
    )


def _parse_repeat_statement(
    lines: list[str], start: int
) -> tuple[RepeatStatement, int]:
    """Parse une boucle REPEAT non imbriquée.

    Args:
        lines: Lignes exécutables.
        start: Index de la ligne ``REPEAT``.

    Returns:
        Boucle REPEAT et index suivant.
    """
    body_lines: list[str] = []
    index = start + 1
    while index < len(lines):
        match = re.match(
            r"UNTIL\s+(?P<condition>.*?)\s+END_REPEAT\s*$",
            lines[index],
            re.IGNORECASE,
        )
        if match is not None:
            return (
                RepeatStatement(
                    statements=_parse_assignments("\n".join(body_lines)),
                    until=parse_expression(match.group("condition")),
                ),
                index + 1,
            )
        body_lines.append(lines[index])
        index += 1
    raise ParseError("Instruction REPEAT sans UNTIL ... END_REPEAT.")


def _parse_for_statement(lines: list[str], start: int) -> tuple[ForStatement, int]:
    """Parse une boucle FOR non imbriquée.

    Args:
        lines: Lignes exécutables.
        start: Index de la ligne ``FOR``.

    Returns:
        Boucle FOR et index suivant.
    """
    match = re.match(
        r"FOR\s+(?P<var>[A-Za-z_][A-Za-z0-9_]*)\s*:=\s*(?P<start>.*?)\s+TO\s+"
        r"(?P<stop>.*?)(?:\s+BY\s+(?P<step>.*?))?\s+DO\s*$",
        lines[start],
        re.IGNORECASE,
    )
    if match is None:
        raise ParseError(f"Instruction FOR invalide: {lines[start]}")
    body_lines, next_index = _collect_until(lines, start + 1, "END_FOR")
    step = match.group("step")
    return (
        ForStatement(
            variable=match.group("var"),
            start=parse_expression(match.group("start")),
            stop=parse_expression(match.group("stop")),
            step=parse_expression(step) if step else None,
            statements=_parse_assignments("\n".join(body_lines)),
        ),
        next_index,
    )


def _collect_until(
    lines: list[str], start: int, terminator: str
) -> tuple[list[str], int]:
    """Collecte les lignes jusqu'à un terminateur exclusif.

    Args:
        lines: Lignes exécutables.
        start: Index de départ.
        terminator: Mot-clé terminateur attendu.

    Returns:
        Lignes collectées et index suivant le terminateur.

    Raises:
        ParseError: Si le terminateur est absent.
    """
    body_lines: list[str] = []
    index = start
    while index < len(lines):
        if lines[index].upper() == terminator:
            return body_lines, index + 1
        body_lines.append(lines[index])
        index += 1
    raise ParseError(f"Terminateur absent: {terminator}")
