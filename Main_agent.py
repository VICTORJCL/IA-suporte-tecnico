import sys
import os
from pathlib import Path

def ensure_venv():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    script_dir = Path(__file__).parent.absolute()
    venv_python = script_dir / ".venv" / "Scripts" / "python.exe"
    
    # Compara os paths resolvidos (ignora diferença de / vs \ e maiúsculas/minúsculas)
    executavel_atual = Path(sys.executable).resolve()
    executavel_venv  = venv_python.resolve()

    # Se já está rodando com o Python do venv, não faz nada
    if executavel_atual == executavel_venv:
        return

    # Se o venv existe, reinicia com o Python correto
    if venv_python.exists():
        import subprocess
        subprocess.run([str(venv_python), __file__])
        sys.exit()
ensure_venv()

from time import sleep
from agno.agent import Agent
from agno.tools.tavily import TavilyTools
from agno.models.openai import OpenAIChat
from agno.os import AgentOS
import subprocess
from data.tools import *
from agno.tools.reasoning import ReasoningTools
from instructions.Role_auto_agent import role_auto_agent
from instructions.instructions_auto_agent import instructions_auto_agent
from datetime import datetime
from agno.db.sqlite import SqliteDb
from dotenv import dotenv_values, load_dotenv
from data.arq_api_acelerato import get_arquivo_chamado_comentario, get_comentarios_raw, verificar_status_chamado
# from data.arq_api_acelerato import *

