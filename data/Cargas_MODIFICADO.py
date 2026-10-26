from playwright.sync_api import sync_playwright
from time import sleep
import os
from dotenv import load_dotenv, dotenv_values
# from arq_api_acelerato import responder_chamado_acelerato

#  Desenvolvido por Victor José Costta Lameiro   https://www.linkedin.com/in/victorjcl  https://github.com/victorjcl

"""
TOOL - GERAÇÃO DE CARGAS AUTOMÁTICA PARA LOJAS

COMO USAR ESTA FERRAMENTA:
Esta ferramenta automatiza a geração de cargas para lojas nos sistemas Bluesoft e Zanthus usando Playwright.

PARÂMETROS:
- conjunto_lojas (str, opcional): Nome do conjunto de lojas pré-definido
  Opções: "Lojas PR MiniPreço", "Lojas PR Salvados", "Lojas SC Salvados", 
          "Lojas Espírito Santo MiniPreço", "Lojas Minipreço", "Todas as lojas"
  
- lojas_especificas (str ou list, opcional): Código(s) de loja(s) específica(s)
  Exemplos: "01", ["01", "02", "04"], ["301", "303"]


2. Playwright instalado: pip install playwright
3. Navegadores instalados: playwright install

EXEMPLOS DE USO PARA IA:
1. Gerar cargas para todas as lojas:
   executar_cargas_playwright(conjunto_lojas="Todas as lojas")

2. Gerar cargas para lojas específicas:
   executar_cargas_playwright(lojas_especificas=["01", "02", "04"])

3. Gerar cargas para um conjunto + lojas adicionais:
   executar_cargas_playwright(conjunto_lojas="Lojas SC Salvados", lojas_especificas=["01"])

PROCESSO:
1. Faz login no Bluesoft
2. Configura e gera cargas para as lojas selecionadas no Bluesoft
3. Faz login no Zanthus
4. Gera cargas para as mesmas lojas no Zanthus (até 3 lojas simultâneas)
5. Monitora o progresso até conclusão
6. Fecha o navegador

OBSERVAÇÕES:
- A ferramenta processa até 3 lojas simultaneamente no Zanthus para otimizar o tempo
- Monitora automaticamente o progresso e aguarda conclusão
- Loga todos os passos para rastreamento
- Usa Playwright (mais rápido e estável que Selenium)
"""




