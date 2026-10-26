from playwright.sync_api import sync_playwright
import os
import json
import inspect
from pathlib import Path
from dotenv import load_dotenv, dotenv_values
import schedule
import threading
from time import sleep
from datetime import datetime
from data.carga_lock import carga_exclusiva
from data.sistemas import ZANTHUS_URL

# ========================================================================
# CONFIGURAÇÃO DE DIRETÓRIOS E AMBIENTE
# ========================================================================
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / '.env'
PENDING_SCHEDULES_FILE = BASE_DIR / 'data' / 'agendamentos_pendentes.json'

os.chdir(str(BASE_DIR))
load_dotenv(dotenv_path=ENV_PATH)
for key, value in dotenv_values(ENV_PATH).items():
    if value is not None:
        os.environ[key] = value

cod_erro = []

# ========================================================================
# PERSISTÊNCIA DE AGENDAMENTOS
# ========================================================================
def _carregar_agendamentos_pendentes():
    if not PENDING_SCHEDULES_FILE.exists():
        return []
    try:
        with open(PENDING_SCHEDULES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[Agendamentos] Erro ao carregar agendamentos pendentes: {e}")
        return []

def _salvar_agendamento_pendente(codigo_pack, numero_chamado, horario="21:00"):
    try:
        agendamentos = _carregar_agendamentos_pendentes()
        novo = {
            "codigo_pack": codigo_pack,
            "numero_chamado": numero_chamado,
            "horario": horario,
            "data": datetime.now().strftime("%Y-%m-%d")
        }
        agendamentos.append(novo)
        with open(PENDING_SCHEDULES_FILE, 'w', encoding='utf-8') as f:
            json.dump(agendamentos, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Agendamentos] Erro ao salvar agendamento pendente: {e}")

def _remover_agendamento_pendente(codigo_pack, numero_chamado):
    try:
        agendamentos = _carregar_agendamentos_pendentes()
        filtrados = [
            a for a in agendamentos
            if not (a.get("codigo_pack") == codigo_pack and a.get("numero_chamado") == numero_chamado)
        ]
        with open(PENDING_SCHEDULES_FILE, 'w', encoding='utf-8') as f:
            json.dump(filtrados, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Agendamentos] Erro ao remover agendamento pendente: {e}")

# ========================================================================
# CLASSES DE AUTOMAÇÃO (ZANTHUS / PROMOÇÕES / CARGAS)
# ========================================================================

class XpathClass:
    def __init__(self) -> None:
        self.link = f'{ZANTHUS_URL}/manager/cad_promocao.php5?id_menu=30201'
        self.input_log_id = '//input[@id="USUARIO"]'
        self.input_log_senha = '//input[@id="SENHA"]'
        self.btn_log_entrar = '//input[@type="submit" and @value=" Entrar "]'
        self.close_notifications = '//li[@class="dropdown notifications-menu open"]'
        self.filtrar_id = '//button[@id="btn_Search"]'
        self.input_codigo_promocao = '//input[@id="FLT_CODPROMOCAO"]'
        self.btn_aplicar_filtro = '//input[@id="EXEC_FILTRO"]'
        self.ativar_desativar_promocao = '//button[@id="novapromocao_ativar_desativar"]'
        self.type_mensage = '//div[@class="sweet-alert showSweetAlert visible"]//div[@id="alert_message_internal"]'
        self.confirm_btn = '//div[@class="sa-confirm-button-container"]//button[@class="confirm"]'

    @property
    def log_zeus(self):
        return os.getenv('log_zeus')

    @property
    def senha_zeus(self):
        return os.getenv('senha_zeus')

    def close_notifications_if_open(self, page):
        if not page:
            return
        try:
            loc = page.locator(self.close_notifications)
            if loc.is_visible(timeout=1000):
                loc.click()
        except Exception:
            pass


class CargasP(XpathClass):
    def __init__(self, conjunto_lojas="lojas Minipreço", lojas_especificas=None) -> None:
        super().__init__()
        self.executar_cargas_playwright(conjunto_lojas=conjunto_lojas, lojas_especificas=lojas_especificas)

    def loguin_function(self, page):
        page.goto(self.link)
        page.wait_for_timeout(1000)
        
        # Preenche login se formulário estiver presente
        if page.locator(self.input_log_id).count() > 0:
            page.fill(self.input_log_id, self.log_zeus or '')
            page.fill(self.input_log_senha, self.senha_zeus or '')
            page.click(self.btn_log_entrar)
            page.wait_for_timeout(3000)
            page.goto(self.link)
            page.wait_for_timeout(1500)
            
        self.close_notifications_if_open(page)

    @carga_exclusiva
    def executar_cargas_playwright(self, conjunto_lojas="lojas Minipreço", lojas_especificas=None):
        opcoes_lojas = {
            "Lojas PR MiniPreço": ["01","02","04","06","07","08","10","11","12","14","19","20"],
            "Lojas PR Salvados": ["01","02","04","06","08","09","11","14","17","18","19"],
            "Lojas SC Salvados": ["201","202","208"],
            "Salvados PR SC" : ["01","02","04","06","08","09","11","14","17","18","19","201","202","208"],
            "Lojas Espírito Santo MiniPreço": ["301","303","304","305","307","308"],
            "lojas Minipreço": ["01","02","04","06","07","08","10","11","12","14","19","20","301","303","304","305","307","308"],
            "Todas as lojas": ["01","02","04","06","07","08","09","10","11","12","14","17","18","19","20","201","202","208","301","303","304","305","307","308"]
        }
        
        selecao_lojas = []
        if conjunto_lojas and conjunto_lojas in opcoes_lojas:
            selecao_lojas.extend(opcoes_lojas[conjunto_lojas])
            opcao_selecionada = conjunto_lojas
        else:
            opcao_selecionada = "Personalizada"
        
        if lojas_especificas:
            lojas_especificas_list = lojas_especificas if isinstance(lojas_especificas, list) else [lojas_especificas]
            selecao_lojas.extend(lojas_especificas_list)
            opcao_selecionada += " + Específicas"
        
        selecao_lojas = sorted(list(set(selecao_lojas)))
        if not selecao_lojas:
            print("ERRO: Nenhuma loja selecionada para carga.")
            return

        all_lojas_unicas = {
            '01': ['1- MINIPRECO SANTA FELICIDADE', 'LJ 01 - JUMBO SANTA FELICIDADE'],
            '02': ['2- MINIPRECO TORRES', 'LJ 02 - JUMBO TORRES'],
            '04': ['4- MINIPRECO PINHAIS', 'LJ 04 - JUMBO PINHAIS'],
            '06': ['6- MINIPRECO PARANAGUA', 'LJ 06 - JUMBO PARANAGUA'],
            '07': ['7- MINIPRECO FANNY', 'LJ 07 - JUMBO FANNY'],
            '08': ['8- MINIPRECO FAZENDA RIO GRANDE', 'LJ 08 - JUMBO FAZ. RIO GRANDE'],
            '09': ['9- RDS SITIO CERCADO', 'LJ 09 - JUMBO SALVADOS SITIO CERCADO'],
            '10': ['10- MINIPRECO XAXIM', 'LJ 10 - JUMBO XAXIM'],
            '11': ['11- MINIPRECO FAZENDINHA', 'LJ 11 - JUMBO FAZENDINHA'],
            '12': ['12- MINIPRECO EXPRESS BOULEVARD', 'LJ 12 - JUMBO BOULEVARD'],
            '14': ['14- MINIPRECO COLOMBO', 'LJ 14 - JUMBO COLOMBO'],
            '17': ['17- RDS XAXIM', 'LJ 17 - JUMBO SALVADOS XAXIM'],
            '18': ['18- RDS FANNY', 'LJ 18 - JUMBO SALVADOS FANNY'],
            '19': ['19- MINIPRECO ARAUCARIA', 'LJ 19 - JUMBO ARAUCARIA'],
            '20': ['20- MINIPRECO BACACHERI', 'LJ 20 - JUMBO BACACHERI'],
            '201': ['201- RDS BALNEARIO CAMBORIU','LJ 201 - JUMBO SALVADOS BAL CAMBORIU'],
            '202': ['202- RDS ITAJAI', 'LJ 202 - JUMBO SALVADOS ITAJAÍ'],
            '207': ['207- RDS PRAIA BRAVA', 'LJ 207 -JUMBO SALVADOS PRAIA B'],
            '208': ['208- RDS JOINVILLE', 'LJ 208 - JUMBO SALVADOS JOINVILLE'],
            '301': ['301- MINIPRECO VILA VELHA', 'LJ 301 - JUMBO VILA VELHA'],
            '303': ['303- MINIPRECO SERRA', 'LJ 303 - JUMBO SERRA'],
            '304': ['304- MINIPRECO VITORIA', 'LJ 304 - JUMBO VITORIA'],
            '305': ['305- MINIPRECO LINHARES', 'LJ 305 - JUMBO LINHARES'],
            '307': ['307- MINIPRECO GLORIA', 'LJ 307 - JUMBO GLORIA'],
            '308': ['308- MINIPRECO DAY BY DAY', 'LJ 308 - JUMBO DAY BY DAY'],
            '602': ['602- DCOR GIFT CRYSTAL', 'LJ 602 - DCOR CRYSTAL'],
            '900': ['900- LOJA TESTE DE SISTEMA', 'LOJA TESTE DE SISTEMA']
        }
        
        print(f"[Cargas Zanthus] Iniciando cargas para: {opcao_selecionada} ({len(selecao_lojas)} lojas)")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_default_timeout(45000)
            
            try:
                self.loguin_function(page)
            except Exception as e:
                print(f"[Cargas Zanthus] Aviso login: {e}")

            url_cargas = f'{ZANTHUS_URL}/manager/adm_cargaDiretaArquivosSemZMS.php5?id_menu=405'
            page.goto(url_cargas)
            try:
                page.locator('//span[@aria-hidden="true"]').click(timeout=1000)
            except Exception:
                pass
            
            page.wait_for_selector("#btn_AddFavoritos", timeout=30000)
            print("[Cargas Zanthus] Login e acesso a tela de cargas confirmados")
            
            def keep_alive():
                try:
                    page.evaluate("""
                    if (!window.__keepAlive) {
                        window.__keepAlive = setInterval(() => {
                            try {
                                fetch(window.location.href, { method: 'GET', cache: 'no-cache', credentials: 'include' });
                            } catch(e) {}
                        }, 60000);
                    }
                    """)
                except Exception:
                    pass

            self.close_notifications_if_open(page)
            
            # Desmarca a loja 1 por padrão se estiver marcada
            try:
                cb_loja1 = page.locator('//input[@id="GERA_1"]')
                if cb_loja1.is_checked():
                    page.locator('//input[@id="GERA_1"]/following-sibling::div[@class="control__indicator"]').click()
            except Exception:
                pass
            
            # Processa cargas Zanthus em lotes de até 6 lojas
            x = 0
            while x < len(selecao_lojas):
                lojas_marcadas = []
                lojas_a_processar = min(6, len(selecao_lojas) - x)
                
                print(f"\n[Cargas Zanthus] Processando grupo de {lojas_a_processar} loja(s)...")
                
                for i in range(lojas_a_processar):
                    loja_cod = selecao_lojas[x + i]
                    loja_id = loja_cod.split("-")[0].lstrip("0")
                    loja_nome = all_lojas_unicas.get(loja_cod, [loja_cod])[0]
                    
                    checkbox_xpath = f'//input[@id="GERA_{loja_id}"]/following-sibling::div[@class="control__indicator"]'
                    try:
                        page.locator(checkbox_xpath).click()
                        lojas_marcadas.append((loja_id, loja_nome))
                        print(f"  [+] Loja {loja_nome} (ID: {loja_id}) selecionada")
                    except Exception as err_sel:
                        print(f"  [-] Falha ao selecionar loja {loja_nome}: {err_sel}")
                    sleep(0.3)
                
                if lojas_marcadas:
                    page.locator('//input[@id="gerarParcial"]').click()
                    print(f"  [OK] Carga parcial disparada para {len(lojas_marcadas)} loja(s)")
                    sleep(8)
                    
                    # Monitora progresso de cada loja com timeout de segurança
                    for loja_id, loja_nome in lojas_marcadas:
                        tentativas = 0
                        tempo = tempo2 = ""
                        while tentativas < 25:
                            sleep(4)
                            keep_alive()
                            try:
                                tempo = page.locator(f'//td[@id="R_{loja_id}_TD_3"]').text_content() or ""
                            except Exception:
                                tempo = ""
                            sleep(2)
                            try:
                                tempo2 = page.locator(f'//td[@id="R_{loja_id}_TD_3"]').text_content() or ""
                            except Exception:
                                tempo2 = ""
                                
                            tentativas += 1
                            if tempo == tempo2 and tempo != "":
                                break
                                
                        print(f"  [OK] Loja {loja_nome} processada (Tempo/Status: {tempo})")
                    
                    # Desmarca lojas processadas
                    for loja_id, loja_nome in lojas_marcadas:
                        try:
                            cb_xpath = f'//input[@id="GERA_{loja_id}"]/following-sibling::div[@class="control__indicator"]'
                            page.locator(cb_xpath).click()
                        except Exception:
                            pass
                        sleep(0.2)
                
                x += lojas_a_processar
                sleep(1)
            
            print("[Cargas Zanthus] Finalizado envio de cargas para todas as lojas selecionadas.")
            browser.close()


class PlaywrightClass(XpathClass):
    def __init__(self):
        super().__init__()
        self.browser = None
        self.page = None

    def start_browser(self, p):
        self.browser = p.chromium.launch(headless=True)
        context = self.browser.new_context()
        self.page = context.new_page()
        self.page.set_default_timeout(30000)

    def loguin_function(self):
        page = self.page
        page.goto(self.link)
        page.wait_for_timeout(1000)
        
        # Preenche usuário e senha caso tela de login apareça
        if page.locator(self.input_log_id).count() > 0:
            page.fill(self.input_log_id, self.log_zeus or '')
            page.fill(self.input_log_senha, self.senha_zeus or '')
            page.click(self.btn_log_entrar)
            page.wait_for_timeout(3000)
            page.goto(self.link)
            page.wait_for_timeout(1500)
            
        self.close_notifications_if_open(page)

    def buscar_cod_prom(self, codigo_id):
        page = self.page
        page.locator(self.filtrar_id).click()
        page.wait_for_timeout(1000)
        page.fill(self.input_codigo_promocao, str(codigo_id))
        page.locator(self.btn_aplicar_filtro).click()
        page.wait_for_timeout(3000)
        self.close_notifications_if_open(page)

    def inativar_promocao(self, cod):
        """
        Inativa o pack promocional inspecionando o checkbox da coluna 'Ativo'.
        Evita reativação acidental se já estiver inativo.
        """
        page = self.page
        page.wait_for_timeout(1000)
        
        # Inspeciona tabela para encontrar a linha do pack e verificar se está ativo
        row_info = page.evaluate("""(codBuscado) => {
            const rows = document.querySelectorAll('table tbody tr, table tr');
            for (let r of rows) {
                const cells = r.querySelectorAll('td');
                if (cells.length >= 5) {
                    const code = cells[0].textContent.trim();
                    if (code === String(codBuscado)) {
                        const cb = cells[4].querySelector('input[type="checkbox"], input[type="CHECKBOX"]');
                        const btn = r.querySelector('#novapromocao_ativar_desativar');
                        return {
                            found: true,
                            checked: cb ? cb.checked : false,
                            hasButton: !!btn
                        };
                    }
                }
            }
            return { found: false };
        }""", str(cod))
        
        if not row_info.get('found'):
            print(f"[Derruba Pack] Pack {cod} nao encontrado na listagem.")
            cod_erro.append(f"Nao foi encontrado o pack {cod}")
            return
            
        if not row_info.get('checked'):
            print(f"[Derruba Pack] [OK] Pack {cod} ja se encontra desativado (inativo).")
            return
            
        print(f"[Derruba Pack] Pack {cod} esta ativo. Inativando...")
        # Clica no botão Ativar/Desativar da linha
        page.locator(self.ativar_desativar_promocao).click()
        page.wait_for_timeout(2000)
        
        # Fecha modal de confirmação/sucesso se aparecer
        try:
            confirm_btn = page.locator('//div[contains(@class, "sweet-alert")]//button[contains(@class, "confirm")]')
            if confirm_btn.is_visible(timeout=3000):
                confirm_btn.click()
                page.wait_for_timeout(1000)
        except Exception:
            pass
            
        # Re-valida o status do checkbox após inativação
        page.wait_for_timeout(2000)
        checked_after = page.evaluate("""(codBuscado) => {
            const rows = document.querySelectorAll('table tbody tr, table tr');
            for (let r of rows) {
                const cells = r.querySelectorAll('td');
                if (cells.length >= 5) {
                    const code = cells[0].textContent.trim();
                    if (code === String(codBuscado)) {
                        const cb = cells[4].querySelector('input[type="checkbox"], input[type="CHECKBOX"]');
                        return cb ? cb.checked : false;
                    }
                }
            }
            return false;
        }""", str(cod))
        
        if checked_after:
            print(f"[Derruba Pack] [AVISO] Pack {cod} ainda consta como ativo apos clique.")
            cod_erro.append(f"Pack {cod} nao foi inativado com sucesso.")
        else:
            print(f"[Derruba Pack] [OK] Pack {cod} inativado com sucesso!")

    def main_plawrigt(self, codigo_id):
        global cod_erro
        cod_erro = []
        if not isinstance(codigo_id, list):
            codigo_id = [codigo_id]
        codigo_id = [str(x).strip() for x in codigo_id]

        with sync_playwright() as p:
            self.start_browser(p)
            self.loguin_function()
            for cod in codigo_id:
                if not cod:
                    continue
                try:
                    self.buscar_cod_prom(cod)
                    self.inativar_promocao(cod)
                except Exception as e:
                    print(f"[Derruba Pack] Erro ao processar pack {cod}: {e}")
                    cod_erro.append(f"Erro ao processar pack {cod}: {e}")

            self.page.wait_for_timeout(2000)
            self.browser.close()


# ========================================================================
# AGENDAMENTO E EXECUÇÃO
# ========================================================================

def exec_agendar_tarefa(codigo_pack, numero_chamado=None):
    """Executa a tarefa agendada (inativação do pack + envio de cargas + resposta do chamado)."""
    print(f"\n{'='*60}")
    print(f"[Scheduler] Executando tarefa agendada para pack(s) {codigo_pack} (Chamado: #{numero_chamado})")
    print(f"{'='*60}")
    
    try:
        # 1. Inativa o pack
        PlaywrightClass().main_plawrigt(codigo_pack)
        
        # 2. Executa as cargas Zanthus
        try:
            CargasP()
            cargas_ok = True
        except Exception as e_carga:
            print(f"[Scheduler] Aviso ao disparar cargas: {e_carga}")
            cargas_ok = False
            
        _remover_agendamento_pendente(codigo_pack, numero_chamado)
        
        # 3. Responde o chamado no Acelerato informando a conclusão
        if numero_chamado:
            try:
                from data.arq_api_acelerato import responder_chamado_acelerato
                if cod_erro:
                    msg = f"<b>Processo agendado de derrubada de pack concluído com avisos:</b><br>" + "<br>".join(cod_erro)
                else:
                    msg = f"<b>Derrubada agendada finalizada com sucesso!</b><br>O(s) Pack(s) <b>{codigo_pack}</b> foi(foram) inativado(s) na Zanthus"
                    if cargas_ok:
                        msg += " e as cargas para as lojas foram disparadas."
                    else:
                        msg += ", porém ocorreu um aviso no disparo de cargas."
                responder_chamado_acelerato(numero_chamado, msg)
                print(f"[Scheduler] Chamado #{numero_chamado} respondido com sucesso após execução agendada.")
            except Exception as e_resp:
                print(f"[Scheduler] Erro ao responder chamado #{numero_chamado}: {e_resp}")
                
    except Exception as e:
        print(f"[Scheduler] Erro geral na execucao agendada: {e}")
        if numero_chamado:
            try:
                from data.arq_api_acelerato import responder_chamado_acelerato
                responder_chamado_acelerato(numero_chamado, f"Erro ao executar processo agendado de derrubada de pack: {e}")
            except Exception:
                pass


def iniciar_scheduler_thread(codigo_pack, numero_chamado=None, horario="21:00"):
    """Inicia o scheduler em uma thread separada e isolada para o horário especificado"""
    _salvar_agendamento_pendente(codigo_pack, numero_chamado, horario)
    
    def run_scheduler():
        custom_scheduler = schedule.Scheduler()
        
        def job():
            try:
                exec_agendar_tarefa(codigo_pack, numero_chamado)
            finally:
                return schedule.CancelJob
                
        custom_scheduler.every().day.at(horario).do(job)
        print(f"[Scheduler] Agendamento ativo para {horario} - Pack(s): {codigo_pack} (Chamado: #{numero_chamado})")
        
        while custom_scheduler.jobs:
            custom_scheduler.run_pending()
            sleep(30)
            
        print(f"[Scheduler] Thread de agendamento finalizada para pack(s) {codigo_pack}")

    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print(f"[Scheduler] Agendamento registrado (thread iniciada as {datetime.now().strftime('%H:%M:%S')})")


def recuperar_agendamentos_pendentes():
    """Recupera agendamentos persistidos caso a aplicação tenha reiniciado"""
    agendamentos = _carregar_agendamentos_pendentes()
    hoje = datetime.now().strftime("%Y-%m-%d")
    agora_hm = datetime.now().strftime("%H:%M")
    
    for ag in agendamentos:
        cod = ag.get("codigo_pack")
        num = ag.get("numero_chamado")
        horario = ag.get("horario", "21:00")
        data_ag = ag.get("data", hoje)
        
        # Se for para hoje e o horário ainda não passou, agenda
        if data_ag == hoje and horario > agora_hm:
            print(f"[Scheduler Recovery] Recuperando agendamento pendente para {horario} - Pack: {cod} (Chamado: #{num})")
            iniciar_scheduler_thread(cod, num, horario)


# Recupera agendamentos ao carregar o módulo
try:
    recuperar_agendamentos_pendentes()
except Exception as e:
    print(f"[Scheduler Recovery] Erro na recuperacao inicial: {e}")


def derruba_pack_mainfun(codigo_pack, option_pack=1, numero_chamado=None):
    option_pack = int(option_pack)
    try:
        if option_pack == 1:
            PlaywrightClass().main_plawrigt(codigo_pack)
            try:
                CargasP()
            except Exception as e_carga:
                print(f"[Derruba Pack] Aviso ao disparar cargas: {e_carga}")
                cod_erro.append(f"Aviso no envio de cargas: {e_carga}")

            if cod_erro:
                return f"Processo concluido, mas com avisos:\n" + "\n".join(cod_erro)
            return "Pack(s) derrubado(s) com sucesso e carga(s) realizada(s)."
        
        elif option_pack == 2:
            iniciar_scheduler_thread(codigo_pack, numero_chamado=numero_chamado, horario="21:00")
            if cod_erro:
                return f"Agendamento realizado, mas com avisos:\n" + "\n".join(cod_erro)
            return "Pack(s) programado(s) para derrubada/inativação e envio de carga(s) para o final do expediente (21:00)."
        
        else:
            raise ValueError(f"Opcao invalida option_pack={option_pack}. Deve ser 1 (imediato) ou 2 (agendado 21:00).")
            
    except Exception as er:
        raise Exception(f"Erro ao derrubar pack: {er}")


if __name__ == "__main__":
    pass
