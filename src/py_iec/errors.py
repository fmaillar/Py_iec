"""Exceptions dédiées aux erreurs de parsing et de validation IEC."""


class PyIecError(Exception):
    """Classe de base pour toutes les erreurs publiques du paquet."""


class ParseError(PyIecError):
    """Erreur levée lorsqu'une source IEC ne respecte pas la syntaxe supportée."""


class ValidationError(PyIecError):
    """Erreur levée lorsqu'un modèle intermédiaire viole une règle métier."""


class UnsupportedFeatureError(PyIecError):
    """Erreur levée lorsqu'une fonctionnalité IEC connue n'est pas encore supportée."""
