import logging
import os
from datetime import timedelta

from agente.acelerato import Acelerato
from agente.config import INTERVALO_DO_PALANTIR_EM_SEGUNDOS, PALANTIR_URL, USUARIO_KEY_IA, carregar_ambiente
from agente.ia import Atendente, criar_agente, criar_modelo
from agente.monitor import MonitorDeChamados
from agente.palantir import Palantir


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    carregar_ambiente()

    acelerato = Acelerato(USUARIO_KEY_IA)
    monitor = MonitorDeChamados(acelerato, Atendente(criar_agente(criar_modelo()), acelerato))
    palantir = Palantir(os.getenv("PALANTIR_URL", PALANTIR_URL), timedelta(seconds=INTERVALO_DO_PALANTIR_EM_SEGUNDOS))
    monitor.rodar(batimento=palantir.pingar_se_for_hora)


if __name__ == "__main__":
    main()
