from pathlib import Path
from playwright.sync_api import sync_playwright
from time import sleep
import os
from dotenv import load_dotenv
from data.sistemas import BLUESOFT_URL

ENV_PATH = Path(__file__).resolve().parent.parent / '.env'


class ChangePassword():
    def __init__(self):
        self.carregamento()

    def carregamento(self):
        load_dotenv(dotenv_path=ENV_PATH)
        self.log_blue = os.getenv('LOG_BLUE')
        self.senha_blue = os.getenv('SENHA_BLUE')

    def loguin_function(self):
        page = self.page
        # Login Bluesoft
        page.goto(f'{BLUESOFT_URL}/menu/334')
        page.wait_for_selector("#j_username")
        page.fill("#j_username", self.log_blue or "")
        page.fill("#j_password", self.senha_blue or "")
        sleep(1)
        page.click("#btnSubmit")
        
        print("[OK] Login Bluesoft realizado")

    def altera_senha(self, cpf: str | int) -> tuple[str, str]:
        page = self.page     
        page.locator("input[name=\"cpfCnpj\"]").fill(str(cpf))
        page.get_by_role("button", name="Buscar").click()
        sleep(2)
        with page.expect_popup() as page2_info:
            page2 = page2_info.value
            page2.get_by_role("link", name="Contatos").click()
            sleep(2)
            email = ""
            try:
                emails = page2.locator("//table[@id='contato']//td[.//span]").all_inner_texts()
                if emails:
                    email = emails[0].split(' ')[0].strip()
            except Exception as e:
                print(f"Erro ao extrair email: {e}")

            # mudar a senha
            page2.get_by_role("link", name="Usuário").click()
            sleep(2)

            login_user = ""
            try:
                login_user = page2.locator('//input[@name="username"]').get_attribute('value') or ""
            except Exception as e:
                print(f"Erro ao pegar login: {e}")
            
            page2.get_by_role("combobox").select_option("APROVADO")

            # Verificar se o checkbox não está marcado antes de marcar
            checkbox_gerar_senha = page2.get_by_role("checkbox", name="Gerar Senha")
            if not checkbox_gerar_senha.is_checked():
                checkbox_gerar_senha.check()
            
            page2.get_by_role("radio", name="Trocar senha no próximo login").check()
            page2.get_by_role("button", name="Salvar").click()
            print("[OK] Senha alterada")
            sleep(4)

            # fechar page 2
            page2.close()

        return email, login_user

    def main(self, list_cpf: list[str | int]) -> list[str]:
        email_lista = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_default_timeout(60000)
            self.page = page
            # ==================== BLUESOFT ====================
            self.loguin_function()

            for cpf in list_cpf:
                try:
                    resultado = self.altera_senha(cpf)
                    email_lista.append(f'Senha enviada para o email. O email e login do usuario é {resultado}')
                except Exception as e:
                    print(f"Erro ao alterar senha para CPF {cpf}: {e}")
                    email_lista.append(f'Erro ao alterar senha para CPF {cpf}: {e}')
            print(email_lista)
            return email_lista