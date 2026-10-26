

from .arq_api_acelerato import get_chamados_for_API, responder_chamado_acelerato, criar_chamado_acelerato, get_chamado_e_comentario
# from .Cargas_Agno_playwright import executar_cargas_playwright
from .Cargas_MODIFICADO import executar_cargas_playwright
from .voucher_tool_retorno import voucher_tools_pl
from .derruba_pack import derruba_pack_mainfun
from .ferramenta_altera_senha_bluesoft import ChangePassword
from .book_relatorio import BookRelatorio
from .book_zanthus import BookZanthus
from .carga_lock import CARGA_LOCK
from agente.config import AVISO_DE_NOVA_TENTATIVA
import threading
from functools import wraps

def import_book_zanthus(ticket):
    '''
    # alteração ebooks - título do chamado designado para IA.
    ## o que faz?
        - Essa automação baixa um anexo csv do acelerato com título 'alteração ebooks'
        - importa direto na zanthus para alterações referentes aos ebooks da promoção
        - envia um print diretamente no chamado após a conclusão
    #Parâmetro obrigatório:
    - número do chamado
    '''.strip()
    book = BookZanthus()
    return book.main(ticket)



def book_relatorio():
    """
    "Atualização CSV Ebooks" — título do chamado designado para IA.
    Automatiza o fluxo completo do relatório diário de E-Book:
      1. Baixa o CSV do Zanthus (sistema de PDV)
      2. Envia o CSV para o painel minipreco (filemanager)

    Retorno de executar():
        ResultadoExecucao (dict) com sucesso, etapa, mensagem, arquivo_csv, data, erro, timestamp.

    limpa os arquivos na pasta arquivos após a execução.
    **AÇÃO OBRIGATÓRIA**: Responder chamado informando  se deu certo ou não
    """.strip()
    resultado = BookRelatorio().executar()
    return resultado


