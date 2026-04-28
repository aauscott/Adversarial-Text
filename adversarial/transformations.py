"""Text transformations that simulate common obfuscation patterns."""

from __future__ import annotations

import random
import string
from typing import Iterable

# Visual confusables; some are font-dependent, so this set favors common high-similarity glyphs.
HOMOGLYPH_MAP = {
    "a": ("а", "α"),  # cyrillic a, greek alpha
    "c": ("с"),  # cyrillic es
    "e": ("е"),  # cyrillic ie
    "h": ("һ"),  # cyrillic shha
    "i": ("і"),  # cyrillic byelorussian-ukrainian i
    "j": ("ј"),  # cyrillic je
    "o": ("о", "ο", "օ"),  # cyrillic o, greek omicron, armenian oh
    "p": ("р", "ρ"),  # cyrillic er, greek rho
    "s": ("ѕ", "ս"),  # cyrillic dze, armenian se
    "t": ("τ", "т", "ե"),  # greek tau, cyrillic te, armenian ech
    "w": ("ա"),  # armenian ayb
    "x": ("х", "χ"),  # cyrillic ha, greek chi
    "y": ("у"),  # cyrillic u
    "A": ("Α", "А", "Ꭺ"),  # greek alpha, cyrillic a, cherokee a
    "B": ("Β", "В", "Ᏼ"),  # greek beta, cyrillic ve, cherokee yv
    "C": ("С"),  # cyrillic es
    "E": ("Ε", "Е", "Ꭼ"),  # greek epsilon, cyrillic ie, cherokee gv
    "F": ("Բ"),  # armenian ben
    "H": ("Η", "Н", "Ꮋ"),  # greek eta, cyrillic en, armenian ho, cherokee mi
    "I": ("Ι", "І", "Ӏ"),  # greek iota, cyrillic i, cyrillic palochka
    "J": ("Ј"),  # cyrillic je
    "K": ("Κ", "К", "Ꮶ"),  # greek kappa, cyrillic ka, cherokee ko
    "M": ("Μ", "М", "Ꮇ"),  # greek mu, cyrillic em, armenian men, cherokee lu
    "N": ("Ν", "Ꮑ"),  # greek nu, cherokee hna
    "O": ("Ο", "О", "Օ", "Ꮎ"),  # greek omicron, cyrillic o, armenian oh, cherokee na
    "P": ("Ρ", "Р", "Ꮲ"),  # greek rho, cyrillic er, cherokee tlv
    "S": ("Ѕ"),  # cyrillic dze
    "T": ("Τ", "Т", "Ꭲ"),  # greek tau, cyrillic te, cherokee i
    "U": ("Ա", "Ս", "Մ"),  # armenian ayb, armenian se, armenian men
    "X": ("Χ", "Х"),  # greek chi, cyrillic ha
    "Y": ("Υ", "Ү"),  # greek upsilon, cyrillic straight u
    "Z": ("Ζ", "Ꮓ"),  # greek zeta, cherokee tsa
}

LEETSPEAK_MAP = {
    "a": "4",
    "b": "8",
    "e": "3",
    "g": "9",
    "i": "1",
    "l": "1",
    "o": "0",
    "s": "$",
    "t": "7",
    "z": "2",
}

PUNCTUATION_NOISE = "._-!@#$%^&*"
KEYBOARD_CHARS = string.ascii_letters + string.digits + string.punctuation


def _pick_rng(rng: random.Random | None = None) -> random.Random:
    return rng if rng is not None else random.Random()


def _replace_with_probability(
    text: str,
    mapping: dict[str, str | tuple[str, ...]],
    probability: float,
    rng: random.Random | None = None,
) -> str:
    local_rng = _pick_rng(rng)

    def pick_replacement(value: str | tuple[str, ...]) -> str:
        if isinstance(value, tuple):
            return local_rng.choice(value)
        return value

    out: list[str] = []
    for ch in text:
        if ch in mapping and local_rng.random() < probability:
            out.append(pick_replacement(mapping[ch]))
        elif ch.lower() in mapping and local_rng.random() < probability:
            replacement = pick_replacement(mapping[ch.lower()])
            out.append(replacement.upper() if ch.isupper() else replacement)
        else:
            out.append(ch)
    return "".join(out)


def homoglyph_substitution(
    text: str,
    probability: float = 0.25,
    rng: random.Random | None = None,
) -> str:
    """Replace characters with visually similar unicode lookalikes."""
    return _replace_with_probability(text=text, mapping=HOMOGLYPH_MAP, probability=probability, rng=rng)


def leetspeak_transformation(
    text: str,
    probability: float = 0.25,
    rng: random.Random | None = None,
) -> str:
    """Apply common leetspeak character substitutions."""
    return _replace_with_probability(text=text, mapping=LEETSPEAK_MAP, probability=probability, rng=rng)


def spacing_punctuation_noise(
    text: str,
    probability: float = 0.1,
    extra_chars: Iterable[str] = PUNCTUATION_NOISE,
    rng: random.Random | None = None,
) -> str:
    """Inject extra spacing or punctuation to break token patterns."""
    local_rng = _pick_rng(rng)
    noise_chars = list(extra_chars)
    out: list[str] = []
    for ch in text:
        out.append(ch)
        if ch.isspace():
            continue
        if local_rng.random() < probability:
            out.append(local_rng.choice(noise_chars))
        if local_rng.random() < probability:
            out.append(" ")
    return "".join(out)


def random_character_noise(
    text: str,
    probability: float = 0.06,
    rng: random.Random | None = None,
) -> str:
    """Insert, delete, or swap characters at random positions."""
    local_rng = _pick_rng(rng)
    chars = list(text)
    i = 0
    while i < len(chars):
        if local_rng.random() >= probability:
            i += 1
            continue

        op = local_rng.choice(["insert", "delete", "swap"])
        if op == "insert":
            chars.insert(i, local_rng.choice(KEYBOARD_CHARS))
            i += 2
        elif op == "delete":
            chars.pop(i)
        else:
            if i + 1 < len(chars):
                chars[i], chars[i + 1] = chars[i + 1], chars[i]
            i += 2

    return "".join(chars)
