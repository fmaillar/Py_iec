"""Interface en ligne de commande pour le prototype Py_iec."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from py_iec.codegen import generate_python_class
from py_iec.errors import PyIecError
from py_iec.parser import parse_source

_EXAMPLE_SOURCE = """FUNCTION_BLOCK Counter
VAR
    count : INT := 0;
END_VAR
count := count + 1;
END_FUNCTION_BLOCK
"""


def main(argv: Sequence[str] | None = None) -> int:
    """Exécute la CLI et affiche un résumé du programme analysé.

    Args:
        argv: Arguments optionnels, utiles pour les tests unitaires.

    Returns:
        Code de retour POSIX: ``0`` en cas de succès, ``1`` en cas d'erreur.
    """
    parser = argparse.ArgumentParser(
        description="Analyse un sous-ensemble IEC 61131-3."
    )
    parser.add_argument(
        "source", nargs="?", type=Path, help="Fichier source IEC à analyser."
    )
    parser.add_argument(
        "--example", action="store_true", help="Analyse un exemple intégré."
    )
    parser.add_argument(
        "--json", action="store_true", help="Affiche le modèle en JSON."
    )
    parser.add_argument(
        "--validate-only", action="store_true", help="Valide sans afficher de résumé."
    )
    parser.add_argument(
        "--generate-python", action="store_true", help="Génère une classe Python."
    )
    parser.add_argument("--output", type=Path, help="Fichier de sortie optionnel.")
    args = parser.parse_args(argv)

    try:
        source = _load_source(args.source, args.example)
        program = parse_source(source)
    except (OSError, PyIecError, ValueError) as exc:
        print(f"Erreur: {exc}")
        return 1

    if args.validate_only:
        print("Validation OK")
        return 0
    if args.json:
        output = _program_to_json(program)
        _write_or_print(output, args.output)
        return 0
    if args.generate_python:
        output = "\n".join(
            generate_python_class(block) for block in program.function_blocks
        )
        _write_or_print(output, args.output)
        return 0
    for block in program.function_blocks:
        print(
            f"FUNCTION_BLOCK {block.name}: "
            f"{len(block.variables)} variable(s), "
            f"{len(block.assignments)} affectation(s)"
        )
    return 0


def _load_source(path: Path | None, use_example: bool) -> str:
    """Charge la source IEC depuis un fichier ou depuis l'exemple intégré.

    Args:
        path: Chemin optionnel vers un fichier texte IEC.
        use_example: Indique si l'exemple intégré doit être utilisé.

    Returns:
        Contenu IEC à analyser.

    Raises:
        FileNotFoundError: Si le fichier demandé n'existe pas.
        ValueError: Si aucune source n'est fournie.
    """
    if use_example:
        return _EXAMPLE_SOURCE
    if path is None:
        raise ValueError("Fournir un fichier source ou utiliser --example.")
    if not path.is_file():
        raise FileNotFoundError(f"Fichier introuvable: {path}")
    return path.read_text(encoding="utf-8")


def _program_to_json(program: object) -> str:
    """Sérialise un programme en JSON public minimal.

    Args:
        program: Programme Py_iec à sérialiser.

    Returns:
        JSON indenté décrivant les blocs, variables et affectations.
    """
    payload = {
        "function_blocks": [
            {
                "name": block.name,
                "variables": [
                    {
                        "name": variable.name,
                        "type": variable.type_name,
                        "scope": variable.scope,
                    }
                    for variable in block.variables
                ],
                "assignments": [assignment.target for assignment in block.assignments],
            }
            for block in program.function_blocks
        ]
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _write_or_print(output: str, path: Path | None) -> None:
    """Écrit une sortie dans un fichier ou sur stdout.

    Args:
        output: Contenu à écrire.
        path: Chemin optionnel du fichier de sortie.
    """
    if path is None:
        print(output)
        return
    path.write_text(output, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
