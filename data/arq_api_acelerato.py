import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv,dotenv_values
import re
import pandas as pd
from time import sleep
import base64


from pathlib import Path
from data.sistemas import ACELERATO_EMAIL_SOLICITANTE, ACELERATO_URL

# Configuração de ambiente
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / '.env'
load_dotenv(dotenv_path=ENV_PATH)
for key, value in dotenv_values(ENV_PATH).items():
    if value is not None:
        os.environ[key] = value

EMAIL = os.getenv('EMAIL')
TOKEN = os.getenv('TOKEN')
TIMEOUT_EM_SEGUNDOS = 30


def get_chamados_for_API():
    '''
    #Verifica todos os Chamados do acelerato
    ##Essa é UMA API que retorna atualizado todos os chamados do acelerato.
    * Deve ser chamada uma vez e aguardar o retorno.
    '''

    EQUIPE_TECNOLOGIA_ID = '19'
    BASE_URL = f'{ACELERATO_URL}/api/publica/v2/chamados'

    #  parâmetros
    params = {
        'equipes' : [EQUIPE_TECNOLOGIA_ID],
        'size' : 100,
        'status': 'PENDENTES'
    }

    # params = {
    # 'equipes': [39],          
    # 'status': 'PENDENTES',    
    # 'agente': 8,              
    # 'etapas': [193],          
    # }

    #  base da API
    response = requests.get(
        BASE_URL,
        timeout=TIMEOUT_EM_SEGUNDOS,
        auth=HTTPBasicAuth(EMAIL,TOKEN),
        params=params,
    )

    chamados= response.json()
    todos_chamados = []

    #  variáveis úteis
    # response.status_code
    # response.text

    filtros = ['ticketKey','titulo','solicitantes','descricao','agente']
    chamados_filtrados = [{k: chamado.get(k) for k in filtros} for chamado in response.json()]


    if response.status_code == 200:
        for chamado in response.json():
            
            agente=chamado['agente']['nome']  if chamado.get('agente') else ''
            agente_key=chamado['agente']['usuarioKey']  if chamado.get('agente') else None
            descricao= chamado['descricao']  if chamado.get('descricao') else ''

            todos_chamados.append({
                'ticketKey': chamado['ticketKey'],
                'titulo': chamado['titulo'],
                'solicitantes' : chamado['solicitantes'][0]['nome'],
                'agente' : agente,
                'agenteKey' : agente_key,
                'descricao': re.sub(r'</?(p|br)>|\n', '', descricao).strip()
            })

    else:
        print("Erro ao consultar chamados:", response.status_code)
    
    # print(response.text)
    return todos_chamados

# get_chamados_for_API()







def criar_chamado_acelerato( titulo, descricao):
    url = f"{ACELERATO_URL}/api/publica/chamados"
    
    headers = {
        "Content-Type": "application/json"
    }

    # TITULO = "Título de teste"
    # DESCRICAO = "Esse chamado foi criado via API."
    # CATEGORIA_KEY = 1
    # EMAIL_SOLICITANTE = EMAIL

    payload = {
        "titulo": titulo,
        "descricao": descricao,
        "categoria": {
            "categoriaKey": 0
        },
        "solicitante": {
            "email": ACELERATO_EMAIL_SOLICITANTE
        }
    }
    response = requests.post(
        url,
        timeout=TIMEOUT_EM_SEGUNDOS,
        headers=headers,
        auth=HTTPBasicAuth(EMAIL, TOKEN),
        json=payload
    )
    # Opcional: lança exceção se status não for sucesso
    # response.raise_for_status()
    return print(response.status_code, 'chamado criado') # retorna o chamado criado (ou erro detalhado)

# criar_chamado_acelerato(titulo='teste', descricao='teste')

def validar_chamado_acelerato(ticketKey):
    """Coloca o chamado em validação na API do Acelerato  Adiciona a IA como Agente"""
    url = f"{ACELERATO_URL}/api/publica/chamados/{ticketKey}"
    payload = {"kanbanStatus": {"kanbanStatusKey": 39}, "agente":{"usuarioKey":822}}
    response = requests.put(url, timeout=TIMEOUT_EM_SEGUNDOS, auth=HTTPBasicAuth(EMAIL, TOKEN), headers={"Content-Type": "application/json"}, json=payload)
    print(f"Status: {response.status_code}", "Chamado em Validação!" if response.status_code in [200, 201, 204] else f"Erro: {response.text}")
    # "kanbanStatusKey": 39 = status de atendimento
    # "kanbanStatusKey": 19 = status de validação 
