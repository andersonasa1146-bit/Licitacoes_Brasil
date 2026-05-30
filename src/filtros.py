"""Normalização e matching de palavras-chave."""
from __future__ import annotations

import unicodedata


def normalizar(texto: str) -> str:
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    return sem_acento.lower()


def contem_palavra_chave(
    objeto: str,
    palavras_chave: list[str],
    palavras_exclusao: list[str],
) -> tuple[bool, str | None]:
    objeto_norm = normalizar(objeto)

    for excl in palavras_exclusao:
        if normalizar(excl) in objeto_norm:
            return False, None

    for kw in palavras_chave:
        if normalizar(kw) in objeto_norm:
            return True, kw

    return False, None
