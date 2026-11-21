- O percentual de ajuste da base do ISSQN (`pAjusteBCISSQN`, regra
  E0453) não é informado: a linha fiscal tem apenas um valor de dedução.
- As regras que dependem dos parâmetros municipais ou de cadastros
  nacionais ficam a cargo do ADN: E0436 (MEI), E0445 (regime especial de
  tributação), E0448 (benefício de isenção municipal), E0437
  (classificação IBS/CBS sem tributação), E0449 a E0452 e E0455 (situação
  do convênio do município e serviços do Simples Nacional), E0444,
  E0446, E0447 e E0454 (parâmetros municipais do serviço), E0466 (código
  IBGE), E0478 a E0488 (cadastro do fornecedor) e E1538 (NIF de
  fornecedor estrangeiro).
- Apenas a primeira linha da NFS-e é informada, como no
  `l10n_br_nfse_nacional`, então a dedução do ISSQN é a dessa linha.
- Os campos estão apenas no formulário do documento fiscal; o formulário
  da fatura do `l10n_br_account` não os mostra.
