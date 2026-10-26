# AI IT Analyst Agent

Agente de IA ([Agno](https://github.com/agno-agi/agno)) que atende chamados de TI no Acelerato de forma autônoma: cargas de preço, vouchers, derrubada de packs, troca de senha na Bluesoft e importação de e-books na Zanthus. As automações web usam Playwright em modo headless.

## Como funciona

1. A cada 2 minutos lista os chamados pendentes da equipe.
2. Chamados com palavra-chave no título (`carga`, `voucher`, `senha`...) vão para o agente, que executa a ferramenta certa e responde no chamado.
3. Cada chamado atendido é acompanhado por **3 dias**: comentários novos do solicitante são respondidos; o acompanhamento para quando o chamado é concluído, excluído ou retirado da IA.
4. Se uma ferramenta falha, a resposta avisa que basta comentar no chamado para tentar de novo.
5. Um chamado com `__pause__` no título pausa a IA até ser concluído.
6. Envia um ping de saúde por hora ao [Palantir](#monitoramento).

## Estrutura

```
Agente.py            ponto de entrada: monta as peças e inicia o loop
agente/
  config.py          parâmetros (palavras-chave, intervalos, modelo, URLs)
  acelerato.py       adapter da API do Acelerato com dados tipados
  ia.py              modelo, agente Agno, hook de falha e Atendente
  monitor.py         loop de chamados e acompanhamento de 3 dias
  palantir.py        ping de monitoramento
data/                ferramentas do agente (Playwright + API)
instructions/        prompts do agente
tests/
```

## Executar

Copie `.env.example` para `.env` e preencha as credenciais.

**Docker (recomendado)**

```bash
docker compose up -d --build
docker compose logs -f
```

**Local**

```bash
uv sync
uv run playwright install chromium
uv run python Agente.py
```

## Configuração

| Onde | O quê |
|---|---|
| `agente/config.py` | Palavras-chave, dias de acompanhamento, intervalos, modelo |
| `.env` | Credenciais, URLs dos sistemas (Acelerato, Zanthus, Bluesoft, painel) e `PALANTIR_URL`. O agente não inicia se faltar uma variável obrigatória |
| `agente/ia.py` → `criar_modelo` | Troca de provedor de LLM |

## Monitoramento

`PALANTIR_URL` recebe um `POST` por hora, só depois de um ciclo bem-sucedido. Se o Palantir estiver fora, o agente registra um aviso e continua.

## Testes

```bash
uv run pytest
```
