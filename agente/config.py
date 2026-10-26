import os
from pathlib import Path

from dotenv import load_dotenv

PALAVRAS_CHAVE = [
    'carga', 'voucher', 'cargas', 'vouchers',
    'derrubar', 'derubar', 'derrube', 'senha',
    'inativar', 'atualização csv ebooks',
    'atualização ebook', 'atualizações ebooks',
    'atualização ebooks',
]
MARCADOR_DE_PAUSA = '__pause__'
USUARIO_KEY_IA = 822

DIAS_DE_ACOMPANHAMENTO = 3
INTERVALO_DO_LOOP_EM_SEGUNDOS = 2 * 60
INTERVALO_DE_ACOMPANHAMENTO_EM_SEGUNDOS = 2 * 60

PALANTIR_URL = "http://localhost:8787/ping/ia-ti"
INTERVALO_DO_PALANTIR_EM_SEGUNDOS = 60 * 60

AVISO_DE_NOVA_TENTATIVA = "Se quiser que eu tente novamente, é só adicionar um comentário abaixo."

NOME_DO_AGENTE = "Agente do ACELERATO"
MODELO_ID = "gpt-4.1-2025-04-14"
DEBUG = True

VARIAVEIS_OBRIGATORIAS = [
    "OPENAI_API_KEY", "EMAIL", "TOKEN",
    "ACELERATO_URL", "ZANTHUS_URL", "BLUESOFT_URL", "PAINEL_URL",
]

RAIZ = Path(__file__).resolve().parent.parent


def carregar_ambiente(arquivo: Path = RAIZ / ".env") -> None:
    load_dotenv(arquivo)
    # No Linux o env diferencia maiúsculas: derruba_pack lê 'log_zeus' e book_zanthus lê 'LOG_ZEUS'.
    for chave, valor in list(os.environ.items()):
        os.environ.setdefault(chave.upper(), valor)
        os.environ.setdefault(chave.lower(), valor)

    faltando = [nome for nome in VARIAVEIS_OBRIGATORIAS if not os.getenv(nome)]
    if faltando:
        raise SystemExit(f"Variáveis ausentes no .env: {', '.join(faltando)}. Veja .env.example.")
