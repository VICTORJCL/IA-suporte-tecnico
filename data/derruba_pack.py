from playwright.sync_api import sync_playwright
from playwright.sync_api import sync_playwright

import os
from dotenv import load_dotenv,dotenv_values

import schedule
import threading
from time import sleep
from datetime import datetime

#  importações
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.listdir()
load_dotenv()
#  opcional rodar no jupyther o .env
for key, value in dotenv_values('.env').items():
    os.environ[key] = value

cod_erro = []

class XpathClass:
    def __init__(self) -> None:
        # self.nome = print('123HL')
        #  listas de xpath 
        self.link =  f"{os.getenv('ZANTHUS_URL')}/manager/cad_promocao.php5?id_menu=30201"
        self.input_log_id = '//input[@id="USUARIO"]'
        self.input_log_senha =  '//input[@id="SENHA"]'
        self.btn_log_entrar = '//input[@type="submit" and @value=" Entrar "]'
        self.close_notifications= '//li[@class="dropdown notifications-menu open"]'
        self.filtrar_id = '//button[@id="btn_Search"]'
        self.input_codigo_promocao= '//input[@id="FLT_CODPROMOCAO"]'
        self.btn_aplicar_filtro = '//input[@id="EXEC_FILTRO"]'
        self.ativar_desativar_promocao = '//button[@id="novapromocao_ativar_desativar"]'
        self.type_mensage = '//div[@class="sweet-alert showSweetAlert visible"]//div[@id="alert_message_internal"]'
        self.confirm_btn = '//div[@class="sa-confirm-button-container"]//button[@class="confirm"]'
        self.log_zeus = os.getenv('log_zeus')
        self.senha_zeus= os.getenv('senha_zeus')
        


# ========================================================================

