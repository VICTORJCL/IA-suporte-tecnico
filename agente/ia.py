import importlib
import logging
from typing import Any, Callable

from agno.agent import Agent
from agno.exceptions import ModelProviderError, ModelRateLimitError
from agno.models.base import Model
from agno.models.deepseek import DeepSeek
from agno.models.fallback import FallbackConfig
from agno.models.openai import OpenAIChat
from agno.models.response import ModelResponse
from agno.run.base import RunStatus
from agno.tools.reasoning import ReasoningTools

import instructions.instructions_auto_agent as prompt_operacional
from agente.acelerato import Acelerato, Comentario
from agente.config import (
    AVISO_DE_NOVA_TENTATIVA,
    DEBUG,
    MODELO_ID,
    MODELO_RESERVA_ID,
    NOME_DO_AGENTE,
    TEMPO_LIMITE_DA_IA_EM_SEGUNDOS,
)
from data.tools import (
    book_relatorio,
    derruba_pack,
    ferramenta_altera_senha_bluesoft,
    ferramenta_de_Cargas_Sem_parar,
    import_book_zanthus,
    responder_chamado_acelerato_tool,
    voucher_tools,
)
from instructions.Role_auto_agent import role_auto_agent

log = logging.getLogger(__name__)

FERRAMENTAS = [
    ReasoningTools(add_instructions=True),
    ferramenta_de_Cargas_Sem_parar,
    responder_chamado_acelerato_tool,
    voucher_tools,
    derruba_pack,
    ferramenta_altera_senha_bluesoft,
    book_relatorio,
    import_book_zanthus,
]

INSTRUCAO_DE_FALHA = (
    "Quando alguma ferramenta falhar, informe o erro no chamado e termine a resposta com: "
    f'"{AVISO_DE_NOVA_TENTATIVA}"'
)


class DeepSeekComReserva(DeepSeek):
    # O Agno não aciona a reserva em erros 4xx como o 402 (sem crédito) da DeepSeek; só em 429 e 5xx.
    def invoke(self, *args: Any, **kwargs: Any) -> ModelResponse:
        try:
            return super().invoke(*args, **kwargs)
        except ModelProviderError as erro:
            raise ModelRateLimitError(erro.message, erro.status_code, erro.model_name, erro.model_id) from erro


def criar_modelo(modelo_id: str = MODELO_ID) -> Model:
    # Sem thinking: com ferramentas, a API exige o reasoning_content de volta, e mensagens da reserva não o têm.
    return DeepSeekComReserva(
        id=modelo_id,
        use_thinking=False,
        timeout=TEMPO_LIMITE_DA_IA_EM_SEGUNDOS,
        max_retries=1,
    )


def criar_modelo_reserva(modelo_id: str = MODELO_RESERVA_ID) -> Model:
    return OpenAIChat(id=modelo_id, timeout=TEMPO_LIMITE_DA_IA_EM_SEGUNDOS)


def registrar_uso_da_reserva(modelo_principal: str, modelo_reserva: str, erro: Exception) -> None:
    log.warning("%s falhou (%s); atendido por %s", modelo_principal, erro, modelo_reserva)


def criar_agente(modelo: Model, reserva: Model) -> Agent:
    return Agent(
        name=NOME_DO_AGENTE,
        model=modelo,
        fallback_config=FallbackConfig(on_error=[reserva], callback=registrar_uso_da_reserva),
        tools=FERRAMENTAS,
        tool_hooks=[avisar_falha],
        role=role_auto_agent,
        instructions=instrucoes,
        debug_mode=DEBUG,
    )


def instrucoes() -> list[str]:
    # O prompt é uma f-string avaliada no import; recarregar mantém a "data de hoje" certa num processo que roda por dias.
    importlib.reload(prompt_operacional)
    return [prompt_operacional.instructions_auto_agent, INSTRUCAO_DE_FALHA]


def falhou(resultado: Any) -> bool:
    if isinstance(resultado, str):
        return resultado.strip().upper().startswith("ERRO")
    if isinstance(resultado, dict):
        return resultado.get("sucesso") is False
    return False


def avisar_falha(function_name: str, function_call: Callable, arguments: dict) -> Any:
    try:
        resultado = function_call(**arguments)
    except Exception as erro:
        log.exception("Ferramenta %s falhou", function_name)
        return f"ERRO em {function_name}: {erro}\n{AVISO_DE_NOVA_TENTATIVA}"

    if not falhou(resultado):
        return resultado
    if isinstance(resultado, dict):
        return {**resultado, "aviso": AVISO_DE_NOVA_TENTATIVA}
    return f"{resultado}\n{AVISO_DE_NOVA_TENTATIVA}"


class Atendente:
    def __init__(self, agent: Agent, acelerato: Acelerato):
        self.agent = agent
        self.acelerato = acelerato

    def atender(self, ticket_key: int) -> None:
        contexto = self.acelerato.contexto(ticket_key)
        self._executar(
            ticket_key,
            f'Com total autonomia, faça o chamado. '
            f'Aqui estão todas as informações: {contexto}',
        )

    def responder(self, ticket_key: int, novos: list[Comentario]) -> None:
        mensagens = '\n'.join(f"- {c.nome}: {c.texto}" for c in novos)
        contexto = self.acelerato.contexto(ticket_key)
        self._executar(
            ticket_key,
            f'Chamado #{ticket_key} recebeu novos comentários do solicitante. '
            f'Responda como continuação do atendimento usando responder_chamado_acelerato_tool.\n\n'
            f'NOVOS COMENTÁRIOS (responda a estes):\n{mensagens}\n\n'
            f'CONTEXTO COMPLETO DO CHAMADO (para referência):\n{contexto}',
        )

    def _executar(self, ticket_key: int, mensagem: str) -> None:
        log.info("Enviando chamado #%s ao agente", ticket_key)
        resposta = self.agent.run(mensagem)
        # O Agno não lança exceção quando o principal e a reserva falham: devolve status de erro.
        if resposta.status == RunStatus.error:
            log.error("Chamado #%s não foi atendido: %s", ticket_key, resposta.content)
            return
        log.info("Chamado #%s: %s", ticket_key, resposta.content)
