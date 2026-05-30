"""Orquestrador do robô de licitações."""
from __future__ import annotations

import logging
import sys
from datetime import date, timedelta
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src import email_notifier, pncp, storage, telegram_notifier
from src.filtros import contem_palavra_chave

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("licitacoes")


def carregar_config() -> dict:
    cfg_path = Path(__file__).resolve().parent.parent / "config.yaml"
    with open(cfg_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> int:
    load_dotenv()
    cfg = carregar_config()

    hoje = date.today()
    data_inicial = hoje - timedelta(days=1)
    data_final = hoje

    logger.info("Consultando PNCP %s a %s", data_inicial, data_final)

    palavras = cfg.get("palavras_chave", [])
    exclusoes = cfg.get("palavras_exclusao", [])
    modalidades = cfg.get("modalidades", [6])
    ufs = cfg.get("ufs", []) or None
    valor_minimo = float(cfg.get("valor_minimo") or 0)

    candidatos: list[dict] = []
    total_vistos = 0

    for item in pncp.buscar_contratacoes(
        data_inicial, data_final, modalidades, ufs
    ):
        total_vistos += 1
        objeto = item.get("objetoCompra") or ""
        match, kw = contem_palavra_chave(objeto, palavras, exclusoes)
        if not match:
            continue

        valor = item.get("valorTotalEstimado") or 0
        try:
            if float(valor) < valor_minimo:
                continue
        except (TypeError, ValueError):
            pass

        item["_url_publica"] = pncp.url_publica(item)
        item["_palavra_match"] = kw or ""
        candidatos.append(item)

    logger.info("Vistos: %s | Candidatos aderentes: %s",
                total_vistos, len(candidatos))

    novos = storage.filtrar_novos(candidatos)
    logger.info("Novos (após dedup): %s", len(novos))

    if not novos:
        logger.info("Nada novo hoje. Encerrando sem enviar.")
        return 0

    try:
        email_notifier.enviar(novos)
        logger.info("E-mail enviado.")
    except Exception:
        logger.exception("Falha ao enviar e-mail")

    try:
        telegram_notifier.enviar(novos)
        logger.info("Telegram enviado.")
    except Exception:
        logger.exception("Falha ao enviar Telegram")

    storage.marcar_enviados(novos)
    logger.info("Histórico atualizado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