# def responder_chamado_acelerato(ticketKey, resposta):
#     """
#     Responde a um chamado adicionando um comentário.
#     - /api/publica/tickets/{ticketKey}/comentarios (SEM /v2/)

#     """
#     url = f"{ACELERATO_URL}/api/publica/tickets/{ticketKey}/comentarios"
#     auth = HTTPBasicAuth(EMAIL, TOKEN)
#     headers = {"Content-Type": "application/json"}
#     payload = {
#         "texto": resposta,
#         "privado": False
#     } 
#     response = requests.post(url, timeout=TIMEOUT_EM_SEGUNDOS, json=payload, headers=headers, auth=auth)

#     if response.status_code in [200, 201, 204]:
#         return print("[OK] Resposta enviada com sucesso!")
#     else:
#         print(f'[ERRO] Falha ao enviar comentario')
#         print(f'  Status HTTP: {response.status_code}')
#         print(f'  Endpoint: {url}')
#         print(f'  Resposta: {response.text}')
#         return None

# responder_chamado_acelerato(ticketKey=120742, resposta='teste')

def responder_chamado_acelerato(ticketKey, resposta):
    
    url = f"{ACELERATO_URL}/api/publica/tickets/{ticketKey}/comentarios"
    auth = HTTPBasicAuth( EMAIL, TOKEN)
    headers = {"Content-Type": "application/json"}
    payload = {
        "texto": resposta,
        "usuarioKey": 822,
        "privado": False,
    } 

    response = requests.post(url, timeout=TIMEOUT_EM_SEGUNDOS, json=payload, headers=headers, auth=auth)

    #adicionado Status em Validação e Se adiciona como agente.
    validar_chamado_acelerato(ticketKey)

    if response.status_code in [200, 201]:
        print("resposta enviada")
        return response.status_code
    else:
        print('Erro ao enviar', response.status_code)
        return None

# responder_chamado_acelerato(ticketKey=123186, resposta='teste')
def responder_com_imagem(ticketKey, texto, caminho_imagem):
    # Converte a imagem para base64
    with open(caminho_imagem, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode("utf-8")
    # Monta o HTML com a imagem embutida
    corpo_html = f"""
        <h1>{texto}</h1>
        <img src="data:image/png;base64,{img_base64}" />
    """
    url = f"{ACELERATO_URL}/api/publica/tickets/{ticketKey}/comentarios"
    payload = {
        "texto": corpo_html,
        "usuarioKey": 822,
        "privado": False,
    }
    response = requests.post(url, timeout=TIMEOUT_EM_SEGUNDOS, json=payload, headers={"Content-Type": "application/json"}, auth=HTTPBasicAuth(EMAIL, TOKEN))
    validar_chamado_acelerato(ticketKey)
    
    print("OK" if response.status_code in [200, 201] else f"Erro: {response.status_code}")




def concluir_chamado_acelerato(ticketKey):
    """ 
    Conclui um chamado na API do Acelerato
    parâmetro:
    * ticketKey: ID do chamado a ser concluído
    """
    url = f"{ACELERATO_URL}/api/publica/chamados/{ticketKey}"
    payload = {"kanbanStatus": {"kanbanStatusKey": 15}}
    response = requests.put(url, timeout=TIMEOUT_EM_SEGUNDOS, auth=HTTPBasicAuth(EMAIL, TOKEN), headers={"Content-Type": "application/json"}, json=payload)
    return print(f"Status: {response.status_code}", "Chamado concluído!" if response.status_code in [200, 201, 204] else f"Erro: {response.text}")

# concluir_chamado_acelerato(110426)

def consultar_anexoKey(ticketKey, tipo_arquivo):
    url = f"{ACELERATO_URL}/api/publica/tickets/{ticketKey}/anexos"
    url_comentário = f"{ACELERATO_URL}/api/publica/v2/tickets/{ticketKey}/comentarios"
    auth = HTTPBasicAuth(EMAIL, TOKEN)
    response = requests.get(url, timeout=TIMEOUT_EM_SEGUNDOS, auth=auth)

    if response.status_code == 200:
        return [
            (anexo.get('anexoKey'), anexo.get('nomeCompleto')) 
            for anexo in response.json() 
            if anexo.get('nomeCompleto', '').lower().endswith(tipo_arquivo.lower())
        ]
    else:
        print('Erro ao consultar anexos:', response.status_code)
        return []

# consultar_anexoKey(113010)
# consultar_anexoKey(123186)

# def baixar_anexo(ticketKey, anexoKey, nome_arquivo):
def baixar_anexo(ticketKey, tipo_arquivo):
    lista_arquivos = consultar_anexoKey(ticketKey, tipo_arquivo)
    
    if not lista_arquivos:
        print(f"Nenhum arquivo '{tipo_arquivo}' encontrado.")
        return []

    pasta_arquivos = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'arquivos')
    os.makedirs(pasta_arquivos, exist_ok=True)
    
    caminhos_baixados = []
    auth = HTTPBasicAuth(EMAIL, TOKEN)

    for anexoKey, nome_arquivo in lista_arquivos:
        url = f"{ACELERATO_URL}/api/publica/tickets/{ticketKey}/anexos/{anexoKey}"
        response = requests.get(url, timeout=TIMEOUT_EM_SEGUNDOS, auth=auth)
        
        if response.status_code == 200:
            caminho_arquivo = os.path.join(pasta_arquivos, nome_arquivo)
            with open(caminho_arquivo, "wb") as f:
                f.write(response.content)
            print(f"Arquivo '{nome_arquivo}' baixado com sucesso!")
            caminhos_baixados.append(caminho_arquivo)
        else:
            print(f"Erro ao baixar '{nome_arquivo}':", response.status_code)
            
    return caminhos_baixados
