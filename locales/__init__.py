"""
Localization helper.
Usage: from locales import t
       t("key", lang)  →  translated string
"""

from locales.ru import STRINGS as RU
from locales.uz import STRINGS as UZ

_LANGS = {"ru": RU, "uz": UZ}


def t(key: str, lang: str = "ru") -> str:
    """Return the translated string for key in the given lang."""
    strings = _LANGS.get(lang, RU)
    return strings.get(key, RU.get(key, f"[{key}]"))
