- Apenas a NF-e de saída ligada a entregas (por meio do
  `stock_picking_invoice_link`) recebe o local de retirada calculado.
  Entregas de vários depósitos com endereços diferentes deixam o campo
  vazio, para preenchimento à mão.
- O local de retirada precisa ter CNPJ ou CPF próprio: um endereço filho
  que usa o CNPJ da empresa mãe é recusado.
- As regras de cadastro do CNPJ/CPF do local de retirada (F02-10, F02-20)
  são conferidas apenas pela SEFAZ.