# baixar_anexo(113010, 93753, 'Teste.xlsx')
# baixar_anexo(123186, 'csv')


def anexar_arquivo_comentario(ticketKey, ticketComentarioKey, caminho_arquivo):
    """
    Anexa um arquivo a um comentário específico no Acelerato.
    """
    url = f"{ACELERATO_URL}/api/publica/tickets/{ticketKey}/comentarios/{ticketComentarioKey}/anexos"
    auth = HTTPBasicAuth(EMAIL, TOKEN)
    
    if not os.path.exists(caminho_arquivo):
        print(f"Erro: Arquivo não encontrado em {caminho_arquivo}")
        return False

    with open(caminho_arquivo, "rb") as f:
        # O Acelerato geralmente espera o campo 'arquivo' ou 'file'
        files = {"arquivo": f}
        response = requests.post(url, timeout=TIMEOUT_EM_SEGUNDOS, auth=auth, files=files)
        
    if response.status_code in [200, 201]:
        print(f"Arquivo {os.path.basename(caminho_arquivo)} anexado com sucesso!")
        return True
    else:
        print(f"Erro ao anexar arquivo: {response.status_code} - {response.text}")
        return False

# Exemplo de teste solicitado:
# ticket = 123186
# comentario_id = 148815

# anexar_arquivo_comentario(ticket, comentario_id, caminho_teste)

def baixar_anexo_comentário(ticketKey, ticketComentarioKey, anexoKey,  nome_arquivo):
    url = f"{ACELERATO_URL}/api/publica/tickets/{ticketKey}/comentarios/{ticketComentarioKey}/anexos/{anexoKey}"
    auth = HTTPBasicAuth(EMAIL, TOKEN)
    response = requests.get(url, timeout=TIMEOUT_EM_SEGUNDOS, auth=auth)
    if response.status_code == 200:
        with open(nome_arquivo, "wb") as f:
            f.write(response.content)
        print("Arquivo baixado com sucesso!")
    else:
        print("Erro ao baixar arquivo:", response.status_code, response.text)

# baixar_anexo_comentário(113010, 135176, 63000, 'Teste.pdf')



def consultar_informações_chamado(TICKET_KEY):
    url = f"{ACELERATO_URL}/api/publica/v2/chamados/{TICKET_KEY}"
    auth = HTTPBasicAuth(EMAIL, TOKEN)

    response = requests.get(url, timeout=TIMEOUT_EM_SEGUNDOS, auth=auth)

    if response.status_code == 200:
        chamado = response.json()
        print(chamado)  # Todas as informações do chamado
    else:
        print("Erro:", response.status_code, response.text)



def get_chamado_e_comentario(ticket_Key):
    url_chamado = f"{ACELERATO_URL}/api/publica/v2/chamados/{ticket_Key}"
    url_comentário = f"{ACELERATO_URL}/api/publica/v2/tickets/{ticket_Key}/comentarios"
    auth = HTTPBasicAuth(EMAIL, TOKEN)

    response_chamado = requests.get(url_chamado, timeout=TIMEOUT_EM_SEGUNDOS, auth=auth).json()
    response_comentário = requests.get(url_comentário, timeout=TIMEOUT_EM_SEGUNDOS, auth=auth).json()

    

    select_info = {
        'Numero chamado': response_chamado['ticketKey'],
        'titulo' : response_chamado['titulo'],
        'descricao' : re.sub(r'</?(?:body|html|head|p|br)>|\n', '' ,response_chamado['descricao']).strip(),
        'comentários': [ {x['usuario']['nome'] : x['texto']}
                        for x in response_comentário
                        if response_comentário ] }

    return select_info




