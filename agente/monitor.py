import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from time import sleep
from typing import Callable

from agente.acelerato import Acelerato, Chamado
from agente.config import (
    DIAS_DE_ACOMPANHAMENTO,
    INTERVALO_DE_ACOMPANHAMENTO_EM_SEGUNDOS,
    INTERVALO_DO_LOOP_EM_SEGUNDOS,
    MARCADOR_DE_PAUSA,
    PALAVRAS_CHAVE,
)
from agente.ia import Atendente

log = logging.getLogger(__name__)


@dataclass
class Acompanhamento:
    inicio: datetime
    comentarios_vistos: set[int] = field(default_factory=set)


class MonitorDeChamados:
    def __init__(
        self,
        acelerato: Acelerato,
        atendente: Atendente,
        relogio: Callable[[], datetime] = datetime.now,
        palavras_chave: list[str] = PALAVRAS_CHAVE,
        duracao: timedelta = timedelta(days=DIAS_DE_ACOMPANHAMENTO),
        intervalo_de_acompanhamento: timedelta = timedelta(seconds=INTERVALO_DE_ACOMPANHAMENTO_EM_SEGUNDOS),
    ):
        self.acelerato = acelerato
        self.atendente = atendente
        self.relogio = relogio
        self.palavras_chave = palavras_chave
        self.duracao = duracao
        self.intervalo_de_acompanhamento = intervalo_de_acompanhamento
        self.ultimo_acompanhamento = relogio()
        self.atendidos: set[int] = set()
        self.ativos: dict[int, Acompanhamento] = {}

    def rodar(
        self,
        batimento: Callable[[], None] = lambda: None,
        intervalo_em_segundos: int = INTERVALO_DO_LOOP_EM_SEGUNDOS,
    ) -> None:
        log.info("IA iniciada")
        while True:
            try:
                self.ciclo()
                batimento()
            except Exception:
                log.exception("Falha de acesso à API do Acelerato")
            sleep(intervalo_em_segundos)

    def ciclo(self) -> None:
        chamados = self.acelerato.listar_pendentes()
        if any(MARCADOR_DE_PAUSA in c.titulo.lower() for c in chamados):
            log.info("IA pausada (chamado %s ativo)", MARCADOR_DE_PAUSA)
            return

        self.atender_novos(chamados)

        if self.relogio() - self.ultimo_acompanhamento >= self.intervalo_de_acompanhamento:
            self.ultimo_acompanhamento = self.relogio()
            self.acompanhar_ativos()

    def atender_novos(self, chamados: list[Chamado]) -> None:
        novos = [c for c in chamados if self._e_do_escopo(c) and c.ticket_key not in self.atendidos]
        if not novos:
            log.info("Nenhum chamado novo")
        for chamado in novos:
            try:
                self._atender(chamado.ticket_key)
            except Exception:
                log.exception("Erro ao atender chamado #%s", chamado.ticket_key)

    def acompanhar_ativos(self) -> None:
        log.info("Acompanhando %s chamado(s)", len(self.ativos))
        for ticket_key, acompanhamento in list(self.ativos.items()):
            try:
                self._acompanhar(ticket_key, acompanhamento)
            except Exception:
                log.exception("Erro no acompanhamento do chamado #%s", ticket_key)

    def _e_do_escopo(self, chamado: Chamado) -> bool:
        titulo = chamado.titulo.lower()
        return any(palavra in titulo for palavra in self.palavras_chave)

    def _atender(self, ticket_key: int) -> None:
        # Registrado antes de atender: se o agente falhar no meio, o chamado não é reatendido a cada ciclo.
        vistos = {c.key for c in self.acelerato.comentarios(ticket_key)}
        self.atendidos.add(ticket_key)
        self.ativos[ticket_key] = Acompanhamento(self.relogio(), vistos)
        self.atendente.atender(ticket_key)
        log.info("Chamado #%s em acompanhamento por %s", ticket_key, self.duracao)

    def _acompanhar(self, ticket_key: int, acompanhamento: Acompanhamento) -> None:
        motivo = self._motivo_para_encerrar(ticket_key, acompanhamento)
        if motivo:
            log.info("Chamado #%s: %s. Encerrando acompanhamento", ticket_key, motivo)
            del self.ativos[ticket_key]
            return

        comentarios = self.acelerato.comentarios(ticket_key)
        novos = [c for c in comentarios if c.key not in acompanhamento.comentarios_vistos]
        acompanhamento.comentarios_vistos |= {c.key for c in comentarios}

        novos_de_humanos = self.acelerato.comentarios_de_humanos(novos)
        if novos_de_humanos:
            log.info("Chamado #%s: %s comentário(s) novo(s)", ticket_key, len(novos_de_humanos))
            self.atendente.responder(ticket_key, novos_de_humanos)

    def _motivo_para_encerrar(self, ticket_key: int, acompanhamento: Acompanhamento) -> str | None:
        if self.relogio() - acompanhamento.inicio >= self.duracao:
            return "expirou"
        status = self.acelerato.status(ticket_key)
        if status.deletado:
            return "excluído"
        if status.concluido:
            return "concluído"
        if not status.da_ia:
            return "retirado da IA"
        return None
