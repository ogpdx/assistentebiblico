"""
Ponto de entrada do módulo interpreter.
"""

from src.interpreter.models import (
    CommandType,
    InterpretedCommand,
    NavigationCommand,
    BibleReferenceCommand,
    UnknownCommand,
)
from src.interpreter.command_classifier import classify_command
from src.interpreter.normalizer import normalize_text
from src.interpreter.number_converter import convert_spoken_numbers_in_text
from src.interpreter.validator import is_valid_bible_reference

__all__ = [
    "CommandType",
    "InterpretedCommand",
    "NavigationCommand",
    "BibleReferenceCommand",
    "UnknownCommand",
    "classify_command",
    "normalize_text",
    "convert_spoken_numbers_in_text",
    "is_valid_bible_reference",
]