def _limpar_html(texto: str) -> str:
    """Limpa HTML de um texto de comentário/descrição preservando URLs de imagem."""
    # 1. Remove imagens base64 embutidas (evita input gigante na IA)
    texto = re.sub(r'data:image/[^;]+;base64,[A-Za-z0-9+/=\s]+', '[imagem-base64-removida]', texto)
    # 2. Converte <img src="URL"> em [imagem: URL] (preserva o link para a IA acessar)
    texto = re.sub(r'<img[^>]*\bsrc=["\']([^"\']+)["\'][^>]*>', r'[imagem: \1]', texto)
    # 3. Remove tags <a> e </a> mas mantém o conteúdo interno
    texto = re.sub(r'</?a[^>]*>', '', texto)
    # 4. Remove demais tags HTML comuns (sem atributos relevantes)
    texto = re.sub(r'</?(?:body|html|head|p|b|strong|i|em|div|span|h[1-6]|ul|ol|li|table|tr|td|th|thead|tbody|hr)[^>]*>', '', texto)
    # 5. Normaliza quebras de linha e espaços
    texto = re.sub(r'\s+', ' ', re.sub(r'\n|</?br>', ' ', texto))
    return texto.strip()


def get_comentarios_raw(ticket_key):
    """
    Retorna lista de comentários do chamado com campos essenciais:
    - comentarioKey: identificador único do comentário
    - usuarioKey: identificador do usuário que fez o comentário
    - nome: nome do usuário
    - texto: conteúdo do comentário (limpo de HTML)
    """
    url = f"{ACELERATO_URL}/api/publica/v2/tickets/{ticket_key}/comentarios"
    auth = HTTPBasicAuth(EMAIL, TOKEN)
    response = requests.get(url, timeout=TIMEOUT_EM_SEGUNDOS, auth=auth)

    if response.status_code != 200:
        print(f"Erro ao buscar comentários do chamado #{ticket_key}: {response.status_code}")
        return []

    comentarios = response.json()
    resultado = []
    for c in comentarios:
        texto_limpo = _limpar_html(c.get('texto', ''))

        resultado.append({
            'comentarioKey': c.get('ticketComentarioKey'),
            'usuarioKey': c.get('usuario', {}).get('usuarioKey'),
            'nome': c.get('usuario', {}).get('nome', 'Desconhecido'),
            'texto': texto_limpo,
        })
    return resultado


def verificar_status_chamado(ticket_key):
    """
    Retorna o status do chamado: {'deletado': bool, 'concluido': bool, 'is_agente_ia': bool}
    """
    url = f"{ACELERATO_URL}/api/publica/v2/chamados/{ticket_key}"
    auth = HTTPBasicAuth(EMAIL, TOKEN)
    response = requests.get(url, timeout=TIMEOUT_EM_SEGUNDOS, auth=auth)

    if response.status_code != 200:
        return {'deletado': True}

    chamado = response.json()
    
    # Se o chamado foi movido para a lixeira, consideramos como deletado
    if chamado.get('lixeira'):
        return {'deletado': True}

    status_key = chamado.get('kanbanStatus', {}).get('kanbanStatusKey')
    agente = chamado.get('agente')
    agente_key = agente.get('usuarioKey') if agente else None

    return {
        'deletado': False,
        'concluido': status_key == 15,
        'is_agente_ia': agente_key == 822
    }


