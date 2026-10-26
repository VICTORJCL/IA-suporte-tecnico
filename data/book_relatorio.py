import os
import traceback
from datetime import date, datetime
from time import sleep
from typing import TypedDict

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv

# # ─── Carrega variáveis de ambiente ───────────────────────────────────────────
# caminho_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
# load_dotenv(caminho_env)


class ResultadoExecucao(TypedDict):
    """Estrutura de retorno padronizada para uso como tool de IA."""
    sucesso: bool          # True = tudo ok | False = falhou
    etapa: str             # Qual etapa estava sendo executada quando falhou (ou 'concluído')
    mensagem: str          # Resumo legível do resultado
    arquivo_csv: str       # Caminho do CSV gerado (vazio se falhou antes)
    data: str              # Data de referência do relatório
    erro: str              # Detalhes do erro (vazio se sucesso)
    timestamp: str         # Momento da execução


class BookRelatorio:
    """
    "Atualização CSV Ebooks" — título do chamado designado para IA.
    Automatiza o fluxo completo do relatório diário de E-Book:
      1. Baixa o CSV do Zanthus (sistema de PDV)
      2. Envia o CSV para o painel minipreco (filemanager)

    Retorno de executar():
        ResultadoExecucao (dict) com sucesso, etapa, mensagem, arquivo_csv, data, erro, timestamp.

    limpa os arquivos na pasta arquivos após a execução.
    """

    def __init__(self):
        self.hoje = date.today().strftime("%d/%m/%Y")
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        os.makedirs("arquivos", exist_ok=True)


    # =========================================================================
    # ETAPA 1 — Download do CSV no Zanthus
    # =========================================================================

    def _login_zanthus(self, page):
        """Realiza login no sistema Zanthus."""
        login = os.getenv('LOG_ZEUS')
        senha = os.getenv('SENHA_ZEUS')

        if not login or not senha:
            raise ValueError("Credenciais LOGIN ou SENHA não encontradas no .env")

        print("[Zanthus] Realizando login...")
        page.goto(f"{os.getenv('ZANTHUS_URL')}/manager/cad_voucher_promocional.php5?id_menu=30204")
        page.fill('#USUARIO', login)
        page.fill('#SENHA', senha)
        page.get_by_role("button", name="Entrar").click()
        print("[Zanthus] Login efetuado.")

    def _download_csv(self, page, data_ini: str, data_fin: str) -> str:
        """Navega até o relatório, aplica datas e faz download do CSV. Retorna o caminho local."""
        page.goto(f"{os.getenv('ZANTHUS_URL')}/manager/relatorio_dinamico_sel.php5?id_menu=614")
        sleep(3)

        page.locator('a').filter(has_text="PDVT-Vendas E-Book").click()
        page.locator(".control__indicator").first.click()  # todas as lojas

        # Data início
        dt1 = page.locator('input[name="m00af_INI"]')
        dt1.fill(data_ini)
        sleep(0.5)
        dt1.press('Enter')
        sleep(1)

        # Data fim
        dt2 = page.locator('input[name="m00af_END"]')
        dt2.fill(data_fin)
        sleep(0.5)
        dt2.press('Enter')
        sleep(1)

        # Dispara o download
        with page.expect_download() as download_info:
            page.locator('''//i[@onclick="MostraRelatorio('CSV');"]''').click()

        download = download_info.value
        caminho_destino = os.path.join("arquivos", download.suggested_filename)
        download.save_as(caminho_destino)

        print(f"[Zanthus] ✓ Arquivo salvo em: {caminho_destino}")
        return caminho_destino

    def _etapa_baixar(self) -> str:
        """Abre o browser, faz login no Zanthus e baixa o CSV do dia. Retorna o caminho do arquivo."""
        print("\n=== ETAPA 1: Baixando CSV do Zanthus ===")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, slow_mo=1000)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()
            page.set_default_timeout(50000)

            self._login_zanthus(page)
            caminho = self._download_csv(page, self.hoje, self.hoje)
            sleep(5)

        print("=== ETAPA 1: Concluída ===\n")
        return caminho

    # =========================================================================
    # ETAPA 2 — Upload do CSV no painel minipreco
    # =========================================================================

    def _login_painel(self, page):
        """Realiza login no painel minipreco."""
        login = os.getenv('LOGIN_S')
        senha = os.getenv('SENHA_S')

        if not login or not senha:
            raise ValueError("Credenciais LOGIN_S ou SENHA_S não encontradas no .env")

        print("[Painel] Realizando login...")
        page.goto(f"{os.getenv('PAINEL_URL')}/")
        page.get_by_role("textbox", name="Enter username").fill(login)
        page.get_by_role("textbox", name="Password").fill(senha)
        sleep(1)
        page.get_by_role("button", name="Sign In").click()
        sleep(4)
        print("[Painel] Login efetuado.")

    def _navegar_pasta_cupons(self, page):
        """Navega até a pasta de cupons no filemanager do painel."""
        # page.get_by_role("link", name=" Websites ").click()
        page.goto(f"{os.getenv('PAINEL_URL')}/websites/listWebsites")
        sleep(3)
        # page.get_by_role("link", name="List Websites").click()
        sleep(2)
        page.get_by_role("link", name="Filemanager").nth(2).click()
        sleep(2)
        page.locator(".list-group-item > a").first.click()
        sleep(2)
        page.locator(".list-group > li:nth-child(5) > a").first.click()
        sleep(2)
        page.get_by_role("link", name="cupons").click()
        sleep(2)

    def _upload_arquivo(self, page, caminho: str):
        """Faz o upload do arquivo CSV na pasta cupons."""
        print(f"[Painel] Enviando arquivo: {caminho}")
        page.get_by_role("link", name="Upload").click()
        sleep(2)
        page.locator("#uploadControlMultiple").set_input_files(caminho)
        sleep(3)
        page.get_by_role("button", name="Upload all").click()
        sleep(9)
        print("[Painel] ✓ Upload concluído.")

    def _etapa_enviar(self, caminho: str):
        """Abre o browser, faz login no painel e envia o CSV."""
        print("\n=== ETAPA 2: Enviando CSV para o Painel ===")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=1500)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()
            page.set_default_timeout(50000)

            self._login_painel(page)
            self._navegar_pasta_cupons(page)
            self._upload_arquivo(page, caminho)

        print("=== ETAPA 2: Concluída ===\n")

    # =========================================================================
    # LIMPEZA — Remove arquivos CSV temporários
    # =========================================================================

    def _limpar_arquivos(self) -> int:
        """Remove todos os arquivos .csv da pasta 'arquivos'. Retorna a quantidade removida."""
        pasta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arquivos")
        removidos = 0
        try:
            for arquivo in os.listdir(pasta):
                if arquivo.lower().endswith(".csv"):
                    caminho_arq = os.path.join(pasta, arquivo)
                    os.remove(caminho_arq)
                    print(f"[Limpeza] 🗑️  Removido: {arquivo}")
                    removidos += 1
            print(f"[Limpeza] ✓ {removidos} arquivo(s) removido(s).")
        except Exception as e:
            print(f"[Limpeza] ⚠️  Erro ao limpar arquivos (não crítico): {e}")
        return removidos


    # =========================================================================
    # PONTO DE ENTRADA PRINCIPAL
    # =========================================================================

    def executar(self) -> ResultadoExecucao:
        """
        Executa o fluxo completo: download → upload.

        Retorna um dicionário ResultadoExecucao com:
          - sucesso (bool): True se tudo correu bem
          - etapa (str): etapa atual ou 'concluído'
          - mensagem (str): resumo legível
          - arquivo_csv (str): caminho do arquivo gerado
          - data (str): data de referência
          - erro (str): detalhes do erro se falhou
          - timestamp (str): momento da execução
        """
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        arquivo_csv = ""
        etapa_atual = "inicialização"

        print(f"📅 Data de hoje: {self.hoje}")

        try:
            # ── Etapa 1: Download ──────────────────────────────────────────
            etapa_atual = "download_zanthus"
            arquivo_csv = self._etapa_baixar()

            # ── Etapa 2: Upload ────────────────────────────────────────────
            etapa_atual = "upload_painel"
            self._etapa_enviar(arquivo_csv)

            # ── Limpeza dos arquivos temporários ───────────────────────────
            etapa_atual = "limpeza"
            self._limpar_arquivos()

            # ── Sucesso ────────────────────────────────────────────────────
            print("✅ Processo concluído com sucesso!")
            return ResultadoExecucao(
                sucesso=True,
                etapa="concluído",
                mensagem=f"CSV do dia {self.hoje} baixado e enviado com sucesso.",
                arquivo_csv=arquivo_csv,
                data=self.hoje,
                erro="",
                timestamp=timestamp,
            )

        except ValueError as e:
            # Erros de configuração (.env incompleto, credenciais ausentes)
            msg_erro = f"[{etapa_atual}] Erro de configuração: {e}"
            print(f"❌ {msg_erro}")
            return ResultadoExecucao(
                sucesso=False,
                etapa=etapa_atual,
                mensagem="Falha por configuração incorreta. Verifique o arquivo .env.",
                arquivo_csv=arquivo_csv,
                data=self.hoje,
                erro=msg_erro,
                timestamp=timestamp,
            )

        except PlaywrightTimeoutError as e:
            # Timeout ao interagir com o browser (elemento não encontrado, página lenta)
            msg_erro = f"[{etapa_atual}] Timeout no browser: {e}"
            print(f"❌ {msg_erro}")
            return ResultadoExecucao(
                sucesso=False,
                etapa=etapa_atual,
                mensagem="Timeout ao interagir com o sistema. Página pode estar lenta ou elemento não encontrado.",
                arquivo_csv=arquivo_csv,
                data=self.hoje,
                erro=msg_erro,
                timestamp=timestamp,
            )

        except Exception as e:
            # Qualquer outro erro inesperado
            msg_erro = f"[{etapa_atual}] Erro inesperado: {e}\n{traceback.format_exc()}"
            print(f"❌ {msg_erro}")
            return ResultadoExecucao(
                sucesso=False,
                etapa=etapa_atual,
                mensagem=f"Erro inesperado na etapa '{etapa_atual}'. Veja o campo 'erro' para detalhes.",
                arquivo_csv=arquivo_csv,
                data=self.hoje,
                erro=msg_erro,
                timestamp=timestamp,
            )


if __name__ == "__main__":
    resultado = BookRelatorio().executar()
    print("\n── Resultado final ──────────────────────────")
    for chave, valor in resultado.items():
        print(f"  {chave}: {valor}")
