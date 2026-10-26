from playwright.sync_api import sync_playwright, Page
from time import sleep
import os
import random
from dotenv import load_dotenv
from typing import Union
from data.sistemas import ZANTHUS_URL


# Inicializa Playwright

def voucher_tools_pl(parametros_voucher: list[dict]) -> tuple[list, list]:
    historico_valchers: list[list] = []
    avisos_voucher: list[str] = []

    from pathlib import Path
    base_dir = Path(__file__).resolve().parent.parent
    env_path = base_dir / '.env'
    load_dotenv(dotenv_path=env_path)

    log_zeus = os.getenv('log_zeus') or os.getenv('LOG_ZEUS')
    senha_zeus = os.getenv('senha_zeus') or os.getenv('SENHA_ZEUS')
    if not log_zeus or not senha_zeus:
        raise RuntimeError('Credenciais log_zeus ou senha_zeus não foram encontradas no .env')

    lojas_dict = {
        1: '(//a[@role="option"])[1]',
        2: '(//a[@role="option"])[2]',
        4: '(//a[@role="option"])[3]',
        6: '(//a[@role="option"])[4]',
        7: '(//a[@role="option"])[5]',
        8: '(//a[@role="option"])[6]',
        10: '(//a[@role="option"])[8]',
        11: '(//a[@role="option"])[9]',
        12: '(//a[@role="option"])[10]',
        14: '(//a[@role="option"])[11]',
        18: '(//a[@role="option"])[13]',
        19: '(//a[@role="option"])[14]',
        20: '(//a[@role="option"])[15]',
        301: '(//a[@role="option"])[22]',
        303: '(//a[@role="option"])[23]',
        304: '(//a[@role="option"])[24]',
        305: '(//a[@role="option"])[25]',
        307: '(//a[@role="option"])[26]',
        308: '(//a[@role="option"])[27]',
        900: '(//a[@role="option"])[29]'
    }


    def tratamento_variaveis(lojas_param: Union[list, str, int]) -> list[int]:
        lojas_lista: list[int] = []
        if isinstance(lojas_param, int):
            lojas_lista = [lojas_param]
        elif isinstance(lojas_param, str):
            lojas_lista = [lojas_param]
        else:
            lojas_lista = list(lojas_param)

        expansao = []
        for loja in lojas_lista:
            if isinstance(loja, str):
                lower = loja.lower()
                if lower in ('prm', 'pr'):
                    expansao.extend([1, 2, 4, 6, 7, 8, 10, 11, 12, 14, 19, 20])
                elif lower == 'prs':
                    expansao.extend([1, 2, 4, 6, 8, 11, 14, 18, 19])
                elif lower in ('scs', 'sc'):
                    expansao.extend([201, 202, 203, 204, 208])
                elif lower in ('salvados', 'salv'):
                    expansao.extend([1, 2, 4, 6, 8, 11, 14, 18, 19])
                elif lower in ('esm', 'es'):
                    expansao.extend([301, 303, 304, 305, 307, 308])
                elif lower == 'mini':
                    expansao.extend([1, 2, 4, 6, 7, 8, 10, 11, 12, 14, 19, 20, 301, 303, 304, 305, 307, 308])
                elif lower == 'tudo':
                    expansao.extend([1,2, 4, 6, 7, 8, 10, 11, 12, 14, 18, 19, 20, 301, 303, 304, 305, 307, 308])
                else:
                    try:
                        expansao.append(int(loja))
                    except:
                        pass
            elif isinstance(loja, int):
                expansao.append(loja)

        lojas_lista = sorted(set(expansao))
        print(lojas_lista)
        return lojas_lista

    def notification(page: Page) -> None:
        try:
            page.locator('//li[@class="dropdown notifications-menu open"]').wait_for(timeout=3000)
        except:
            pass

    def login_function(page: Page) -> None:
        page.goto(f'{ZANTHUS_URL}/manager/adm_cargaDiretaArquivosSemZMS.php5?id_menu=405')
        page.wait_for_selector('#USUARIO', timeout=15000)
        page.fill('#USUARIO', log_zeus)
        page.fill('#SENHA', senha_zeus)
        page.click('//input[@type="submit" and @value=" Entrar "]')
        page.wait_for_load_state('networkidle')

        try:
            page.click('//span[@aria-hidden="true"]', timeout=3000)
        except:
            pass

        page.goto(f'{ZANTHUS_URL}/manager/cad_voucher_promocional.php5?opt=Inc&id_menu=30204')
        page.wait_for_load_state('networkidle')
        sleep(1)
        print('DEBUG: current page URL after login:', page.url)
        try:
            page.wait_for_selector('body', timeout=5000)
        except:
            pass
        notification(page)

    def select_stores(page: Page, lojas_lista: list[int]) -> None:
        page.locator('#DIV_ABA_H_2').click()
        page.wait_for_selector('#COD_LOJA', timeout=8000)
        page.wait_for_timeout(500)

        for loj in lojas_lista:
            if loj not in lojas_dict:
                continue
            try:
                page.select_option('#COD_LOJA', str(loj))
                page.locator('#CLASSE_1_BOTAO').click()

            except Exception as error:
                print(f'falha ao achar a loja na aba de lojas\nErro loja: {error}' )


    def essenciais_checkbox_fun(page: Page, lojas_lista: list[int]) -> None:
        # page.pause()
        page.wait_for_selector('//input[@id="COD_VOUCHER"]', timeout=15000)
        page.evaluate(
            "document.evaluate(\"(//label[@class='control control--radio'][following-sibling::span[text()='No produto']]//div[@class='control__indicator'])[1]\", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click();"
        )
        page.wait_for_timeout(500)
        page.evaluate(
            "document.evaluate(\"(//div[@id='TIPO_VENDA_DIV']//div[@class='control__indicator'])[2]\", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click();"
        )
        page.wait_for_timeout(500)
        page.evaluate(
            "document.evaluate(\"(//div[@id='FLAGS_DIV']//div[@class='control__indicator'])[2]\", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click();"
        )
        page.wait_for_timeout(500)
        page.evaluate(
            "document.evaluate(\"(//div[@id='FLAGS_DIV']//div[@class='control__indicator'])[1]\", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click();"
        )
        page.wait_for_timeout(300)
        # page.pause()

        #  comportamento:
        # page.evaluate(
        #     "var select = document.querySelector('select[name=\"TIPO_COMPORTAMENTO\"]') || document.querySelector('select#TIPO_COMPORTAMENTO');"
        #     "if(select) { select.value='2'; select.dispatchEvent(new Event('change', { bubbles: true })); }"
        # )
        # page.wait_for_timeout(600)

        if not lojas_lista:
            page.evaluate(
                "document.evaluate(\"//div[@class='form-group'][.//label[@id='L_FLAGS_MANAGER[]' ]]//div[@class='control__indicator']\", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click();"
            )
        else:
            select_stores(page, lojas_lista)
            page.wait_for_timeout(1000)
            page.evaluate("document.getElementById('DIV_ABA_H_0')?.click();")
            page.wait_for_timeout(800)

    def new_voucher(page: Page) -> None:
        page.wait_for_selector('body', timeout=20000)

        try:
            if page.locator('#btn_Incluir').is_visible():
                page.click('#btn_Incluir')
                page.wait_for_timeout(1700)
                notification(page)
                return
        except:
            pass

        page.goto(f'{ZANTHUS_URL}/manager/cad_voucher_promocional.php5?opt=Inc&id_menu=30204')
        page.wait_for_selector('//input[@id="COD_VOUCHER"]', timeout=20000)
        page.wait_for_timeout(1200)
        notification(page)

    def gerar_numero_7d() -> int:
        return random.randint(100000, 99999999)

    def inputs_dados(
        page: Page,
        valor_ou_poncentagem: Union[str, int],
        lista_quantia_valor_param: list,
        data_vencimento_param: str,
        parceiro_param: str,
        lojas_lista: list[int],
    ) -> None:
        if str(valor_ou_poncentagem) == '1':
            page.evaluate(
                "document.evaluate(\"(//div[@class='form-group'][.//label[@id='L_TIPO_APLICACAO' ]]//div[@class='control__indicator'])[2]\", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click();"
            )
        elif str(valor_ou_poncentagem) == '2':
            page.evaluate(
                "document.evaluate(\"(//div[@class='form-group'][.//label[@id='L_TIPO_APLICACAO' ]]//div[@class='control__indicator'])[1]\", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click();"
            )

        number_voucher = str(gerar_numero_7d())
        page.fill('//div[@id="aba_body_0"]//input[@id="COD_VOUCHER"]', number_voucher)
        page.press('//div[@id="aba_body_0"]//input[@id="COD_VOUCHER"]', 'Tab')
        page.wait_for_timeout(250)
        page.fill('//div[@id="aba_body_0"]//input[@id="VALOR_APLICACAO"]', str(lista_quantia_valor_param[1]))
        page.fill('//div[@id="aba_body_0"]//input[@id="VALIDADE_FINAL"]', data_vencimento_param)
        page.press('//div[@id="aba_body_0"]//input[@id="VALIDADE_FINAL"]', 'Tab')
        page.fill('//div[@id="aba_body_0"]//input[@id="DESCRICAO_PARCEIRO"]', parceiro_param)

        page.click('//button[@id="btn_Salvar"]')
        page.wait_for_timeout(2000)

        try:
            if page.locator('//div[@id="alert_message_internal"]').is_visible():
                alerta = page.locator('//div[@id="alert_message_internal"]').text_content()
                if alerta:
                    avisos_voucher.append(alerta)
        except:
            pass

        try:
            page.wait_for_selector('//button[@class="confirm"]', timeout=5000)
            page.click('//button[@class="confirm"]')
        except:
            pass

        historico_valchers.append([number_voucher, lista_quantia_valor_param[1], lojas_lista])

    def clone_voucher(page: Page, lista_quantia_valor_param: list, lojas_lista: list[int]) -> None:
        qtd = 1
        try:
            qtd = int(lista_quantia_valor_param[0])
        except:
            pass

        for _ in range(2, qtd + 1):
            page.wait_for_selector('//input[@id="FLT_COD_VOUCHER"]', timeout=15000)
            page.fill('//input[@id="FLT_COD_VOUCHER"]', str(historico_valchers[-1][0]))
            page.click('//input[@id="EXEC_FILTRO"]')
            page.wait_for_timeout(1500)
            page.wait_for_selector('//button[@data-original-title="Clonar cadastro"]', timeout=15000)
            page.click('//button[@data-original-title="Clonar cadastro"]')
            page.wait_for_selector('//div[@id="aba_body_0"]//input[@id="COD_VOUCHER"]', timeout=15000)

            number_voucher = str(gerar_numero_7d())
            page.fill('//div[@id="aba_body_0"]//input[@id="COD_VOUCHER"]', number_voucher)
            page.fill('//div[@id="aba_body_0"]//input[@id="VALOR_APLICACAO"]', str(lista_quantia_valor_param[1]))
            page.click('//button[@id="btn_Salvar"]')
            page.wait_for_timeout(2000)

            try:
                page.wait_for_selector('//button[@class="confirm"]', timeout=5000)
                page.click('//button[@class="confirm"]')
            except:
                pass

            historico_valchers.append([number_voucher, lista_quantia_valor_param[1], lojas_lista])

            try:
                page.click('//button[@data-original-title="Voltar"]', timeout=8000)
                page.wait_for_timeout(800)
            except:
                pass

    resultados: list[dict] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        login_function(page)
        sleep(1)

        for parametro in parametros_voucher:
            try:
                lista_qt_val = parametro.get('quantidade_valor', [1, 0])
                tipo = parametro.get('valor_ou_poncentagem', parametro.get('valor_ou_poncertagem', 1))
                lojas_param = parametro.get('lojas_param', [])
                data_venc = parametro.get('data_vencimento_param', '')
                nome = parametro.get('Nome_do_voucher', 'voucher')

                lojas_lista_final = tratamento_variaveis(lojas_param) if lojas_param else []
                try:
                    qtd = max(1, int(lista_qt_val[0]))
                except Exception:
                    qtd = 1

                for _ in range(qtd):
                    new_voucher(page)
                    essenciais_checkbox_fun(page, lojas_lista_final)
                    inputs_dados(page, tipo, lista_qt_val, data_venc, nome, lojas_lista_final)

                resultados.append({'parametro': parametro, 'historico': historico_valchers[-qtd:]})
            except Exception as e:
                avisos_voucher.append(str(e))
                print(f"Erro criando voucher para {parametro}: {e}")

        try:
            context.close()
            browser.close()
        except:
            pass
    # print(historico_valchers)
    return historico_valchers, avisos_voucher



# if __name__ == '__main__':
#     # fazder um teste de funcionamento
#     teste = voucher_tools_pl([{'quantidade_valor': [2, 10],
#                                  'valor_ou_poncentagem': 1,
#                                     'lojas_param': [7, 900, 1, 2], 
#                                 'data_vencimento_param': '11/07/2026',
#                                     'Nome_do_voucher': 'Voucher promotoras ação Clube MiniPreço'}])
#     print(teste)


    # voucher_tools_pl([{'quantidade_valor': [1, 200],
    #  'valor_ou_poncentagem': 1,
    #   'lojas_param': [7], 
    # 'data_vencimento_param': '17/12/2025',
    #  'Nome_do_voucher': 'Voucher promotoras ação Clube MiniPreço'}])
    # voucher_tools_pl(
    #      [{'quantidade_valor': [2, 5], 
    #        'valor_ou_poncentagem': 1, 
    #        'lojas_param': [900], 
    #       'data_vencimento_param': '11/07/2026', 
    #       'Nome_do_voucher': 'Teste'}]
    # )