#  iniciando testes e lógica
def get_arquivo_chamado_comentario(ticket_Key):
    # global df
    url_chamado = f"{ACELERATO_URL}/api/publica/v2/chamados/{ticket_Key}"
    url_comentário = f"{ACELERATO_URL}/api/publica/v2/tickets/{ticket_Key}/comentarios"
    url_anexos = f"{ACELERATO_URL}/api/publica/tickets/{ticket_Key}/anexos"
    auth = HTTPBasicAuth(EMAIL, TOKEN)

    def consultar_anexos():
        nonlocal auth, url_anexos
        anexos = requests.get(url_anexos, timeout=TIMEOUT_EM_SEGUNDOS, auth=auth).json()
        return anexos

    def baixar_anexo( download_link, nome_arquivo):
        url = f"{ACELERATO_URL}/api/publica{download_link}"
        response = requests.get(url, timeout=TIMEOUT_EM_SEGUNDOS, auth=auth)
        if response.status_code == 200:
            with open(nome_arquivo, "wb") as f:
                f.write(response.content)
            print("Arquivo baixado com sucesso!")
        else:
            print("Erro ao baixar arquivo:", response.status_code, response.text)


    response_chamado = requests.get(url_chamado, timeout=TIMEOUT_EM_SEGUNDOS, auth=auth).json()
    response_comentário = requests.get(url_comentário, timeout=TIMEOUT_EM_SEGUNDOS, auth=auth).json()

    df_lista = []
    palavras_chave= ['atualização ebook','atualização ebooks', 'atualizações ebooks']
    if not  response_chamado.get('titulo').strip().lower() in palavras_chave:
        # ── Pasta absoluta de arquivos (sempre dentro de data/arquivos) ──────────
        pasta_arquivos = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'arquivos')
        os.makedirs(pasta_arquivos, exist_ok=True)

        # ── Limpar arquivos ANTIGOS antes de baixar novos (evita leitura cruzada) ─
        for arq_antigo in os.listdir(pasta_arquivos):
            if arq_antigo.endswith('.xlsx'):
                try:
                    os.remove(os.path.join(pasta_arquivos, arq_antigo))
                    print(f"[limpeza prévia] removido: {arq_antigo}")
                except Exception as e:
                    print(f"[limpeza prévia] erro ao remover {arq_antigo}: {e}")

        #  baixar anexos se for Excel
        anexos = consultar_anexos()
        if anexos:
            count = 0
            for anexo in anexos:
                count += 1
                if anexo['extensao'] == 'xlsx':
                    # baixa o arquivo dentro da pasta data/arquivos
                    caminho_destino = os.path.join(pasta_arquivos, f'Arquivo_{count}.xlsx')
                    baixar_anexo(anexo['downloadLink'], caminho_destino)
                
            sleep(4)
            #  ler anexos — com limite de 50 linhas para não explodir o prompt da IA
            try:
                for arquivo in os.listdir(pasta_arquivos):
                    if arquivo.endswith('.xlsx'):
                        df = pd.read_excel(os.path.join(pasta_arquivos, arquivo))
                        total_linhas = len(df)
                        if total_linhas > 70:
                            print(f"[AVISO] Planilha tem {total_linhas} linhas — truncando para 70 no prompt da IA.")
                            df = df.head(70)
                        df_lista = df.to_markdown(index=False)
                        if total_linhas > 70:
                            df_lista += f"\n\n[AVISO] Exibindo apenas 70 de {total_linhas} linhas. Planilha completa disponível no chamado."
            except Exception as e:
                print("Erro ao ler arquivos:", e)
            finally:
                #  excluir todos os arquivos xlsx após processar (sempre, mesmo com erro)
                for arquivo in os.listdir(pasta_arquivos):
                    if arquivo.endswith('.xlsx'):
                        try:
                            os.remove(os.path.join(pasta_arquivos, arquivo))
                        except Exception as e_rem:
                            print(f"[limpeza] erro ao remover {arquivo}: {e_rem}")


    
    # ------------------
    #  pegar o cpf se tiver

    cpf_lista = [
        campo['valor'] 
        for campo in response_chamado.get('camposPersonalizadosTicket', [])
        if campo.get('nomeCampo') == 'CPF do usuário' 
        and campo.get('valor') 
    ]
        # and str(campo['valor']).strip().isdigit()
        # and len(str(campo['valor']).replace('.','').replace('-','').strip()) == 11

    cpf = cpf_lista[0] if cpf_lista else None
    # ------------------

    select_info = {
                    'Numero chamado': response_chamado['ticketKey'],
                    'titulo' : response_chamado['titulo'],
                    'descricao' : _limpar_html(response_chamado['descricao']),
                    **({'CPF do usuário caso peça alteração de senha' : cpf} if cpf else {}),
                    'comentários': [ {x['usuario']['nome'] : _limpar_html(x['texto'])}
                                    for x in response_comentário
                                    if response_comentário ],
                    **({'Anexos' : df_lista} if df_lista else {}),
                    }

    print(select_info)

    return select_info


# get_arquivo_chamado_comentario(123650)
# get_arquivo_chamado_comentario(124221)

