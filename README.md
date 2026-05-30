# Robô de Licitações — Conectar

Busca diária no PNCP (Portal Nacional de Contratações Públicas) por licitações nas áreas de atuação da Conectar e envia resumo por **e-mail** e **grupo Telegram**.

## Áreas monitoradas
Elétrica, redes de computadores, cabeamento estruturado, fibra óptica, dutos para telecomunicações, racks, pontos de rede e correlatos.

## Custo operacional
**R$ 0,00/mês.** Roda em GitHub Actions (free tier), envia por SMTP do Gmail e Telegram Bot API.

---

## Setup — passo a passo (uma vez)

### 1. Criar o bot Telegram

1. No Telegram, abra `@BotFather`
2. Envie `/newbot`
3. Escolha nome (ex: `Conectar Licitações`) e username (ex: `conectar_licitacoes_bot`)
4. **Guarde o token** que ele envia (formato `123456:ABC-DEF...`)

### 2. Adicionar o bot ao grupo "Licitações Brasil"

1. Abra o grupo no Telegram → Adicionar membros → busque o username do bot
2. Dê permissão de **enviar mensagens** ao bot
3. Para pegar o `chat_id` do grupo:
   - Envie qualquer mensagem no grupo
   - Abra no navegador: `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates`
   - Procure por `"chat":{"id":-1001234567890,...}` — esse número (com sinal de menos) é o **chat_id**

### 3. Senha de app do Gmail

1. Conta Google → Segurança → **Verificação em duas etapas** (precisa estar ativa)
2. **Senhas de app** → Criar nova → nome: `licitacoes-conectar`
3. **Guarde a senha de 16 caracteres** gerada (não é sua senha normal)

### 4. Subir para o GitHub

```powershell
cd "C:\Users\DELL\Desktop\Analista de Ddaos AND\licitacoes-conectar"
git init
git add .
git commit -m "init: robô de licitações"
git branch -M main
git remote add origin https://github.com/<seu-usuario>/<seu-repo>.git
git push -u origin main
```

### 5. Configurar Secrets no GitHub

Vá em **Settings → Secrets and variables → Actions → New repository secret** e cadastre:

| Nome | Valor |
|---|---|
| `GMAIL_USER` | `andersonasa1146@gmail.com` |
| `GMAIL_APP_PASSWORD` | senha de app de 16 caracteres |
| `EMAIL_DESTINATARIOS` | `andersonasa1146@gmail.com` (separe por vírgula se mais de um) |
| `TELEGRAM_BOT_TOKEN` | token do BotFather |
| `TELEGRAM_CHAT_ID` | chat_id do grupo (com sinal de menos) |

### 6. Habilitar GitHub Actions

Em **Actions** → Enable workflows. O cron está agendado para rodar **às 07h de Brasília** todo dia útil.

Para testar antes: **Actions → Buscar Licitações → Run workflow** (rodar manualmente).

---

## Rodar local (opcional, para desenvolvimento)

```powershell
cd licitacoes-conectar
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Edite .env com suas credenciais
python -m src.main
```

---

## Estrutura

```
licitacoes-conectar/
├── .github/workflows/licitacoes.yml    # cron diário
├── src/
│   ├── main.py                          # orquestrador
│   ├── pncp.py                          # consulta PNCP API
│   ├── filtros.py                       # palavras-chave + matching
│   ├── email_notifier.py                # SMTP Gmail
│   ├── telegram_notifier.py             # Bot API
│   └── storage.py                       # deduplicação (JSON commitado)
├── config.yaml                          # palavras-chave, UFs
├── enviados.json                        # histórico (auto-commit pelo bot)
├── requirements.txt
└── .env.example
```

## Ajustar palavras-chave
Edite `config.yaml`. As mudanças entram em vigor na próxima execução.

## Logs e falhas
GitHub Actions mostra o log de cada execução. Se algo falhar, você recebe um e-mail automático do GitHub.