class AutoIA ():
    def __init__(self) -> None:
        self.local_keys()
        self.data_bank()
        self.config_agent()

    def local_keys(self):
            
        load_dotenv()
        #  Jupyter
        config = dotenv_values(".env")

        # Define manualmente as variáveis de ambiente
        for key, value in config.items():
            os.environ[key] = value
        API_KEY = os.getenv('OPENAI_API_KEY')

    def data_bank(self ):
        if not 'DB_SQLITE' in os.listdir():
            os.makedirs('DB_SQLITE')

        #  desabilitado
        # DB_FILE = "DB_SQLITE/agent_storage.db"
        # self.sqlite_db = SqliteDb(db_file=DB_FILE)

        # memory_manager = MemoryManager(
        #     memory_capture_instructions="""\
        #                     * Collect User's name,
        #                     * Collect the ticketKey when using responder_chamado_acelerato_tool
        #                 """,
        #     model=OpenAIChat(id="gpt-4.1-mini"),
        # )

    def config_agent(self):
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        self.agent = Agent(
            name="Agente do ACELERATO",
            model=OpenAIChat(id="gpt-4.1-2025-04-14"),
            db=SqliteDb(db_file="DB_SQLITE/agents.db"), 
            learning=True, 
            # model=OpenAIChat(id="gpt-4.1-mini"),
            tools=[
                TavilyTools(),
                ReasoningTools(add_instructions=True),
                # ferramenta_de_Cargas,
                ferramenta_de_Cargas_Sem_parar,
                # get_chamados_for_API_TOOLS,
                responder_chamado_acelerato_tool,
                voucher_tools,
                derruba_pack, 
                ferramenta_altera_senha_bluesoft,
                book_relatorio,
                import_book_zanthus,
                # Voucher_tools_tool,
                # criar_chamado_acelerato_tool,        
                # concluir_chamado_sync,          
                ],
                # db=self.sqlite_db,
                # memory_manager=memory_manager,
                add_history_to_context=True,
                # enable_agentic_memory=False,
                # add_history_to_context=False,
                num_history_runs=6,
                debug_mode=True,
                role=role_auto_agent,
                instructions=instructions_auto_agent,)
    
    def agent_OS(self):
        agent_os = AgentOS(
            os_id="Agente_Suporte_Acelerato",
            description="Esse é um agente especializado em suporte  técnico do Acelerato.",
            agents=[self.agent],
            # interfaces=[Whatsapp(agent=agent)], 
        )
        app = agent_os.get_app()
        agent_os.serve(app="Auto_agent melhoriaP2:app", reload=True)


    
    # palavras_chave = ['carga','voucher','cargas', 'vouchers']

    def main_run(self):
        """
        Loop principal:
        - A cada 120s: detecta chamados novos (pela palavra-chave)
        - Chamados novos → processa com o agent e entra em monitoramento
        - Monitoramento persistente (chamados_persistentes):
            * Dura até 1h a partir do primeiro atendimento
            * Verifica novos comentários humanos a cada 2min
            * Envia novos comentários ao agent para resposta em modo chat
            * Encerra se chamado for concluído ou expirar 1h
        """
        print('IA iniciada')
        PALAVRAS_CHAVE = ['carga','voucher','cargas', 'vouchers', 'derrubar', 'derubar', 'derrube', 'senha', 'inativar', 'atualização csv ebooks', 'atualização ebook', 'atualizações ebooks', 'atualização ebooks',  'atualização ebook']
        # PALAVRAS_CHAVE = ['aly']
        USUARIO_KEY_IA = 822               # usuarioKey do agente IA no Acelerato
        TEMPO_MONITORAMENTO = 60 * 150      # 1 hora em segundos
        INTERVALO_MONITORAMENTO = 2 * 60   # 2 minutos em segundos
        INTERVALO_LOOP = 2 * 60            # 2 minutos em segundos

        # set com ticketKeys já enviados para o agent na primeira vez
        chamados_processados: set = set()

        # dict {ticketKey: {'inicio': datetime, 'comentarios_vistos': set, 'ultimo_check': datetime}}
        chamados_persistentes: dict = {}

        ultimo_check_persistentes = datetime.now()

        while True:
            agora = datetime.now()

            # ─── Verificação de PAUSA ────────────────────────────────────
            #  pausa enquanto tiver um chamado escrito __pause__ no título, até ele ser concluído
            try:
                chamados = get_chamados_for_API_TOOLS()
                if any('__pause__' in c['titulo'].lower() for c in chamados):
                    print(f"[{agora}] ⏸️  IA PAUSADA (chamado __pause__ ativo). Aguardando...")
                    sleep(INTERVALO_LOOP)
                    continue
            except Exception as e:
                print(f"FALHA DE ACESSO A API DO ACELETARO")
                print(f"[ERRO check pausa] {e}")
                sleep(INTERVALO_LOOP)
                continue

            # ─────────────────────────────────────────────────────────────
            # 1. Detectar chamados NOVOS (loop principal a cada 120s)
            # ─────────────────────────────────────────────────────────────
            try:
                chamados_novos = [
                    x for x in chamados
                    if x['ticketKey'] not in chamados_processados
                    and any(p in x['titulo'].lower() for p in PALAVRAS_CHAVE)
                ]

                if chamados_novos:
                    print(f"\n[{agora}] {len(chamados_novos)} chamado(s) novo(s) detectado(s).")
                    for chamado in chamados_novos:
                        ticket_key = chamado['ticketKey']
                        chamados_processados.add(ticket_key)

                        # Pega contexto completo (descricao + comentarios + anexos)
                        context = get_arquivo_chamado_comentario(ticket_key)
                        print(f"  → Enviando chamado #{ticket_key} ao agent...")
                        self.agent.print_response(
                            f'Com total autonomia, faça o chamado. '
                            f'Aqui estão todas as informações: {context}'
                        )

                        # Registra para monitoramento persistente
                        # Captura todos os comentários atuais como "já vistos"
                        comentarios_atuais = get_comentarios_raw(ticket_key)
                        comentarios_vistos = {c['comentarioKey'] for c in comentarios_atuais}

                        chamados_persistentes[ticket_key] = {
                            'inicio': agora,
                            'comentarios_vistos': comentarios_vistos,
                            'ultimo_check': agora,
                        }
                        print(f"  ✓ Chamado #{ticket_key} em monitoramento por 1h.")
                else:
                    print(f"[{agora}] Nenhum chamado novo.")

            except Exception as e:
                print(f"[ERRO loop principal] {e}")

            # ─────────────────────────────────────────────────────────────
            # 2. Monitoramento PERSISTENTE (a cada 2 min)
            # ─────────────────────────────────────────────────────────────
            agora = datetime.now()
            if chamados_persistentes and (agora - ultimo_check_persistentes).total_seconds() >= INTERVALO_MONITORAMENTO:
                ultimo_check_persistentes = agora
                print(f"\n[{agora}] Verificando {len(chamados_persistentes)} chamado(s) em monitoramento...")

                expirados = []
                for ticket_key, info in chamados_persistentes.items():
                    try:
                        tempo_decorrido = (agora - info['inicio']).total_seconds()

                        # Verificar expiração (1h)
                        if tempo_decorrido >= TEMPO_MONITORAMENTO:
                            print(f"  ⏰ Chamado #{ticket_key} expirou monitoramento (1h).")
                            expirados.append(ticket_key)
                            continue

                        # Verificar status atual do chamado
                        status_info = verificar_status_chamado(ticket_key)
                        
                        if status_info['deletado']:
                            print(f"  🗑️ Chamado #{ticket_key} excluído/na lixeira. Removendo do monitoramento.")
                            expirados.append(ticket_key)
                            continue
                            
                        if status_info['concluido']:
                            print(f"  ✅ Chamado #{ticket_key} concluído. Removendo do monitoramento.")
                            expirados.append(ticket_key)
                            continue
                            
                        if not status_info['is_agente_ia']:
                            print(f"  🛑 Chamado #{ticket_key} não está atribuído à IA ou foi retirado dela. Removendo do monitoramento.")
                            expirados.append(ticket_key)
                            continue

                        # Buscar comentários atuais
                        comentarios_atuais = get_comentarios_raw(ticket_key)

                        # Filtrar apenas comentários NOVOS e que NÃO sejam da IA
                        novos_de_humanos = [
                            c for c in comentarios_atuais
                            if c['comentarioKey'] not in info['comentarios_vistos']
                            and c['usuarioKey'] != USUARIO_KEY_IA
                        ]

                        # Atualizar set de comentários vistos (incluindo novos da IA também)
                        for c in comentarios_atuais:
                            info['comentarios_vistos'].add(c['comentarioKey'])

                        if novos_de_humanos:
                            print(f"  💬 Chamado #{ticket_key}: {len(novos_de_humanos)} novo(s) comentário(s) humano(s).")
                            # Formata os novos comentários destacados
                            msgs = '\n'.join(
                                f"- {c['nome']}: {c['texto']}"
                                for c in novos_de_humanos
                            )
                            # Busca contexto completo do chamado (título, descrição, todos comentários, anexos)
                            context_completo = get_arquivo_chamado_comentario(ticket_key)
                            self.agent.print_response(
                                f'Chamado #{ticket_key} recebeu novos comentários do solicitante. '
                                f'Responda como continuação do atendimento usando responder_chamado_acelerato_tool.\n\n'
                                f'NOVOS COMENTÁRIOS (responda a estes):\n{msgs}\n\n'
                                f'CONTEXTO COMPLETO DO CHAMADO (para referência):\n{context_completo}'
                            )
                        else:
                            print(f"  → Chamado #{ticket_key}: sem novos comentários humanos.")

                    except Exception as e:
                        print(f"  [ERRO monitoramento #{ticket_key}] {e}")

                # Remove expirados/concluídos
                for key in expirados:
                    chamados_persistentes.pop(key, None)

            sleep(INTERVALO_LOOP)

if __name__ == "__main__":
    # agent_os.serve(app="Agent:app", reload=True)  # Para interface Agno
    # agent.run('quais os chamados ativos?')   # para somente rodar
    # agent.print_response('quais os chamados ativos?')   # para  printar a resposta no terminal
    # agent.cli_app('quais os chamados?')  # roda em loop sempre esperando a resposta do usuário pelo terminal (interativo)

    inicio = AutoIA()
    # Inicia diretamente no terminal interativo em vez de usar main_run() ou serve()
    print("Iniciando o modo interativo no terminal...")
    # inicio.agent.cli_app()
    inicio.main_run()

#  atualizações:
# pip install --upgrade agno




#  melhoria para o agente para não responder o chamado se for fora de escopo
# verificar se ele armazena informações na base de conhecimento