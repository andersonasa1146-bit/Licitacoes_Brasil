"""Envio para grupo Telegram via Bot API."""
from __future__ import annotations

import logging
import os
import time

import requests

logger = logging.getLogger(__name__)

MAX_CHARS = 4000


def _formatar_valor(v) -> str:
    try:
        v = float(v)
        return f"R$ {v:,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return "valor não informado"


def _linha_processo(p: dict, idx: int) -> str:
    orgao = p.get("orgaoEntidade", {}).get("razaoSocial", "—")
    uf = p.get("unidadeOrgao", {}).get("ufSigla", "")
    municipio = p.get("unidadeOrgao", {}).get("municipioNome", "")
    objeto = (p.get("objetoCompra") or "").strip()
    if len(objeto) > 180:
        objeto = objeto[:177] + "..."
    valor = _formatar_valor(p.get("valorTotalEstimado"))
    abertura = (p.get("dataAberturaProposta") or "")[:10]
    if abertura:
        abertura = "/".join(abertura.split("-")[::-1])
    url = p.get("_url_publica", "")

    local = f"{municipio}/{uf}" if municipio else uf

    return (
        f"\n*{idx}. {_escapar(orgao)} — {_escapar(local)}*\n"
        f"{_escapar(objeto)}\n"
        f"💰 {valor}   📅 abre {abertura or '—'}\n"
        f"🔗 [Ver edital no PNCP]({url})\n"
    )


def _escapar(s: str) -> str:
    # Markdown V1 do Telegram: escapar apenas *, _, ` e [
    return (
        s.replace("\\", "\\\\")
         .replace("*", "\\*")
         .replace("_", "\\_")
         .replace("`", "\\`")
         .replace("[", "\\[")
    )


def _quebrar_em_mensagens(processos: list[dict]) -> list[str]:
    from datetime import date
    header = (
        f"🔔 *{len(processos)} novas licitações* "
        f"({date.today():%d/%m/%Y})\n"
        f"_Elétrica · Redes · Telecom · Cabeamento_\n"
    )

    mensagens = []
    atual = header
    for i, p in enumerate(processos, 1):
        linha = _linha_processo(p, i)
        if len(atual) + len(linha) > MAX_CHARS:
            mensagens.append(atual)
            atual = linha
        else:
            atual += linha
    if atual.strip():
        mensagens.append(atual)
    return mensagens


def enviar(processos: list[dict]) -> None:
    if not processos:
        return

    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    for msg in _quebrar_em_mensagens(processos):
        try:
            resp = requests.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": msg,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True,
                },
                timeout=30,
            )
            if resp.status_code != 200:
                logger.warning("Telegram retornou %s: %s",
                               resp.status_code, resp.text[:300])
            time.sleep(1)  # respeita rate limit (30 msg/s, mas conservador)
        except requests.RequestException as e:
            logger.warning("Falha ao enviar Telegram: %s", e)
