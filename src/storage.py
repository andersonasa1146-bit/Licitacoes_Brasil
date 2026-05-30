"""Deduplicação simples via arquivo JSON commitado no repositório."""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

ARQUIVO = Path("enviados.json")
RETENCAO_DIAS = 60


def _carregar() -> dict:
    if not ARQUIVO.exists():
        return {}
    try:
        return json.loads(ARQUIVO.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def filtrar_novos(processos: list[dict]) -> list[dict]:
    historico = _carregar()
    novos = []
    for p in processos:
        chave = p.get("numeroControlePNCP") or p.get("_chave")
        if not chave:
            continue
        if chave not in historico:
            novos.append(p)
    return novos


def marcar_enviados(processos: list[dict]) -> None:
    historico = _carregar()
    hoje = date.today().isoformat()

    for p in processos:
        chave = p.get("numeroControlePNCP") or p.get("_chave")
        if chave:
            historico[chave] = hoje

    limite = (date.today() - timedelta(days=RETENCAO_DIAS)).isoformat()
    historico = {k: v for k, v in historico.items() if v >= limite}

    ARQUIVO.write_text(
        json.dumps(historico, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
