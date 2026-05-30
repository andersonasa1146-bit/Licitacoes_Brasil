"""Consulta ao Portal Nacional de Contratações Públicas (PNCP).

Documentação: https://pncp.gov.br/api/consulta/swagger-ui/index.html
API pública, sem autenticação.

Resiliência:
- Retry com backoff exponencial para falhas de rede, 5xx e 429.
- Tolerante a respostas com body inválido (loga e desiste daquela combinação).
- Sleep curto entre páginas para não estressar a API.
"""
from __future__ import annotations

import logging
import time
from datetime import date
from typing import Iterator

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://pncp.gov.br/api/consulta/v1"
TAMANHO_PAGINA = 50
TIMEOUT = 30
SLEEP_ENTRE_PAGINAS = 0.3
MAX_RETRIES = 3
USER_AGENT = (
    "ConectarLicitacoesBot/1.0 "
    "(+github.com/andersonasa1146-bit/Licitacoes_Brasil)"
)


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


def _fetch_pagina(params: dict) -> dict | None:
    """Faz GET com retry. Retorna dict do payload ou None se desistir."""
    headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    url = f"{BASE_URL}/contratacoes/publicacao"

    for tentativa in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, timeout=TIMEOUT, headers=headers)
        except requests.RequestException as e:
            logger.warning("Rede falhou (tentativa %s): %s", tentativa, e)
            time.sleep(2 ** tentativa)
            continue

        # 204 = sem conteúdo (paginação acabou)
        if resp.status_code == 204:
            return None

        # 5xx ou rate-limit → backoff e retry
        if resp.status_code == 429 or resp.status_code >= 500:
            logger.warning(
                "HTTP %s (tentativa %s) — backoff", resp.status_code, tentativa
            )
            time.sleep(2 ** tentativa)
            continue

        # 4xx não recuperável (params errados, etc.) — desiste
        if resp.status_code != 200:
            logger.warning(
                "HTTP %s não recuperável: %s",
                resp.status_code, resp.text[:200],
            )
            return None

        # 200 OK — tenta decodificar JSON
        try:
            return resp.json()
        except ValueError as e:
            logger.warning(
                "JSON inválido (tentativa %s): %s | body[:200]=%r",
                tentativa, e, resp.text[:200],
            )
            time.sleep(2 ** tentativa)
            continue

    logger.error(
        "Esgotadas %s tentativas. Pulando esta combinação. params=%s",
        MAX_RETRIES, params,
    )
    return None


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

        payload = _fetch_pagina(params)
        if payload is None:
            return

        dados = payload.get("data") or []
        if not dados:
            return

        for item in dados:
            yield item

        total_paginas = payload.get("totalPaginas") or 1
        if pagina >= total_paginas:
            return
        pagina += 1
        time.sleep(SLEEP_ENTRE_PAGINAS)


def url_publica(contratacao: dict) -> str:
    """Monta a URL pública do edital no PNCP."""
    cnpj = contratacao.get("orgaoEntidade", {}).get("cnpj", "")
    ano = contratacao.get("anoCompra", "")
    seq = contratacao.get("sequencialCompra", "")
    if cnpj and ano and seq:
        return f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}"
    return "https://pncp.gov.br/"