class CargasP(XpathClass):
    def __init__(self) -> None:
        super().__init__()
        self.executar_cargas_playwright()

    
    def loguin_function(self,page):
        page.goto(self.link)
        sleep(1)
        
        # Preenche usuário
        page.fill(self.input_log_id, self.log_zeus)
        page.fill(self.input_log_senha, self.senha_zeus)
        page.click(self.btn_log_entrar)
        sleep(3)
        page.goto(self.link)
        self.notifictions()

    def executar_cargas_playwright(self, conjunto_lojas="lojas Minipreço", lojas_especificas=None):

        
        # Configuração de lojas disponíveis
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
        
        # Processa seleção de lojas
        if conjunto_lojas and conjunto_lojas in opcoes_lojas:
            selecao_lojas.extend(opcoes_lojas[conjunto_lojas])
            opcao_selecionada = conjunto_lojas
        
        if lojas_especificas:
            lojas_especificas_list = lojas_especificas if isinstance(lojas_especificas, list) else [lojas_especificas]
            selecao_lojas.extend(lojas_especificas_list)
            if conjunto_lojas:
                opcao_selecionada = f"{conjunto_lojas} + Específicas"
            else:
                opcao_selecionada = "Lojas Específicas"
        
        # Remove duplicatas e ordena
        selecao_lojas = sorted(list(set(selecao_lojas)))
        
        if not selecao_lojas:
            print("ERRO: Nenhuma loja foi selecionada. Use os parâmetros conjunto_lojas ou lojas_especificas.")
            return
        
        print(f'Executando para: {opcao_selecionada}')
        print(f'Lojas selecionadas: {selecao_lojas}')
        
        # Carrega credenciais do .env
        caminho_atual = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.chdir(caminho_atual)
        load_dotenv()
        config = dotenv_values(".env")
        
        for key, value in config.items():
            os.environ[key] = value

        
        # Mapeamento de lojas
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
        
        # Inicia Playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_default_timeout(30000)
            
            # ==================== BLUESOFT ====================
            try:
                self.loguin_function(page)
            except:pass

            page.goto(f"{os.getenv('ZANTHUS_URL')}/manager/adm_cargaDiretaArquivosSemZMS.php5?id_menu=405")
            # page.wait_for_selector("#TOP_HEADER")
            try:
                page.locator('//span[@aria-hidden="true"]').click(timeout=1000)
            except:
                pass
            
            page.wait_for_selector("#btn_AddFavoritos")
            print("✓ Login Zanthus realizado")
            
            # Mantém sessão ativa no Zanthus durante o monitoramento (keepalive periódico)
            def keep_alive ():
                page.evaluate("""
                if (!window.__keepAlive) {
                    window.__keepAlive = setInterval(() => {
                    try {
                        fetch(window.location.href, {
                        method: 'GET',
                        cache: 'no-cache',
                        credentials: 'include'
                        });
                    } catch(e) {}
                    }, 60000);
                }
                """)
            #  desmarca a loja 1 por padrão
            try:
                page.locator('//li[@class="dropdown notifications-menu open"]').click()
            except:pass
            page.locator('//input[@id="GERA_1"]/following-sibling::div[@class="control__indicator"]').click()
            
            # Processa cargas Zanthus (até 3 lojas simultâneas)
            x = 0
            while x < len(selecao_lojas):
                lojas_marcadas = []
                lojas_a_processar = min(6, len(selecao_lojas) - x)
                
                print(f'\n{"="*60}')
                print(f'PROCESSANDO GRUPO DE {lojas_a_processar} LOJA(S)')
                print(f'{"="*60}')
                
                # Marca até 3 lojas
                for i in range(lojas_a_processar):
                    loja_id = selecao_lojas[x + i].split("-")[0].lstrip("0")
                    loja_nome = all_lojas_unicas[selecao_lojas[x + i]][0]
                    
                    checkbox_xpath = f'//input[@id="GERA_{loja_id}"]/following-sibling::div[@class="control__indicator"]'
                    page.locator(checkbox_xpath).click()
                    lojas_marcadas.append((loja_id, loja_nome))
                    print(f'✓ Loja {loja_nome} (ID: {loja_id}) marcada')
                    sleep(0.5)
                
                # Clica em gerar carga
                page.locator('//input[@id="gerarParcial"]').click()
                print(f'✓ Carga iniciada para {len(lojas_marcadas)} loja(s)')
                sleep(10)
                
                # Monitora progresso de cada loja
                for loja_id, loja_nome in lojas_marcadas:
                    print(f'\nMonitorando loja: {loja_nome} (ID: {loja_id})')
                    tempo = tempo2 = ""
                    
                    try:
                        tempo = page.locator(f'//td[@id="R_{loja_id}_TD_3"]').text_content()
                        print(f'Tempo inicial: {tempo}')
                    except:
                        tempo = "0"
                    
                    sleep(2)
                    
                    try:
                        tempo2 = page.locator(f'//td[@id="R_{loja_id}_TD_3"]').text_content()
                    except:
                        tempo2 = "1"
                    
                    tentativas = 0
                    while tempo != tempo2 and tentativas < 100:
                        sleep(8)
                        try:
                            #  clique na notificação
                            # page.locator('//li[@data-original-title="Notificações"]').click()
                            # add sessão ativa
                            keep_alive()
                        except:
                            pass

                        
                        try:
                            tempo = page.locator(f'//td[@id="R_{loja_id}_TD_3"]').text_content()
                            print(f'Progresso: {tempo}')
                        except:
                            tempo = "0"
                        
                        sleep(2)
                        
                        try:
                            tempo2 = page.locator(f'//td[@id="R_{loja_id}_TD_3"]').text_content()
                        except:
                            tempo2 = "1"
                        
                        tentativas += 1
                    
                    print(f'✓ Loja {loja_nome} concluída!')
                
                # Desmarca lojas
                for loja_id, loja_nome in lojas_marcadas:
                    try:
                        checkbox_xpath = f'//input[@id="GERA_{loja_id}"]/following-sibling::div[@class="control__indicator"]'
                        page.locator(checkbox_xpath).click()
                        print(f'✓ Loja {loja_nome} desmarcada')
                        sleep(0.5)
                    except:
                        pass
                
                x += lojas_a_processar
                sleep(2)
            
            print('\n' + '='*60)
            print('TUDO FINALIZADO COM SUCESSO!')
            print('='*60)
            print('\nDesenvolvido por Victor José Costta Lameiro')
            print('https://www.linkedin.com/in/victorjcl')
            print('https://github.com/victorjcl')
            
            # Limpa keepalive antes de fechar o navegador
            try:
                page.evaluate("""
                if (window.__keepAlive) { clearInterval(window.__keepAlive); delete window.__keepAlive; }
                """)
            except:
                pass
            
            browser.close()
            p.stop()






