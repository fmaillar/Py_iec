"""Tests du parseur Structured Text minimal."""

from pathlib import Path

import pytest

from py_iec.errors import ParseError, UnsupportedFeatureError
from py_iec.parser import parse_source

FIXTURE = Path(__file__).parent / "fixtures" / "counter.st"


def test_parse_valid_function_block_fixture() -> None:
    """Vérifie le parsing d'un bloc de fonctions valide."""
    program = parse_source(FIXTURE.read_text(encoding="utf-8"))

    block = program.function_blocks[0]
    assert block.name == "Counter"
    assert len(block.variables) == 2
    assert block.assignments[0].target == "count"


def test_empty_source_is_rejected() -> None:
    """Vérifie qu'une source vide déclenche une erreur de parsing."""
    with pytest.raises(ParseError):
        parse_source("   ")


def test_unsupported_program_construct_is_explicit() -> None:
    """Vérifie qu'une construction connue mais hors périmètre est explicite."""
    with pytest.raises(UnsupportedFeatureError):
        parse_source("PROGRAM Main\nEND_PROGRAM")


def test_tolerant_variable_pass_accepts_missing_semicolon() -> None:
    """Vérifie la seconde passe tolérante pour les déclarations partielles."""
    source = """FUNCTION_BLOCK Counter
VAR
    count : INT
END_VAR
count := count + 1;
END_FUNCTION_BLOCK
"""

    program = parse_source(source)

    assert program.function_blocks[0].variables[0].name == "count"
