# Matrice de conformité IEC 61131-3

| Fonctionnalité | Statut | Module | Tests | Commentaire |
| --- | --- | --- | --- | --- |
| FUNCTION_BLOCK | Support initial | `parser.py`, `model.py` | `test_parser.py` | Parsing textuel minimal |
| VAR / VAR_INPUT / VAR_OUTPUT | Support initial | `parser.py`, `model.py` | `test_parser.py`, `test_model.py` | Portées normalisées |
| Types scalaires | Partiel | `types.py` | `test_type_checker.py` | Types principaux déclarés |
| Expressions | Partiel | `expressions.py` | `test_expressions.py` | Littéraux, références, opérations |
| IF | Partiel | `parser.py`, `model.py` | `test_control_structures.py` | Non imbriqué |
| CASE | Partiel | `parser.py`, `model.py` | `test_control_structures.py` | Branches simples |
| Boucles | Partiel | `parser.py`, `model.py` | `test_control_structures.py` | Parsing minimal |
| Validation sémantique | Partiel | `validator.py`, `type_checker.py` | `test_validator.py`, `test_type_checker.py` | Références et types simples |
| Génération Python | Prototype | `codegen.py` | `test_codegen_runtime.py` | Affectations de premier niveau |
| Runtime | Prototype | `runtime.py` | `test_codegen_runtime.py` | Affectations de premier niveau |
| FBD / LD / SFC / IL | Non supporté | - | - | Hors périmètre actuel |
