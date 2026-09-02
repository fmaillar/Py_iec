"""Tests de non-régression basés sur fixtures Structured Text."""

from pathlib import Path

import pytest

from py_iec.errors import ValidationError
from py_iec.parser import parse_source

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "st"
VALID_FIXTURES = tuple((FIXTURE_ROOT / "valid").glob("*.st"))
INVALID_FIXTURES = tuple((FIXTURE_ROOT / "invalid").glob("*.st"))


@pytest.mark.parametrize("fixture", VALID_FIXTURES)
def test_valid_structured_text_fixtures(fixture: Path) -> None:
    """Vérifie que les fixtures ST valides restent parseables."""
    parse_source(fixture.read_text(encoding="utf-8"))


@pytest.mark.parametrize("fixture", INVALID_FIXTURES)
def test_invalid_structured_text_fixtures(fixture: Path) -> None:
    """Vérifie que les fixtures ST invalides restent rejetées."""
    with pytest.raises(ValidationError):
        parse_source(fixture.read_text(encoding="utf-8"))
