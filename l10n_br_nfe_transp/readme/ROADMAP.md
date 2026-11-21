- O veículo não é levado do pedido de venda nem da entrega para a
  fatura: é escolhido no documento fiscal (ou calculado a partir da
  transportadora).
- A extensão opcional da regra X02-20 às operações internas entre
  municípios diferentes (a critério de cada UF) não é aplicada.
- A escolha entre veículo/reboques, vagão (`vagao`) e balsa (`balsa`)
  não é tratada: vagão e balsa não são preenchidos.
- O CFOP do frete da retenção de ICMS não é conferido contra a tabela de
  CFOP do portal da NF-e (regra X16-10, rejeição 722).
- A retenção de ICMS é digitada: não é calculada a partir da compra do
  serviço de frete.
