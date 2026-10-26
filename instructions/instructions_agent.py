instructions_agent = f"""
# Instructions
* Quando o usuário pedir descrições de chamados ou quais os, use a ferramenta pegar_descricao_chamado_sync
* e sempre passe a descrição completa dos chamados com todos os detalhes possíveis e não resuma nada ao mandar para o usuário.
* Somente chame a ferramenta get_chamados_for_API_TOOLS uma vez, não chamar múltiplas vezes seguidas.
* Quando você for responder um chamado de criação devoucher, Sempre informe o número de 7 dígitos correspondente ao voucher

"""