class PlaywrightClass(XpathClass):
    def __init__(self,):
        super().__init__()
        self.page = None  # Inicialize depois
        # self.codigo_id=codigo_id
        

    def start_browser(self,p):
        self.browser = p.chromium.launch(headless=False, )
        # context = browser.new_context(viewport={"width": 900, "height": 600})
        context = self.browser.new_context()
        self.page = context.new_page()

    def loguin_function(self):
        page=self.page
        page.goto(self.link)
        sleep(1)
        
        # Preenche usuário
        page.fill(self.input_log_id, self.log_zeus)
        page.fill(self.input_log_senha, self.senha_zeus)
        page.click(self.btn_log_entrar)
        sleep(3)
        page.goto(self.link)
        self.notifictions()
        page=self.page
        # Maximiza janela
        # page.set_viewport_size({"width": 1920, "height": 1080})

    def notifictions(self):
        try:
            self.page.click(self.close_notifications, timeout=1000)
        except: pass

    def buscar_cod_prom(self, codigo_id):
        # codigo_id = '17'
        
        self.page.locator(self.filtrar_id).click()
        self.page.fill(self.input_codigo_promocao, codigo_id)
        self.page.locator(self.btn_aplicar_filtro).click()
        self.notifictions()
    
    def ativar__promocao(self):
        self.page.locator(self.ativar_desativar_promocao).click()
        sleep(2)
        message_loc =self.page.locator(self.type_mensage).text_content()
        self.page.locator(self.confirm_btn).click()
        if 'ativada com Sucesso' in message_loc:
            self.page.locator(self.ativar_desativar_promocao).click()
            self.page.locator(self.confirm_btn).click()
            print('mensagem DESATIVADA', message_loc)
        elif 'desativada com sucesso' in  message_loc:
            print('mensagem já desativada',message_loc)

    def main_plawrigt(self, codigo_id):
        global cod_erro
        cod_erro = []
        if not isinstance(codigo_id, list):
            codigo_id = [codigo_id]
        # codigo_id = lambda codigo_id: [str(x) for x in codigo_id]
        codigo_id=[str(x) for x in codigo_id]

        with sync_playwright() as p:
            self.start_browser(p)
            
            self.loguin_function()
            for cod in codigo_id:
                self.buscar_cod_prom(cod)
                try:
                    self.ativar__promocao()
                except:
                    print(f'pack {cod} não encontrado')
                    cod_erro.append(f'Não foi encontrado o pack {cod}')

            sleep(5)
            self.browser.close()
            p.stop()
        





# ==========================


# def exec_agendar_tarefa( codigo_pack):
#     print('executando exec_agendar_tarefa')
#     PlaywrightClass().main_plawrigt(codigo_pack)
#     # CargasP()
#     print('finalizado exec_agendar_tarefa')



# def derruba_pack_mainfun(codigo_pack, option_pack=1):
#     option_pack=int(option_pack)
#     try:
#         if option_pack==1:
#             PlaywrightClass().main_plawrigt(codigo_pack)
#             return "Pack derrubado com sucesso, não foi realizada a carga"
#         elif option_pack==2:
#             PlaywrightClass().main_plawrigt(codigo_pack)
#             CargasP()
#             return "Pack derrubado com sucesso e carga realizada"
#         elif option_pack==3:
#             #  lógica para agendar execução de  exec_agendar_tarefa() para as 11h de forma que o código não fique parado, seja executado em um processo diferente desse e execute os outros prints
          
            
            