def executar_cargas_playwright(conjunto_lojas=None, lojas_especificas=None):
    aviso_erro=[]
    avisos_blue = {}
    """
    Executa geração de cargas para lojas nos sistemas Bluesoft e Zanthus usando Playwright.
    
    Args:
        conjunto_lojas: Nome do conjunto de lojas pré-definido
        lojas_especificas: Lista ou string com código(s) de loja(s) específica(s)
    """
    
    # Configuração de lojas disponíveis
    opcoes_lojas = {
        "Lojas PR MiniPreço": ["01","02","04","06","07","08","10","11","12","14","19","20"],
        "Lojas PR Salvados": ["01","02","04","06","08","09","11","14","17","18","19"],
        "Lojas SC Salvados": ["201","202","208"],
        "Salvados PR SC" : ["01","02","04","06","08","09","11","14","17","18","19","201","202","208"],
        "Lojas Espírito Santo MiniPreço": ["301","303","304","305","307","308"],
        "Lojas Minipreço": ["01","02","04","06","07","08","10","11","12","14","19","20","301","303","304","305","307","308"],
        "Todas as lojas":  ["01","02","04","06","07","08","09","10","11","12","14","17","18","19","20","301","303","304","305","307","308"]
        # "Todas as lojas": ["01","02","04","06","07","08","09","10","11","12","14","17","18","19","20","201","202","208","301","303","304","305","307","308"]
    }
    
    selecao_lojas = []
    
    # Processa seleção de lojas
    if conjunto_lojas and conjunto_lojas in opcoes_lojas:
        selecao_lojas.extend(opcoes_lojas[conjunto_lojas])
        opcao_selecionada = conjunto_lojas
    
    if lojas_especificas:
        lojas_especificas_list = [str(l) for l in (lojas_especificas if isinstance(lojas_especificas, list) else [lojas_especificas])]
        # Normaliza códigos de loja: adiciona '0' à esquerda se for número < 10
        lojas_especificas_list = [loja.zfill(2) if loja.isdigit() and int(loja) < 10 else loja for loja in lojas_especificas_list]
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
    
    log_blue = os.getenv('LOG_BLUE')
    senha_blue = os.getenv('SENHA_BLUE')
    log_zeus = os.getenv('LOG_ZEUS')
    senha_zeus = os.getenv('SENHA_ZEUS')
    
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
        # browser = p.chromium.launch(headless=True)
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_default_timeout(30000)
        
        # ==================== BLUESOFT ====================
        print("\n=== INICIANDO BLUESOFT ===")
        page.goto(f"{os.getenv('BLUESOFT_URL')}/menu/170")
        
        # Login Bluesoft
        page.wait_for_selector("#j_username")
        page.fill("#j_username", log_blue)
        page.fill("#j_password", senha_blue)
        sleep(1)
        page.click("#btnSubmit")
        page.wait_for_selector("#conteudoFrenteCaixa")
        
        print("✓ Login Bluesoft realizado")
        
        # Configura página de cargas
        sleep(2)
        # page.locator('//select[.//option[@label="Somente alterados no período"]]').select_option(label="Somente alterados no período")
        page.get_by_role("checkbox", name="PDVs", exact=True).click()
        page.get_by_role("checkbox", name="Terminais de Consulta").click()
        page.get_by_role("checkbox", name="Promoção Ganhe Pontos").click()
        # page.get_by_role("checkbox", name="PDVs Regras Fiscais (Zanthus)").click()
        page.get_by_role("checkbox", name="Etiquetas").click()
        
        print("✓ Configurações de carga aplicadas")
        
        # Marca lojas no Bluesoft
        for loja in selecao_lojas:
            page.locator(f'//label[contains(., "{all_lojas_unicas[loja][1]}")]/input[@type="checkbox"]').click()
            print(f"✓ Loja {all_lojas_unicas[loja][1]} marcada")
        
        sleep(2)
        page.locator('//button[@id="gerarArquivos"]').click()
        print("✓ Geração de cargas iniciada no Bluesoft")
        
        # Monitora progresso Bluesoft
        sleep(20)
        count_blue = 0
        if len(selecao_lojas) == 1:
            cot = 0
            nunb_mesage = len(page.locator('''//h4[@id="msg-arquivo-gerado-sucesso"] ''').all())
            while nunb_mesage == 0:
                cot+=5
                sleep(5)
                nunb_mesage = len(page.locator('''//h4[@id="msg-arquivo-gerado-sucesso"] ''').all())
                if nunb_mesage == 1:
                    break
                nunb_mesage = len(page.locator('''//h4[@id="msg-erro-gerar-arquivo"] ''').all())
                if cot == 1200:
                    break
        else:
            progress = page.locator('//div[@class="progress-bar"]//span[@class="ng-binding ng-scope"]').text_content()
            while progress != '100%':
                sleep(30)
                try:
                    progress = page.locator('//div[@class="progress-bar"]//span[@class="ng-binding ng-scope"]').text_content()
                    print(f'Progresso Bluesoft: {progress}')
                except Exception as err:
                    print(f'Erro no progresso do tempo Bluesoft:\n{err}')
                    break
                count_blue += 30
                if count_blue >= 5000:
                    print('⚠️ Tempo de espera Bluesoft expirado (5000s)')
                    break
            
        # Captura relatório de avisos/erros das lojas
        try:
            lojas = page.locator('//span[@ng-class="vm.obterLojaCssClass(key, loja)"]').all()
            avisos_blue = {}
            for l in lojas:
                try:
                    l.click()
                    # page.wait_for_timeout(1000)
                    aviso_element = page.locator('//div[@ng-class="[\'alert-\' + (type || \'warning\'), closeable ? \'alert-dismissible\' : null]"]').first
                    texto_aviso = aviso_element.inner_text()
                    if 'Arquivo(s) gerado(s) com sucesso' not in texto_aviso:
                        avisos_blue[l.inner_text()] = texto_aviso
                        print(f'⚠️ Aviso na loja {l.inner_text()}: {texto_aviso}')
                except Exception as e:
                    # Ignora erros ao processar lojas individuais
                    continue
            
            if avisos_blue:
                print(f'\n⚠️ Avisos encontrados em {len(avisos_blue)} loja(s) no Bluesoft')
        except Exception as e:
            print(f'⚠️ Não foi possível capturar relatório de avisos: {e}')
        
        print('✓ Lojas finalizadas no Bluesoft\n')
        
        # ==================== ZANTHUS ====================
        print("=== INICIANDO ZANTHUS ===")
        page.goto(f"{os.getenv('ZANTHUS_URL')}/manager/adm_cargaDiretaArquivosSemZMS.php5?id_menu=405")
        
        # Login Zanthus
        page.wait_for_selector("#USUARIO")
        page.fill("#USUARIO", log_zeus)
        page.fill("#SENHA", senha_zeus)
        page.locator('//input[@type="submit" and @value=" Entrar "]').click()
        sleep(3)
        
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
            lojas_a_processar = min(8, len(selecao_lojas) - x)
            
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
            
            # Função para detectar erros no formato do tempo
            def aviso_tempo(tempo, loja_id_param):
                nonlocal aviso_erro
                if ':' not in tempo and 's' not in tempo:
                    aviso_erro.append(f'Erro de carga na loja {loja_id_param}: {tempo}')
                    print(f'⚠️ Erro detectado na loja {loja_id_param}: {tempo}')
                    return True
                return False
            
            # Monitora progresso de cada loja
            for loja_id, loja_nome in lojas_marcadas:
                print(f'\nMonitorando loja: {loja_nome} (ID: {loja_id})')
                tempo = tempo2 = ""
                count_zanthus = 0
                
                try:
                    tempo = page.locator(f'//td[@id="R_{loja_id}_TD_3"]').text_content()
                    print(f'Tempo inicial: {tempo}')
                    # Verifica se já há erro no tempo inicial
                    if aviso_tempo(tempo, loja_id):
                        continue  # Pula para próxima loja
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
                    count_zanthus += 8
                    
                    # Timeout de 2700 segundos 
                    if count_zanthus >=2700:
                        print(f'⚠️ Timeout de 2700 segundos atingido para loja {loja_nome}')
                        aviso_erro.append(f'Timeout na loja {loja_id}: processo excedeu 45 min')
                        break
                    
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
                        # Verifica se há erro no formato do tempo
                        if aviso_tempo(tempo, loja_id):
                            break  # Interrompe o monitoramento desta loja
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
        
        # Resumo de erros detectados
        print('\n' + '='*60)
        if aviso_erro or avisos_blue:
            print('PROCESSO FINALIZADO COM AVISOS/ERROS')
            if avisos_blue:
                print(f'\n⚠️ Avisos no Bluesoft: {len(avisos_blue)} loja(s)')
                for loja, aviso in avisos_blue.items():
                    print(f'  - {loja}: {aviso}')
            if aviso_erro:
                print(f'\n⚠️ Erros no Zanthus: {len(aviso_erro)}')
                for erro in aviso_erro:
                    print(f'  - {erro}')
        else:
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

        # Retorno condicional baseado nos erros encontrados
        if aviso_erro and not avisos_blue:
            return f'<p>Carga feita das lojas: {selecao_lojas}</p> <p>Erro Zanthus: {aviso_erro}</p>'
        elif avisos_blue and not aviso_erro:
            return f'<p>Carga feita das lojas: {selecao_lojas}</p> <p>Erro na Bluesoft: {avisos_blue}</p>'
        elif avisos_blue and aviso_erro:
            return f'<p>Carga feita das lojas: {selecao_lojas}</p> <p>Erro na Bluesoft: {avisos_blue}</p> <p>Erro Zanthus: {aviso_erro}</p>'
        else: 
            return f'Carga realizada para as lojas {selecao_lojas}'
    
    


