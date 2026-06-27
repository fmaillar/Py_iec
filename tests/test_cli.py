"""Tests de l'interface en ligne de commande."""

from pytest import CaptureFixture

from py_iec.cli import main


def test_cli_without_source_returns_error(capsys: CaptureFixture[str]) -> None:
    """Vérifie qu'une source manquante produit une erreur lisible."""
    exit_code = main([])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Fournir un fichier source" in captured.out


def test_cli_example_outputs_summary(capsys: CaptureFixture[str]) -> None:
    """Vérifie que l'exemple intégré produit un résumé lisible."""
    exit_code = main(["--example"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "FUNCTION_BLOCK Counter" in captured.out


def test_cli_json_outputs_model(capsys: CaptureFixture[str]) -> None:
    """Vérifie la sortie JSON de la CLI."""
    exit_code = main(["--example", "--json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"function_blocks"' in captured.out


def test_cli_generate_python_outputs_class(capsys: CaptureFixture[str]) -> None:
    """Vérifie la génération Python via la CLI."""
    exit_code = main(["--example", "--generate-python"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "class Counter" in captured.out
