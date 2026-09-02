# Py_iec

Py_iec est un prototype Python 3.10+ destiné à construire progressivement une
chaîne d'analyse pour des sources d'automatisme conformes à la famille
IEC 61131-3. La demande initiale mentionnait `IEC 61141-3`; le périmètre courant
est documenté sur `IEC 61131-3`, norme usuelle des langages d'automates.

## Objectif

Le projet fournit une base maintenable pour :

- analyser un sous-ensemble Structured Text centré sur `FUNCTION_BLOCK` ;
- représenter les sources dans un modèle intermédiaire typé ;
- signaler explicitement les erreurs de syntaxe, validation et fonctionnalités
  hors périmètre ;
- valider sémantiquement les affectations vers des variables déclarées ;
- préparer de futures extensions vers FBD, LD, SFC ;
- fournir des helpers robustes pour lire les listes documentaires Excel de
  certification et extraire des identifiants textuels avec fallback.

## Périmètre fonctionnel

| Élément IEC | Statut | Notes |
| --- | --- | --- |
| Structured Text `FUNCTION_BLOCK` | Support initial | Nom, sections variables, affectations simples |
| Déclarations `BOOL`, `INT`, `DINT`, `REAL`, `STRING` | Support initial | Sections `VAR`, `VAR_INPUT`, `VAR_OUTPUT` |
| Affectation `variable := expression;` | Support initial | Expression convertie en AST minimal |
| `PROGRAM`, `FUNCTION` | Hors périmètre | Erreur explicite `UnsupportedFeatureError` |
| `IF`, `CASE`, boucles | Support partiel | Parsing minimal non imbriqué |
| Génération Python et runtime | Prototype | Affectations de premier niveau |
| Structured Text `FUNCTION_BLOCK` | Support initial | Nom, section `VAR`, affectations simples |
| Déclarations `BOOL`, `INT`, `DINT`, `REAL`, `STRING` | Support initial | Valeur initiale textuelle optionnelle |
| Affectation `variable := expression;` | Support initial | Expression conservée sous forme textuelle |
| `PROGRAM`, `FUNCTION`, `VAR_INPUT`, `VAR_OUTPUT` | Hors périmètre | Erreur explicite `UnsupportedFeatureError` |
| FBD, LD, SFC, IL | À faire | Non analysés dans cette première base |
| Feuilles Excel `Liste_documentaire`, `Liste_Documentaire` | Support helper | Lecture exacte via `pandas` et `openpyxl` |
| Colonnes dynamiques Excel | Support helper | Recherche regex stricte puis tolérante |
| Validation sémantique | Support initial | Les affectations doivent cibler une variable déclarée |

## Prérequis techniques

- Python 3.10 ou supérieur ;
- `pytest`, `ruff` et `pdoc` pour le développement ;
- optionnellement `pandas` et `openpyxl` pour de futurs traitements Excel.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Utilisation

Analyser l'exemple intégré :

```bash
python -m py_iec --example
```

Analyser un fichier local :

```bash
python -m py_iec chemin/vers/source.st
```

Exemple d'entrée :

```iecst
FUNCTION_BLOCK Counter
VAR_INPUT
    enabled : BOOL;
END_VAR
VAR
    count : INT := 0;
END_VAR
count := count + 1;
END_FUNCTION_BLOCK
```

Exemple de sortie CLI :

```text
FUNCTION_BLOCK Counter: 1 variable(s), 1 affectation(s)
```

## Qualité

Les commandes de développement sont centralisées dans le `Makefile` :

```bash
make run
make lint
make test
make doc
make type
make coverage
```

La documentation HTML est générée localement dans `docs/` et n'est pas
versionnée afin d'éviter les artefacts générés dans le dépôt.

## Architecture

- `src/py_iec/model.py` : dataclasses du modèle intermédiaire ;
- `src/py_iec/parser.py` : parseur Structured Text minimal ;
- `src/py_iec/expressions.py` : AST et parseur Pratt pour expressions ;
- `src/py_iec/types.py` : catalogue des types scalaires IEC ;
- `src/py_iec/type_checker.py` : inférence et validation de types ;
- `src/py_iec/validator.py` : validation sémantique du modèle intermédiaire ;
- `src/py_iec/errors.py` : exceptions publiques ;
- `src/py_iec/excel.py` : helpers de lecture Excel sans chemin absolu ;
- `src/py_iec/extraction.py` : extractions regex stricte, tolérante puis fallback ;
- `src/py_iec/codegen.py` : génération Python prototype ;
- `src/py_iec/runtime.py` : runtime d'exécution minimal ;
- `src/py_iec/diagnostics.py` : diagnostics structurés ;
- `src/py_iec/cli.py` : point d'entrée CLI ;
- `tests/` : tests unitaires et fixture texte légère.

## Conformité et CI

La matrice de conformité détaillée est maintenue dans `docs/compliance.md`.
Le workflow GitHub Actions exécute lint, typage et tests sur plusieurs versions Python.

## Options CLI avancées

```bash
python -m py_iec --example --json
python -m py_iec --example --validate-only
python -m py_iec --example --generate-python
```
