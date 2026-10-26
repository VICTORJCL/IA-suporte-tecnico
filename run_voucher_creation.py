from data.tools import voucher_tools

payload = [{
    'quantidade_valor': [5, 30],
    'valor_ou_poncentagem': 1,
    'lojas_param': ['303'],
    'data_vencimento_param': '04/06/2026',
    'Nome_do_voucher': 'voucher_30_loja_303_2026'
}]

print('Iniciando criação de vouchers com payload:', payload)
res = voucher_tools(payload)
print('Resultado da criação:', res)
