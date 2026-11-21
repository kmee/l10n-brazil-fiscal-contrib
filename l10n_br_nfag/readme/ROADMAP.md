## Transmissão

- Os WSDL da NFAg só são servidos a quem apresenta certificado de cliente, e
  não foram lidos: os namespaces (`http://www.portalfiscal.inf.br/NFAg/wsdl/`
  seguido do serviço) e os métodos (`NFAgRecepcao`, `NFAgRecepcaoEvento`,
  `NFAgConsultaNF` e `NFAgStatusServicoNF`) seguem o MOC NFAg 1.00l, Visão
  Geral. Conferir com o WSDL na primeira transmissão em homologação.
- Levar o cliente (`nfag_client`) para a `nfelib`, ao lado dos clientes de CT-e
  e MDF-e, junto com os bindings que hoje estão no `l10n_br_nfag_spec`.
- Consulta da situação e do status do serviço pela tela (o cliente já tem
  `consulta_nfag` e `status_servico`), regra de prazo do cancelamento (120
  horas do mês anterior, regra L11) e o evento de liberação de prazo.

## Leiaute

- Faturamento por terceiro, conjunto, agregado e agregador (`tpFat` 2 a 5,
  grupos `infPAA`, `gFatConjunto` e `gAgregadora`, NT 2026.004 v1.01) e NFAg
  de substituição (`finNFAg` 3, grupo `gSub`): hoje só a NFAg normal
  (`tpFat` 1, `finNFAg` 0).
- Contingência off-line (`tpEmis` 2): `dhCont`, `xJust` e o parâmetro `sign`
  do QR Code (MOC NFAg 1.00l, Visão Geral, itens 9 e 11).
- Valor líquido do item e do total (`vItemLiq`, `vProdLiq`, NT 2026.004
  v1.01), fator de poluição (`fatorPoluicao`, regra G70), indicador de
  devolução com a chave da NFAg anterior (`indDevolucao`, `chNFAgAnt`, regra
  G47), tarifas por período (`gTarif`), medição do item (`gMedicao`),
  pagamento antecipado, processo referenciado (`gProcRef`), PIX (`gPIX`),
  endereço de correspondência, qualidade da água (`gQualiAgua`), vinculação de
  pagamento (`pgtoVinc`, NT 2026.001), autorizados ao XML (`autXML`) e
  responsável técnico (`gRespTec`).
- Taxas de fiscalização de serviço e de uso (`TFS`, `TFU`): o motor fiscal não
  as calcula e os totais saem zerados.
- IBS e CBS: IBS municipal (hoje exportado zerado, como no `l10n_br_nf3e`),
  estorno de crédito (`gEstornoCred`), diferimento, devolução de tributos,
  tributação regular, compras governamentais (`gCompraGov`) e doação
  (`indDoacao`).

## Regras de negócio

- Validar o `cClass` pela tabela de classificação de itens do Portal NFAg
  (regras G69 e G71 a G73) e trazer a unidade de medida e a classificação
  padrão do produto.
- Cadastro da ligação e dos medidores no cliente, em vez de no documento, e o
  histórico de consumo montado a partir das NFAg anteriores da mesma ligação.
- DANFAG (MOC NFAg, Anexo II) e importação do XML da NFAg.
