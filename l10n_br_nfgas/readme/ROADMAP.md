## Framework

- Levar para o `spec_driven_model` o disparo do
  `_register_remaining_schema_models_hook` para cada esquema empilhado no
  documento fiscal: hoje o hook só roda para o esquema do último módulo que
  estende o documento, e os módulos sem outro modelo concreto (NFCom, BP-e)
  ficam sem as tabelas dos modelos restantes. O documento da NFGas dispara o
  hook para todos os esquemas até lá.

## Transmissão

- Conferir no WSDL dos serviços (servido só com certificado de cliente) o
  namespace e a ação SOAP: o cliente usa os do MOC NFGas 1.00g, Visão Geral
  (`http://www.portalfiscal.inf.br/NFGas/wsdl/<serviço>` e os métodos
  `NFGasRecepcao`, `NFGasRecepcaoEvento`, `NFGasConsultaNF` e
  `NFGasStatusServicoNF`). A transmissão só foi testada contra um autorizador
  simulado.
- Levar o `nfgas_client` para a `nfelib` (`nfelib/nfgas/client`), junto com os
  bindings do `l10n_br_nfgas_spec`.
- Prazo do cancelamento (regra L11, autorização até 120 horas do mês anterior)
  e o evento de liberação de prazo do fisco (240170).
- Contingência off-line (`tpEmis` 2): `dhCont`, `xJust` e o parâmetro `sign`
  do QR Code (Visão Geral, item 9).

## Leiaute e regras

- Faturamento agregado e agregador (`tpFat` 2 e 3, grupo `gAgregadora`) e NFGas
  de substituição (`finNFGas` 3, grupo `gSub`).
- Sinal dos itens no total: os códigos `cClass` iniciados por 5 (deduções) e o
  indicador de devolução (`indDevolucao`) subtraem do total (Visão Geral,
  "Classificação de Produtos", e Anexo I, observação dos totais). Hoje esses
  itens são recusados na confirmação.
- Grupos de ICMS com ST, diferimento ou desoneração (`ICMS10`, `ICMS51`,
  `ICMS60`, `ICMS70`), item sem CST de ICMS (`indSemCST`) e ICMS previsto do
  pagamento antecipado (`gICMSPrevistoPagtoAntecip`, NT 2026.004).
- Valor líquido do item (`vItemLiq`, `vProdLiq` e o total `vProdLiq`, NT
  2026.004, regras 1050 e 1054), opcional no leiaute.
- Fatores de poder calorífico e de correção (`fatorPCS`, `fatorPTZ`, `fatorP`,
  `fatorT`; regra G58), tarifas por período (`gTarif`), volumes contratados
  (`gVolContrat`), taxa regulatória (`TxReg`), motivo da não leitura, processo
  judicial (`gProcRef`), pagamento antecipado, PIX, endereço de
  correspondência, vinculação de pagamento (`pgtoVinc`, NT 2026.001),
  autorizados ao XML (`autXML`) e responsável técnico (`gRespTec`).
- IBS e CBS: estorno de crédito (`gEstornoCred`), diferimento, devolução de
  tributos, IBS municipal (hoje exportado zerado), compras governamentais
  (`gCompraGov`), tributação regular e doação (`indDoacao`).
- Município do fato gerador do IBS e da CBS (`cMunFG`): hoje é o município da
  empresa, como no `l10n_br_nf3e`; conferir se deve ser o da instalação.
- Cadastro da instalação e dos medidores no cliente, com o `cClass` padrão no
  produto, e histórico de consumo montado a partir das NFGas anteriores.
- DANFGas (MOC NFGas, Anexo II) e importação do XML da NFGas.
- Quando a OCA criar o tipo de documento 76 no `l10n_br_fiscal`, trocar o
  registro deste módulo pelo de lá.
