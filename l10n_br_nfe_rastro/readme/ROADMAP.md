- Os grupos são preenchidos pelo assistente de faturamento da
  separação. Faturas criadas de outras formas (a partir de um pedido de
  venda, à mão) podem chamar `account.move.line._fill_nfe40_rastro()` ou
  ter os grupos digitados.
- O código de agregação (`cAgreg`) não é preenchido automaticamente.
- A importação de uma NF-e recebida mantém seus lotes na linha do
  documento fiscal, mas não cria os lotes de estoque do recebimento.
