- A nota de empenho e o contrato são digitados: não há vínculo com um
  modelo de compra pública ou de contrato (por exemplo o módulo
  `contract` da OCA).
- Os campos estão no formulário do documento fiscal, não no formulário
  da fatura.
- A importação de uma NF-e recebida mantém o grupo `compra` no registro
  `nfe40_compra`, mas não preenche os três campos do documento.
- As regras ZB02-20 e ZB02-30 (nota de empenho inválida ou desconhecida
  na UF) dependem do cadastro de cada UF e não são conferidas.