#             print('agendamento realizado ****')
#             print('código continua sem ficar preso')
#             return "Pack derrubado e agendamento realizado"
#         else:
#             print("Opção inválida")
#     except Exception as er:
#         raise Exception('Erro ao derrubar pack', er)
#         return 'Erro ao derrubar pack'


# =======================





def exec_agendar_tarefa(codigo_pack):
    global cont_loop
    print('executando exec_agendar_tarefa')
    PlaywrightClass().main_plawrigt(codigo_pack)
    # CargasP()
    print('finalizado exec_agendar_tarefa')
    cont_loop= False

     

def iniciar_scheduler_thread(codigo_pack):
    """Inicia o scheduler em uma thread separada"""
    def run_scheduler():
        global cont_loop
        cont_loop=True
        schedule.every().day.at("21:00").do(exec_agendar_tarefa, codigo_pack)
        
        # while True:
        while cont_loop:
            # if cont_loop == False:
            #     break
            schedule.run_pending()
            # time.sleep(60)  # Verifica a cada 60 segundos
            sleep(60)  # Verifica a cada 60 segundos
            print('AGENDAMENTO DE PACK ATIVO PARA 21:00')
            
        print('programa finalizado')

    
    # Cria e inicia a thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=False)
    scheduler_thread.start()
    print(f'Agendamento criado(thread iniciada às {datetime.now().strftime("%H:%M:%S")})')

def derruba_pack_mainfun(codigo_pack, option_pack=1):
    option_pack = int(option_pack)
    try:
        # if option_pack == 1:
        #     PlaywrightClass().main_plawrigt(codigo_pack)
        #     return "Pack derrubado com sucesso, não foi realizada a carga"
        if option_pack == 1:
            PlaywrightClass().main_plawrigt(codigo_pack)
            CargasP()
            if cod_erro:
                return f"Processo concluído, mas com avisos:\n" + "\n".join(cod_erro)
            return "Pack(s) derrubado(s) com sucesso e carga(s) realizada(s)."
        
        elif option_pack == 2:
            # Agenda execução para as 11h em thread separada
            iniciar_scheduler_thread(codigo_pack)
            
            print('agendamento realizado ****')
            print('código continua sem ficar preso')
            if cod_erro:
                return f"Agendamento realizado, mas com avisos:\n" + "\n".join(cod_erro)
            return "Pack(s) programado(s) para derrubada/inativação e envio de carga(s) para o final do expediente."
        
        elif option_pack != 1 and option_pack != 2:
            raise ValueError('erro de valor option_pack, diferente de 1 ou 2')

        else:
            print("Opção inválida")
            return "Opção inválida"
            
    except Exception as er:
        raise Exception(f'Erro ao derrubar pack: {er}')



if __name__ == "__main__":
    pass
    # print('exe')
    #  pode ter mais de um pack para derrubar
    # derruba_pack_mainfun(17, 3)
    # derruba_pack_mainfun(8125, 3)
    # derruba_pack_mainfun(8125, 2)



# def exec_agendar_tarefa( codigo_pack):
#     print('executando exec_agendar_tarefa')
#     PlaywrightClass().main_plawrigt(codigo_pack)
#     # CargasP()
#     print('finalizado exec_agendar_tarefa')
    # Seu código aqui

# async def run_scheduler():
#     """Loop assíncrono que verifica agendamentos pendentes"""
#     while True:
#         schedule.run_pending()
#         await asyncio.sleep(1)

# async def agendar_tarefa(codigo_pack):
#     loop = asyncio.get_running_loop()
#     schedule.every().day.at("10:55").do(lambda: loop.create_task(asyncio.to_thread(exec_agendar_tarefa, codigo_pack)))
#     asyncio.create_task(run_scheduler())
#     print("Agendamento configurado!")
#     while True:
#         await asyncio.sleep(1)
    


