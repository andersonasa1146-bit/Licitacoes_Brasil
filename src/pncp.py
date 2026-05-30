"""Consulta ao Portal Nacional de Contratações Públicas (PNCP).

Documentação: https://pncp.gov.br/api/consulta/swagger-ui/index.html
API pública, sem autenticação.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Iterator

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://pncp.gov.br/api/consulta/v1"
TAMANHO_PAGINA = 50
TIMEOUT = 30


def _formatar_data(d: date) -> str:
    return d.strftime("%Y%m%d")


def buscar_contratacoes(
    data_inicial: date,
    data_final: date,
    modalidades: list[int],
    ufs: list[str] | None = None,
) -> Iterator[dict]:
    """Itera sobre contratações publicadas no intervalo, por modalidade.

    Se `ufs` for vazio/None, consulta sem filtro de UF (Brasil inteiro).
    """
    ufs_iter = ufs if ufs else [None]

    for modalidade in modalidades:
        for uf in ufs_iter:
            yield from _buscar_uma_combinacao(
                data_inicial, data_final, modalidade, uf
            )


def _buscar_uma_combinacao(
    data_inicial: date,
    data_final: date,
    modalidade: int,
    uf: str | None,
) -> Iterator[dict]:
    pagina = 1
    while True:
        params = {
            "dataInicial": _formatar_data(data_inicial),
            "dataFinal": _formatar_data(data_final),
            "codigoModalidadeContratacao": modalidade,
            "pagina": pagina,
            "tamanhoPagina": TAMANHO_PAGINA,
        }
        if uf:
            params["uf"] = uf

        try:
            resp = requests.get(
                f"{BASE_URL}/contratacoes/publicacao",
                params=params,
                timeout=TIMEOUT,
                headers={"Accept": "application/json"},
            )
        except requests.RequestException as e:
            logger.warning("Falha de rede modalidade=%s uf=%s pagina=%s: %s",
                           modalidade, uf, pagina, e)
            return

        if resp.status_code == 204:
            return
        if resp.status_code != 200:
            logger.warning("HTTP %s modalidade=%s uf=%s pagina=%s",
                           resp.status_code, modalidade, uf, pagina)
            return

        payload = resp.json()
        dados = payload.get("data") or []
        if not dados:
            return

        for item in dados:
            yield item

        total_paginas = payload.get("totalPaginas", 1)
        if pagina >= total_paginas:
            return
        pagina += 1


def url_publica(contratacao: dict) -> str:
    """Monta a URL pública do edital no PNCP a partir do CNPJ + ano + sequencial."""
    cnpj = contratacao.get("orgaoEntidade", {}).get("cnpj", "")
    ano = contratacao.get("anoCompra", "")
    seq = contratacao.get("sequencialCompra", "")
    if cnpj and ano and seq:
        return f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}"
    return "https://pncp.gov.br/"
