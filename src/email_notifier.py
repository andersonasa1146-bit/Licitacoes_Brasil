"""Envio de e-mail via SMTP do Gmail (senha de app)."""
from __future__ import annotations

import os
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape


def _formatar_valor(v) -> str:
    try:
        v = float(v)
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "Não informado"


def _data_br(s: str | None) -> str:
    if not s:
        return "—"
    return s[:10].split("-")[::-1] and "/".join(s[:10].split("-")[::-1])


def _card_html(p: dict) -> str:
    orgao = p.get("orgaoEntidade", {}).get("razaoSocial", "—")
    uf = p.get("unidadeOrgao", {}).get("ufSigla", "—")
    municipio = p.get("unidadeOrgao", {}).get("municipioNome", "—")
    objeto = p.get("objetoCompra", "—")
    valor = _formatar_valor(p.get("valorTotalEstimado"))
    abertura = _data_br(p.get("dataAberturaProposta"))
    encerramento = _data_br(p.get("dataEncerramentoProposta"))
    modalidade = p.get("modalidadeNome", "—")
    url = p.get("_url_publica", "https://pncp.gov.br/")
    palavra = p.get("_palavra_match", "")

    return f"""
    <div style="border:1px solid #d0d7de;border-left:4px solid #0969da;
                border-radius:6px;padding:14px;margin-bottom:14px;
                font-family:Arial,sans-serif;font-size:14px;color:#1f2328;">
      <div style="font-weight:600;font-size:15px;color:#0969da;">
        {escape(orgao)} — {escape(municipio)}/{escape(uf)}
      </div>
      <div style="margin-top:8px;"><b>Objeto:</b> {escape(objeto)}</div>
      <div style="margin-top:6px;"><b>Modalidade:</b> {escape(modalidade)}</div>
      <div><b>Valor estimado:</b> {valor}</div>
      <div><b>Abertura propostas:</b> {abertura} &nbsp;|&nbsp;
           <b>Encerramento:</b> {encerramento}</div>
      <div style="margin-top:6px;color:#57606a;font-size:12px;">
           Match: <i>{escape(palavra)}</i></div>
      <div style="margin-top:10px;">
        <a href="{escape(url)}" style="background:#0969da;color:#fff;
           padding:6px 12px;border-radius:5px;text-decoration:none;">
           Ver edital no PNCP →</a>
      </div>
    </div>
    """


def _montar_html(processos: list[dict]) -> str:
    cards = "\n".join(_card_html(p) for p in processos)
    total_valor = sum(
        float(p.get("valorTotalEstimado") or 0) for p in processos
    )
    total_fmt = _formatar_valor(total_valor)

    return f"""<!doctype html>
<html><body style="background:#f6f8fa;padding:20px;">
<div style="max-width:760px;margin:auto;background:#fff;padding:24px;
            border-radius:8px;font-family:Arial,sans-serif;">
  <h2 style="color:#0969da;margin:0 0 6px 0;">
    Licitações do dia — {date.today().strftime("%d/%m/%Y")}
  </h2>
  <p style="color:#57606a;margin:0 0 16px 0;">
    <b>{len(processos)}</b> novas oportunidades · Valor estimado total: <b>{total_fmt}</b>
  </p>
  {cards}
  <p style="color:#8b949e;font-size:12px;margin-top:20px;">
    Robô de Licitações · Conectar Tecnologia e Engenharia · Fonte: PNCP
  </p>
</div></body></html>"""


def enviar(processos: list[dict]) -> None:
    if not processos:
        return

    user = os.environ["GMAIL_USER"]
    pwd = os.environ["GMAIL_APP_PASSWORD"]
    destinatarios = [
        d.strip() for d in os.environ["EMAIL_DESTINATARIOS"].split(",") if d.strip()
    ]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Licitações] {len(processos)} novas — {date.today():%d/%m/%Y}"
    msg["From"] = f"Robô Licitações Conectar <{user}>"
    msg["To"] = ", ".join(destinatarios)

    html = _montar_html(processos)
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(user, pwd)
        smtp.sendmail(user, destinatarios, msg.as_string())
