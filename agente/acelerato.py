from dataclasses import dataclass

from data import arq_api_acelerato as api


@dataclass(frozen=True)
class Chamado:
    ticket_key: int
    titulo: str


@dataclass(frozen=True)
class Comentario:
    key: int
    usuario_key: int | None
    nome: str
    texto: str


@dataclass(frozen=True)
class StatusChamado:
    deletado: bool
    concluido: bool = False
    da_ia: bool = False


class Acelerato:
    def __init__(self, usuario_key_ia: int):
        self.usuario_key_ia = usuario_key_ia

    def listar_pendentes(self) -> list[Chamado]:
        return [Chamado(c['ticketKey'], c['titulo']) for c in api.get_chamados_for_API()]

    def contexto(self, ticket_key: int) -> dict:
        return api.get_arquivo_chamado_comentario(ticket_key)

    def comentarios(self, ticket_key: int) -> list[Comentario]:
        return [
            Comentario(c['comentarioKey'], c['usuarioKey'], c['nome'], c['texto'])
            for c in api.get_comentarios_raw(ticket_key)
        ]

    def comentarios_de_humanos(self, comentarios: list[Comentario]) -> list[Comentario]:
        return [c for c in comentarios if c.usuario_key != self.usuario_key_ia]

    def status(self, ticket_key: int) -> StatusChamado:
        status = api.verificar_status_chamado(ticket_key)
        return StatusChamado(
            deletado=status['deletado'],
            concluido=status.get('concluido', False),
            da_ia=status.get('is_agente_ia', False),
        )