if __name__ == "__main__":
    # ==================== EXEMPLOS DE USO PARA TESTE ====================
    
    # Teste 1: Lojas PR MiniPreço
    # print("\n### TESTE 1: Lojas PR MiniPreço ###")
    # executar_cargas_playwright(conjunto_lojas="Lojas PR MiniPreço")
    
    # Teste 2: Lojas PR Salvados
    # print("\n### TESTE 2: Lojas PR Salvados ###")
    # executar_cargas_playwright(conjunto_lojas="Lojas PR Salvados")
    
    # Teste 3: Lojas SC Salvados
    # print("\n### TESTE 3: Lojas SC Salvados ###")
    # executar_cargas_playwright(conjunto_lojas="Lojas SC Salvados")
    
    # Teste 4: Lojas Espírito Santo MiniPreço
    # print("\n### TESTE 4: Lojas Espírito Santo MiniPreço ###")
    # executar_cargas_playwright(conjunto_lojas="Lojas Espírito Santo MiniPreço")
    
    ##Teste 5: Todas as Lojas Minipreço
    # print("\n### TESTE 5: Todas as Lojas Minipreço ###")
    # executar_cargas_playwright(conjunto_lojas="Lojas Minipreço")
    
    # #Teste 6: TODAS AS LOJAS
    # print("\n### TESTE 6: TODAS AS LOJAS ###")
    # executar_cargas_playwright(conjunto_lojas="Todas as lojas")
    
    # Teste 7: Lojas específicas
    # print("\n### TESTE 7: Lojas específicas ###")
    # executar_cargas_playwright(lojas_especificas=["04", "06"])
    # pass
  
    # executar_cargas_playwright(lojas_especificas=["900","201","202","208","301","303","304"])
    # func_retorno = executar_cargas_playwright(lojas_especificas=["900","201","202","208","301","303","304"])
    # print(func_retorno)
    
    # print("\n✓ Arquivo de teste criado com sucesso!")
    # print("Descomente qualquer teste acima para executar")
    # print("\nREQUISITOS:")
    # print("1. pip install playwright python-dotenv")
    # print("2. playwright install")
    # print("3. Configurar arquivo .env com as credenciais")
    
    # executar_cargas_playwright(lojas_especificas= ['11', '301', '303', '308', '10', '06'])
    # executar_cargas_playwright(lojas_especificas= ['304'])
    # executar_cargas_playwright(conjunto_lojas='tudo')
    pass