def executar_async_e_responder_chamado(func):
    """
    Decorador que executa a função em uma thread separada e 
    automaticamente responde o chamado com o resultado.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extrai o numero_chamado dos kwargs ou args
        numero_chamado = kwargs.get('numero_chamado')
        if not numero_chamado:
            try:
                import inspect
                sig = inspect.signature(func)
                bound = sig.bind_partial(*args, **kwargs)
                numero_chamado = bound.arguments.get('numero_chamado')
            except Exception:
                pass
        
        def executar_e_responder():
            try:
                # Executa a função original
                resultado = func(*args, **kwargs)
                
                # Responde o chamado se existir número de chamado e resultado
                if numero_chamado and resultado:
                    responder_chamado_acelerato_tool(numero_chamado, resultado)
                    
                print('Processo concluído com sucesso')
            except Exception as e:
                print(f'Erro na execução: {e}')
                if numero_chamado:
                    responder_chamado_acelerato_tool(
                        numero_chamado, 
                        f"Erro ao executar: {str(e)}<br>{AVISO_DE_NOVA_TENTATIVA}"
                    )
        
        carga_em_andamento = CARGA_LOCK.locked()

        # Inicia a thread
        thread = threading.Thread(target=executar_e_responder)
        thread.start()

        if carga_em_andamento:
            return (
                "Já existe uma carga em andamento. Esta carga entrou na fila e será executada "
                "automaticamente quando a anterior terminar; o chamado será respondido ao concluir."
            )
        return "Processo de carga iniciado em segundo plano"
    
    return wrapper

def ferramenta_altera_senha_bluesoft(cpf_lista:list[str]):
    """
    **Ferramenta**: Altera senhas de funcionários na Bluesoft.
    
    **Parâmetro**: cpf_lista: list[str] - Ex: ["00000000000", "11111111111"]
    
    **Retorno**: Lista com email+login (sucesso) ou CPF (erro)
    
    **AÇÃO OBRIGATÓRIA**: Responder chamado informando:
    - Usuário receberá email para alterar senha
    - Informar email retornado (sempre)
    - Informar login (apenas se pedido)
    """.strip()
    exe_tool = ChangePassword()
    return exe_tool.main(cpf_lista)


def ferramenta_de_Cargas(conjunto_lojas=None, lojas_especificas=None):
    """
    Executa cargas de atualização de preços.
    Essa é uma ferramenta que deve ser usada quando o usuário pedir 'Carga' deve ser usada passando 1 parâmetro para um conjunto de lojas  ou um parâmetro para lista de lojas específicas
    Essa ferramenta somente deve ser usada UMA VEZ  e deve aguardar o término da execução.
    ES sifgnifa Espírito Santo e PR significa Paraná e SC significa Santa Catarina e RDs significa Rei dos Salvados ou Salvados E uma mesma loja RDs também pode ser MiniPreço.
    # MUITO IMPORTANTE:
    * NUMCA passe mais de um valor de string para o parâmetro de conjunto_lojas, somente pode assumir um dos 6 valores("Lojas PR MiniPreço","Lojas PR Salvados", "Lojas SC Salvados", "Lojas Espírito Santo MiniPreço", "Lojas Minipreço", "Todas as lojas")
    * O valor "Lojas Minipreço" do parâmetro conjunto_lojas, engloba as cargas para PR e ES, use quando pedirem 'carga PR e ES.'
    * Se o usuário pedir carga somente para uma ou 3 lojas específicas, use somente o parâmetro lojas_especificas, exemplo: lojas_especificas=["02"]
    * Ao finalizar essa função, use a ferramenta responder_chamado_acelerato_tool para responder o chamado correspondente ao pedido de voucher se ele existir.

    # IMPORTANTE sobre Quando usar a ferramenta ferramenta_de_Cargas:
    - Chame APENAS UMA VEZ por solicitação do usuário
    - NÃO faça múltiplas chamadas da mesma ferramenta
    - Aguarde o resultado antes de responder
    - Consulte lojas_keys para ver o número da loja e o nome, Exemplo: "Loja de utilização: Serra BR  Referencia: '303'  Nome: MINIPRECO SERRA"
    - Se o usuário pedir cargas, execute UMA VEZ, aguarde o término da execução e informe o resultado
    - Ao finalizar essa função, use a ferramenta responder_chamado_acelerato_tool para responder o chamado correspondente ao pedido de carga se ele existir.
    - Sempre adicione o parâmetro no formato string
    - se for usar o lojas_especificas, passe a numeração exatamente como na descrição, por exemplo: use '04' ao invéz de '4'   
    - se não for usar o parâmetro lojas_especificas, não adicione ele na função, exemplo: ferramenta_de_Cargas(conjunto_lojas="Todas as lojas")
    - se não for usar o parâmetro conjunto_lojas, não adicione ele na função, exemplo: ferramenta_de_Cargas(lojas_especificas=["01", "02", "04"])

    # COMO USAR A FERRAMENTA:
    * Escolha um ou 2 dos parâmetros opcionais
    * Use exatamente os valores strings no parâmetro
    * busque priorizar o parâmetro conjunto de lojas se possível,
    * Ao finalizar a ferramenta, não responda que está iniciando pois já fez isso uma vez, não responda nada.

    # O conjunto_lojas é um atalhao para não precisar digitar todas as lojas na lojas_especificas.
    pode-se acionar todas as lojas usando apenas  a string "Todas as lojas" no parâmetro conjunto_lojas="Todas as lojas", assim não precisa usar o outro parâmetro

    # valores de parâmetros strings key para conjunto de loja: [
     "Lojas PR MiniPreço": ["01","02","04","06","07","08","10","11","12","14","19","20"],
        "Lojas PR Salvados": ["01","02","04","06","08","09","11","14","17","18","19"],
        "Lojas SC Salvados": ["201","202","203","204","208"],
        "Salvados PR SC" : ["01","02","04","06","08","09","11","14","17","18","19","201","202","208"],
        "Lojas Espírito Santo MiniPreço": ["301","303","304","305","307","308"],
        "Lojas Minipreço": ["01","02","04","06","07","08","10","11","12","14","19","20","301","303","304","305","307","308"],
        "Todas as lojas": ["01","02","04","06","07","08","09","10","11","12","14","17","18","19","20","201","202","203","204","208","301","303","304","305","307","308"]
        
    # lojas_especificas (list): É um parâmetro opcional, que pode assumir os seguintes valores Key de string numéricos:
    Aqui a lista de todos dos valores Keys das lojas
    lojas_keys ={
        '01': '1- MINIPRECO SANTA FELICIDADE',
        '02': '2- MINIPRECO TORRES',
        '04': '4- MINIPRECO PINHAIS',
        '06': '6- MINIPRECO PARANAGUA'
        '07': '7- MINIPRECO FANNY  ou LINHA VERDE
        '08': '8- MINIPRECO FAZENDA RIO GRANDE',
        '09': '9- RDS SITIO CERCADO',
        '10': '10- MINIPRECO XAXIM',
        '11': '11- MINIPRECO FAZENDINHA',
        '12': '12- MINIPRECO EXPRESS BOULEVARD',,
        '14': '14- MINIPRECO COLOMBO',
        '17': '17- RDS XAXIM',
        '18': '18- RDS FANNY',
        '19': '19- MINIPRECO ARAUCARIA',
        '20': '20- MINIPRECO BACACHERI',
        '201': '201- RDS BALNEARIO CAMBORIU',
        '202': '202- RDS ITAJAI',
        '207': '207- RDS PRAIA BRAVA',
        '208': '208- RDS JOINVILLE',
        '301': '301- MINIPRECO VILA VELHA',
        '303': '303- MINIPRECO SERRA',
        '304': '304- MINIPRECO VITORIA',,
        '305': '305- MINIPRECO LINHARES',
        '307': '307- MINIPRECO GLORIA',
        '308': '308- MINIPRECO DAY BY DAY',
        '602': '602- DCOR GIFT CRYSTAL',
        '900': '900- LOJA TESTE DE SISTEMA'}

    # EXEMPLOS DE USO:
    ferramenta_de_Cargas(conjunto_lojas="Todas as lojas")
    ferramenta_de_Cargas(conjunto_lojas="Lojas SC Salvados", lojas_especificas=["01", "02", "04"])
    ferramenta_de_Cargas(lojas_especificas=["01", "02", "04"])
    ferramenta_de_Cargas(lojas_especificas="900")
    </lojas_especificas>

    Caso tenha um chamado associado pedindo cargas e você esteja realizando esse chamado, responda o chamado  usando responder_chamado_acelerato_tool
    """.strip()

    # ── Validação de conjunto_lojas ──────────────────────────────────
    CONJUNTOS_VALIDOS = [
        "Lojas PR MiniPreço", "Lojas PR Salvados", "Lojas SC Salvados",
        "Salvados PR SC", "Lojas Espírito Santo MiniPreço",
        "Lojas Minipreço", "Todas as lojas"
    ]
    if conjunto_lojas and conjunto_lojas not in CONJUNTOS_VALIDOS:
        return (
            f"ERRO: '{conjunto_lojas}' não é um valor válido para conjunto_lojas. "
            f"Use EXATAMENTE um dos seguintes valores: {CONJUNTOS_VALIDOS}. "
            f"Se o chamado pede ES/Espírito Santo, use 'Lojas Espírito Santo MiniPreço'. "
            f"Se não tiver certeza, use 'Lojas Minipreço' como padrão."
        )
    if not conjunto_lojas and not lojas_especificas:
        return "ERRO: Passe pelo menos um parâmetro: conjunto_lojas ou lojas_especificas."
    # ────────────────────────────────────────────────────────────────

    resultado = executar_cargas_playwright(
        conjunto_lojas=conjunto_lojas, 
        lojas_especificas=lojas_especificas
    )
    
    return resultado





@executar_async_e_responder_chamado
def ferramenta_de_Cargas_Sem_parar(conjunto_lojas=None, lojas_especificas=None, numero_chamado=None):
    """
    Executa cargas de atualização de preços.
    
    Essa é uma ferramenta que deve ser usada quando o usuário pedir 'Carga' deve ser 
    usada passando 1 parâmetro para um conjunto de lojas ou um parâmetro para lista 
    de lojas específicas e 1 parâmetro para o  numero do chamado.
    
    Essa ferramenta somente deve ser chamada apenas 1 vez, e não deve aguardar conclusão, pois ela vai responder o chamado sozinha quando as cargas finalizarem
    
    ES significa Espírito Santo e PR significa Paraná e SC significa Santa Catarina 
    e RDs significa Rei dos Salvados ou Salvados. Uma mesma loja RDs também pode ser MiniPreço.
    
    # MUITO IMPORTANTE:
    * NUNCA passe mais de um valor de string para o parâmetro de conjunto_lojas, 
      somente pode assumir um dos 6 valores:
      ("Lojas PR MiniPreço", "Lojas PR Salvados", "Lojas SC Salvados", 
       "Lojas Espírito Santo MiniPreço", "Lojas Minipreço", "Todas as lojas")
    * O valor "Lojas Minipreço" do parâmetro conjunto_lojas engloba as cargas para PR e ES, 
      use quando pedirem 'carga PR e ES.'
    * Se o usuário pedir carga somente para uma ou 3 lojas específicas, use somente o 
      parâmetro lojas_especificas, exemplo: lojas_especificas=["02"]
    * nunca responda o chamado de conclusão, essa ferramenta fará sozinha isso quando concluir e sempre passe o número do chamado no parâmetro  numero_chamado
    
    # IMPORTANTE sobre quando usar a ferramenta:
    - Chame APENAS UMA VEZ por solicitação do usuário
    - NÃO faça múltiplas chamadas da mesma ferramenta
    - Aguarde o resultado antes de responder
    - Consulte lojas_keys para ver o número da loja e o nome
    - Sempre adicione o parâmetro no formato string
    - Se for usar lojas_especificas, passe a numeração exatamente como na descrição, 
      por exemplo: use '04' ao invés de '4'
    - Se não for usar o parâmetro lojas_especificas, não adicione ele na função
    - Se não for usar o parâmetro conjunto_lojas, não adicione ele na função
    
    # COMO USAR A FERRAMENTA:
    * Escolha um ou 2 dos parâmetros opcionais das lojas
    * Passe o numero do chamado no parâmetro
    * Use exatamente os valores strings no parâmetro
    * Busque priorizar o parâmetro conjunto de lojas se possível
    
    # Conjuntos de lojas disponíveis:
    {
        "Lojas PR MiniPreço": ["01","02","04","06","07","08","10","11","12","14","19","20"],
        "Lojas PR Salvados": ["01","02","04","06","08","09","11","14","17","18","19"],
        "Lojas SC Salvados": ["201","202","203","204","208"],
        "Salvados PR SC": ["01","02","04","06","08","09","11","14","17","18","19","201","202","208"],
        "Lojas Espírito Santo MiniPreço": ["301","303","304","305","307","308"],
        "Lojas Minipreço": ["01","02","04","06","07","08","10","11","12","14","19","20","301","303","304","305","307","308"],
        "Todas as lojas": ["01","02","04","06","07","08","09","10","11","12","14","17","18","19","20","201","202","203","204","208","301","303","304","305","307","308"]
    }
    
    # Lojas disponíveis (lojas_keys):
    {
        '01': '1- MINIPRECO SANTA FELICIDADE',
        '02': '2- MINIPRECO TORRES',
        '04': '4- MINIPRECO PINHAIS',
        '06': '6- MINIPRECO PARANAGUA',
        '07': '7- MINIPRECO FANNY ou LINHA VERDE',
        '08': '8- MINIPRECO FAZENDA RIO GRANDE',
        '09': '9- RDS SITIO CERCADO',
        '10': '10- MINIPRECO XAXIM',
        '11': '11- MINIPRECO FAZENDINHA',
        '12': '12- MINIPRECO EXPRESS BOULEVARD',
        '14': '14- MINIPRECO COLOMBO',
        '17': '17- RDS XAXIM',
        '18': '18- RDS FANNY',
        '19': '19- MINIPRECO ARAUCARIA',
        '20': '20- MINIPRECO BACACHERI',
        '201': '201- RDS BALNEARIO CAMBORIU',
        '202': '202- RDS ITAJAI',
        '207': '207- RDS PRAIA BRAVA',
        '208': '208- RDS JOINVILLE',
        '301': '301- MINIPRECO VILA VELHA',
        '303': '303- MINIPRECO SERRA',
        '304': '304- MINIPRECO VITORIA',
        '305': '305- MINIPRECO LINHARES',
        '307': '307- MINIPRECO GLORIA',
        '308': '308- MINIPRECO DAY BY DAY',
        '602': '602- DCOR GIFT CRYSTAL',
        '900': '900- LOJA TESTE DE SISTEMA'
    }
    Caso não esteja claro e tenha dúvida de qual parâmetro usar, use conjunto_lojas='Lojas Minipreço'    
    # EXEMPLOS DE USO:
    ferramenta_de_Cargas_Sem_parar(conjunto_lojas="Todas as lojas", numero_chamado=114699)
    ferramenta_de_Cargas_Sem_parar(conjunto_lojas="Lojas SC Salvados", lojas_especificas=["01", "02", "04"], numero_chamado=114699)
    ferramenta_de_Cargas_Sem_parar(lojas_especificas=["01", "02", "04"], numero_chamado=114699)
    ferramenta_de_Cargas_Sem_parar(lojas_especificas=["900"], numero_chamado=114699)
    """.strip()

    # ── Validação de conjunto_lojas ──────────────────────────────────
    CONJUNTOS_VALIDOS = [
        "Lojas PR MiniPreço", "Lojas PR Salvados", "Lojas SC Salvados",
        "Salvados PR SC", "Lojas Espírito Santo MiniPreço",
        "Lojas Minipreço", "Todas as lojas"
    ]
    if conjunto_lojas and conjunto_lojas not in CONJUNTOS_VALIDOS:
        return (
            f"ERRO: '{conjunto_lojas}' não é um valor válido para conjunto_lojas. "
            f"Use EXATAMENTE um dos seguintes valores: {CONJUNTOS_VALIDOS}. "
            f"Se o chamado pede ES/Espírito Santo, use 'Lojas Espírito Santo MiniPreço'. "
            f"Se não tiver certeza, use 'Lojas Minipreço' como padrão."
        )
    if not conjunto_lojas and not lojas_especificas:
        return "ERRO: Passe pelo menos um parâmetro: conjunto_lojas ou lojas_especificas."
    # ────────────────────────────────────────────────────────────────

    resultado = executar_cargas_playwright(
        conjunto_lojas=conjunto_lojas, 
        lojas_especificas=lojas_especificas
    )
    
    return resultado



# ferramenta_de_Cargas_TESTE(lojas_especificas=["900"], numero_chamado=114699)


    # thread = threading.Thread(target=executar_cargas_playwright, args=(conjunto_lojas, lojas_especificas))
    # thread.start()
    # print('continue')





# ferramenta_de_Cargas_assincrona(lojas_especificas=["900"], numero_chamado=114699)
  


def get_chamados_for_API_TOOLS():
    '''
    #Verifica todos os Chamados do acelerato
    ##Essa é UMA API que retorna atualizado todos os chamados do acelerato.
    * Essa ferramenta somente deve ser chamada uma vez, não chamar múltiplas vezes seguidas.
    * Quando usar essa ferramenta, apenas printe todas as informações de retorno em uma formatação melhorada
    '''.strip()
    return get_chamados_for_API()

def responder_chamado_acelerato_tool(ticketKey, resposta):
    """
    Adiciona uma resposta/comentário a um chamado específico no Acelerato.
    IMPORTANTE:
    * Não chame essa ferramenta por conta própria, apenas quando o usuário pedir "responda o chamado". 
    * Essa ferramenta somente deve ser chamada uma vez, não chamar múltiplas vezes seguidas.
    
    Parametros obrigatórios:
        * ticketKey -  número do chamado
        * resposta

    #Tipos de resposta por categoria
    ##Na categoria Voucher os chamados devem ser respondidos no formato Html com as seguintes informações (numero do voucher de 7 dígitos:  ,valor do voucher  ,validade de #####  a  ##### ,lojas )
     - sempre informe o número do voucher e su valor na categoria voucher
    ##Categoria Carga: Carga realizada com sucesso para as lojas...
    """.strip()


    return responder_chamado_acelerato(ticketKey, resposta)



def voucher_tools (parametros_voucher: list[dict]):
  """Cria vouchers promocionais para as lojas 
    
    IMPORTANTE: 
    *Esta ferramenta automatiza a criação de vouchers promocionais no sistema.
    *Use apenas quando o usuário solicitar criação de vouchers.
    * antes de passar os parâmetros se pergunte: Qual a data de hoje? considere a data de hoje a que foi passada nas suas intruções,  se colocar na data de vencimento parâmetro uma data inferior, vai dar erro.
    * Ao finalizar essa função, use a ferramenta responder_chamado_acelerato_tool para responder o chamado correspondente ao pedido de voucher se ele existir.
    * Sempre coloque os parâmetros como uma lista de dicionários


    PARÂMETROS da função é uma lista de dicionários:
    parametros_voucher: lista de dicionários com:
        - 'quantidade_valor': [quantidade, valor] ex: [3, 15]
        - 'valor_ou_poncentagem': 1=valor fixo, 2=porcentagem de desconto
        - 'lojas_param': [numéricos] ou ['PRM','ESM','TUDO','salvados']

        - 'Nome_do_voucher': 'descrição'

      OBS: o mesmo dicionário pode ser usado para vários vouchers que somente muda o valor. Caso precise de voucher com outros parâmetros ou outra loja ou conjunto de lojas, adicione outro dicionário  e a quantidade e valores
    EXEMPLO de 2 vouchers de 15 reais para somente a loja 900:
    [{'quantidade_valor': [2, 15], 'valor_ou_poncentagem': 1, 'lojas_param': [900], 
      'data_vencimento_param': '22/10/2025', 
      'Nome_do_voucher': 'Teste'}]

    ORIENTAÇÕES para cada variável do parâmetro
    - quantidade_valor: Lista com [quantidade, valor] para cada voucher, Exemplo: [[1, 150], [3, 200]] - cria 1 voucher de R$150 e 3 vouchers de R$200
    - parceiro: Nome do parceiro responsável pelo voucher, Exemplo: "Parceiro ABC"
    - valor_ou_poncentagem = 1 : para voucers de valor  Exemplo(- 1 = Valor fixo (ex: R$ 10,00)
    - valor_ou_poncentagem = 2 : para vouchers de percentual de desconto Exemplo(ex: 10%)
  
    - data_vencimento_param: Data de vencimento no formato dd/mm/aaaa. Pode ser no mínimo 1 dia após a data de hoje e não pode ser anterior a data de hoje. verifique a data que está pedindo no chamado e use ela se corresponder as regras. Se não corresponder as regras, deixe por padrão de 1 mês.
    - lojas_param: é uma lista com Códigos das lojas onde o voucher será válido e/ou com códigos especiais, exemplo de voucher válido para todas as lojas mini preço e loja Itajai. lojas_param=[MINI,202], outro exemplo: voucher para  mini preço torres lojas_param=[2] 
      * Opções de conjunto de lojas:
       Códigos especiais:
        - "PRM" = MiniPreço Paraná
        - "PRS" = Salvados Paraná  
        - "SCS" = Salvados Santa Catarina
        - "ES" = MiniPreço Espírito Santo
        - "MINI" = Todas as lojas do MiniPreço (PR+ES)
        - "salvados" = Todos Salvados (PR+SC)
        - "TUDO" = Todas as lojas (Rei dos salvados e Mini Preço)

      * observação,  quando o usuário pedir voucher para usar em qualquer loja do Rei e Mini, entende-se que o código especial deve ser "TUDO"

      * opção de lojas:
        { 1: ' MINIPRECO SANTA FELICIDADE',
          2: 'MINIPRECO TORRES',
          4: 'MINIPRECO PINHAIS',
          6: 'MINIPRECO PARANAGUA'
          7: 'MINIPRECO FANNY  ou LINHA VERDE
          8: 'MINIPRECO FAZENDA RIO GRANDE',
          9: 'RDS SITIO CERCADO',
          10: 'MINIPRECO XAXIM',
          11: 'MINIPRECO FAZENDINHA',
          12: 'MINIPRECO EXPRESS BOULEVARD',,
          14: 'MINIPRECO COLOMBO',
          17: 'RDS XAXIM',
          18: 'RDS FANNY',
          19: 'MINIPRECO ARAUCARIA',
          20: 'MINIPRECO BACACHERI',
          201: 'RDS BALNEARIO CAMBORIU',
          202: 'RDS ITAJAI',
          203: 'RDS BLUMENAU',
          204: 'RDS JARAGUA DO SUL',
          207: 'RDS PRAIA BRAVA',
          208: 'RDS JOINVILLE',
          301: 'MINIPRECO VILA VELHA',
          303: 'MINIPRECO SERRA',
          304: 'MINIPRECO VITORIA',,
          305: 'MINIPRECO LINHARES',
          307: 'MINIPRECO GLORIA',
          308: 'MINIPRECO DAY BY DAY',
          602: 'DCOR GIFT CRYSTAL',
          900: 'LOJA TESTE DE SISTEMA'}

      # Interpretação de voucher para lojas
      - RDS significa Rei dos Salvados que pode ser interpretado como Salvados, se pedirem para todas as lojas RDS ou  totos os salvados, pode adicionar 'salvados' em lojas_param=['salvados'] que esse código adiciona automaticamente todas as numerações das lojas dos salvados
      - Se alguém pedir para (Mini preço + o nome da loja). Ele está pedindo somente para aquela loja e não para todas as lojas mini preço. Exemplo: mini preço linha verde, lojas_param=[7]
  """.strip()
  return voucher_tools_pl(parametros_voucher)



def criar_chamado_acelerato_tool(titulo, descricao):
    """
    Cria um chamado no Acelerato.
    IMPORTANTE:
    * Não chame essa ferramenta por conta própria, apenas quando o usuário pedir exatamente "crie um chamado".
    * Essa ferramenta somente deve ser chamada uma vez, não chamar múltiplas vezes seguidas.
    
    Parametros obrigatórios:
        * titulo: Título do chamado
        * descricao: Descrição do chamado
    """.strip()
    return criar_chamado_acelerato(titulo, descricao)


@executar_async_e_responder_chamado
def derruba_pack(codigo_pack, option_pack, numero_chamado=None):
  '''
  #Essa é uma ferramenta que derruba packs de promoção na Zanthus e tem como parâmetro uma lista de packs
  * CHAME ESSA FERRAMENTA SOMENTE 1 VEZ SE O CHAMADO PEDE DERRUBAR PACK ou INATIVAR PACK, nunca chame múltiplas vezes
  * Essa ferramenta é assíncrona e vai responder o chamado sozinha ao finalizar. NÃO chame a ferramenta de resposta de chamados após executá-la.
  * Sempre adicione e passe o número do chamado no parâmetro 'numero_chamado'.
  * nunca use ferramenta de cargas no chamado de derrubar pack, se pedirem carga sem agendamento no chamado de pack, use a opção option_pack=1
  * nunca invente numeros de codigo_pack, pese somente o que foi descrito no chamado, se não tiver nada, não use essa ferramenta e responda o chamado pedindo para colocar escrito o número dos packs sem ser anexo
  * a própria ferramenta informará no chamado caso não encontre algum Pack
  ##PARÂMETROS OBRIGATÓRIOS:
  ###codigo_pack=list, option_pack= int, numero_chamado=int
  * codigo_pack = uma lista que contém os packs que devem ser derrubados, exemplo: codigo_pack=['17']
  #### option_pack pode assumir valores de 1 ou 2 
  * option_pack=1 é para somente derrupar o pack e lançar carga
  * option_pack=2 usa-se quando pede para derrubar pack para o final do expediente, a carga é realizada na madrugada, essa opção é somente quando pede para fazer no final do expediente. Avise no chamado que o processo foi agendado
  ##Observação:
  * Na descrição do chamado ou no título estiver Derrubar Pack no Fim do Expediente de Hoje, use a ferramenta derruba_pack opção que gera agendamento que é option_pack=2
  '''.strip()

  return derruba_pack_mainfun(codigo_pack, option_pack, numero_chamado=numero_chamado)