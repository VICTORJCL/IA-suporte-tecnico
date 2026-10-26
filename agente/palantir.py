import logging
from datetime import datetime, timedelta
from typing import Callable

import requests

log = logging.getLogger(__name__)


class Palantir:
    def __init__(
        self,
        url: str,
        intervalo: timedelta,
        timeout_em_segundos: int = 3,
        relogio: Callable[[], datetime] = datetime.now,
    ):
        self.url = url
        self.intervalo = intervalo
        self.timeout_em_segundos = timeout_em_segundos
        self.relogio = relogio
        self.ultimo_ping: datetime | None = None

    def pingar_se_for_hora(self) -> None:
        agora = self.relogio()
        if self.ultimo_ping and agora - self.ultimo_ping < self.intervalo:
            return
        self.ultimo_ping = agora
        self.pingar()

    def pingar(self) -> None:
        # Falha no monitoramento nunca pode derrubar o agente: só registra e segue.
        try:
            resposta = requests.post(self.url, timeout=self.timeout_em_segundos)
            log.info("Palantir [%s] %s", resposta.status_code, self.url)
        except requests.RequestException as erro:
            log.warning("Palantir indisponível em %s: %s", self.url, erro)
