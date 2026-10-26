import os
import traceback
from datetime import date
from time import sleep
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import pandas as pd

try:
    from .arq_api_acelerato import baixar_anexo, responder_com_imagem  # importação como pacote
except ImportError:
    from arq_api_acelerato import baixar_anexo, responder_com_imagem   # execução direta

""" Falta:
validar para 18 dígitos completando com 0
deixar ' antes do primeiro 0
"""


class BookZanthus:
    """
    Envia um CSV para a Zanthus automaticamente para atualizar os packs de e-books.

    Retorna um dict com o resultado de cada etapa para consumo pela IA:
    {
        "sucesso": bool,
        "etapa_falha": str | None,
        "mensagem": str,
        "detalhes": str | None
    }
    """

    def __init__(self):
        self.hoje = date.today().strftime("%d/%m/%Y")
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        os.makedirs("arquivos", exist_ok=True)

    def _resultado(self, sucesso: bool, etapa_falha: str | None, mensagem: str, detalhes: str | None = None) -> dict:
        return {
            "sucesso": sucesso,
            "etapa_falha": etapa_falha,
            "mensagem": mensagem,
            "detalhes": detalhes,
        }

    def login_zanthus(self, page):
        """Realiza login no sistema Zanthus."""
        load_dotenv()
        login = os.getenv('LOG_ZEUS')
        senha = os.getenv('SENHA_ZEUS')

        if not login or not senha:
            raise ValueError("Credenciais LOG_ZEUS ou SENHA_ZEUS não encontradas no .env")

        print("[Zanthus] Realizando login...")
        page.goto(f"{os.getenv('ZANTHUS_URL')}/manager/adm_importacao_6.php5?id_menu=10702")
        page.fill('#USUARIO', login)
        page.fill('#SENHA', senha)
        page.get_by_role("button", name="Entrar").click()
        sleep(5)
        print("[Zanthus] Login efetuado.")

    def zanthus_upload(self, page, caminho):
        """Faz o upload do CSV na Zanthus e tira screenshot do resultado."""
        print('Processando...')
        page.goto(f"{os.getenv('ZANTHUS_URL')}/manager/adm_importacao_6.php5?id_menu=10702")
        sleep(3)
        page.locator(".control__indicator").first.click()
        page.locator("tr:nth-child(9) > .classe_label_form_padrao > .control > .control__indicator").click()  # arquivo.csv  (ordem dos botões)
        page.get_by_text("selecionar arquivo(s)").set_input_files(caminho)
        sleep(3)
        page.get_by_role("button", name="OK").click()
        page.locator('//input[@id="GERAR"]').click()
        sleep(110)

        try:
            page.screenshot(path="arquivos/print_tela_inteira.png", full_page=True)
            print("[Zanthus] Screenshot salvo.")
        except Exception:
            print("[Zanthus] Aviso: falha ao salvar screenshot.")

        sleep(1)

    def padroniza_csv(self, caminho):
        try:
            # Processa de acordo com o formato real que o baixador entregou
            if caminho.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(caminho, converters={'codproduto': str})
            else:
                try:
                    df = pd.read_csv(caminho, sep=None, engine='python', converters={'codproduto': str}, encoding='utf-8')
                except UnicodeDecodeError:
                    # Se falhar a leitura CSV por ser ISO-8859-1 (ansi normal do excel), cai aqui para forçar salvar
                    df = pd.read_csv(caminho, sep=None, engine='python', converters={'codproduto': str}, encoding='latin-1')
        except Exception as e:
            raise ValueError(f"Erro ao ler o CSV, deve existir uma coluna chamada  'codproduto', motivo do erro: {e}")
            
        df.loc[:, 'codproduto'] = df['codproduto'].apply( lambda x: "'" + x.lstrip("'").zfill(18))
        # df['bonuspositivo'] = df['bonuspositivo'].astype(object)
        # df['bonusnegativo'] = df['bonusnegativo'].astype(object)
        df.loc[: ,'bonuspositivo'] = 1.0
        df.loc[: ,'bonusnegativo']=  2.0
        print('tratamento de dados realizada')
        print(df.head(3))

        caminho = os.path.join(os.path.dirname(caminho) + '\\' + 'promocao_produto.csv')
        df.to_csv(caminho, index=False, sep=';')
        return caminho
        

    def main(self, ticket: int) -> dict:
        """
        Executa o fluxo completo: baixa CSV do Acelerato, importa na Zanthus e
        responde o chamado com print do resultado.

        Parâmetro:
            ticket (int): número do chamado no Acelerato com o CSV anexado.

        Retorna:
            dict com sucesso, etapa_falha, mensagem e detalhes.
        """

        # ── ETAPA 1: Baixar CSV do Acelerato ─────────────────────────────────
        print(f"[Etapa 1] Baixando  excel ou CSV do chamado {ticket}...")
        try:
            lista_caminhos = baixar_anexo(ticket, 'xlsx')
            if not lista_caminhos:
                raise Exception('Falha no encontrar o arquivo xlsx')
            caminho = lista_caminhos[-1]
            print(f"[Etapa 1] CSV baixado: {caminho}")
        except:
            try:
                lista_caminhos = baixar_anexo(ticket, 'csv')
                if not lista_caminhos:
                    return self._resultado(False, "download_csv", "Nenhum arquivo CSV encontrado nos anexos do chamado.")
                caminho = lista_caminhos[-1]
                print(f"[Etapa 1] CSV baixado: {caminho}")
            except Exception as e:
                return self._resultado(False, "download_csv", "Erro ao baixar o CSV do Acelerato.", traceback.format_exc())

        # ── ETAPA 2: Upload na Zanthus via Playwright ────────────────────────
        print("[Etapa 2] Iniciando upload na Zanthus...")

        try:
            caminho = self.padroniza_csv(caminho)
        except Exception as err:
            print( f'Falha no padrozinar a tabela {err}')

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, slow_mo=1000)
                context = browser.new_context(accept_downloads=True)
                page = context.new_page()
                page.set_default_timeout(50000)

                self.login_zanthus(page)
                self.zanthus_upload(page, caminho)
                browser.close()

            print("[Etapa 2] Upload concluído.")
        except Exception as e:
            return self._resultado(False, "upload_zanthus", "Erro durante o upload na Zanthus.", traceback.format_exc())

        # ── ETAPA 3: Responder chamado com screenshot ─────────────────────────
        print("[Etapa 3] Respondendo chamado com print...")
        try:
            print_path = "arquivos/print_tela_inteira.png"
            if os.path.exists(print_path):
                responder_com_imagem(ticket, f'✅ Importação de e-books concluída em {self.hoje}', print_path)
            else:
                print("[Etapa 3] Aviso: print não encontrado, pulando resposta com imagem.")
        except Exception as e:
            print(f"[Etapa 3] Aviso: não foi possível responder o chamado. {e}")

        # ── LIMPEZA ───────────────────────────────────────────────────────────
        #  alteração
        self.limpar_arquivos()

        print("csv_book_zanthus enviado\n")
        return self._resultado(True, None, f"Importação de e-books concluída com sucesso em {self.hoje}.")

    def limpar_arquivos(self) -> int:
        """Remove arquivos .csv e .png temporários da pasta 'arquivos'."""
        pasta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arquivos")
        removidos = 0 
        try:
            for arquivo in os.listdir(pasta):
                if arquivo.lower().endswith((".csv", ".png", ".xlsx")):
                    os.remove(os.path.join(pasta, arquivo))
                    print(f"[Limpeza] 🗑️  Removido: {arquivo}")
                    removidos += 1
            print(f"[Limpeza] ✓ {removidos} arquivo(s) removido(s).")
        except Exception as e:
            print(f"[Limpeza] ⚠️  Erro ao limpar (não crítico): {e}")
        return removidos

if __name__ == "__main__":
    # resultado = BookZanthus().main(129566)
    # resultado = BookZanthus().main(124318)
    # print(resultado)
    pass



