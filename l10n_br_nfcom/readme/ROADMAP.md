- Transmissão (destino: contribuição ao nfelib). O nfelib 3.3.0 tem os
  bindings da NFCom, mas não tem os bindings SOAP (`nfelib/nfcom/soap/v1_0`)
  nem o cliente (`nfelib/nfcom/client/v1_0`) sobre o `brazil_fiscal_client`,
  como já existem para NF-e, CT-e e MDF-e. Os WSDL dos serviços
  `NFComRecepcao`, `NFComConsulta`, `NFComRecepcaoEvento` e
  `NFComStatusServico` só são servidos com autenticação mútua (certificado
  ICP-Brasil) e o MOC NFCom 1.00a (item 3.4.1) escreve o namespace com caixa
  diferente da usada nos schemas (`NFCom` x `nfcom`), então o nome do elemento
  `nfcomDadosMsg` e o namespace de cada serviço precisam ser conferidos no WSDL
  antes de gerar os bindings. A recepção é síncrona e a mensagem vai
  compactada em GZip e codificada em Base64 (MOC, itens 3.4.1 e 4.2); os
  autorizadores são MG, MS, MT e SVRS (página de serviços do Portal NFCom).
  Com o cliente no nfelib: envio, consulta, protocolo (`nfcomProc`) e envio do
  evento de cancelamento já montado por este módulo.
- `schema_validation` da NFCom no nfelib: o `CommonMixin` não conhece o caminho
  do XSD da NFCom e o módulo passa o caminho explicitamente.
- Leiaute: os schemas são os do pacote `PL_NFCOM_1.00_NT2026.002 RTC_1.01`
  distribuído pelo nfelib 3.3.0. A NT 2026.004 v1.01 (produção em
  14/12/2026) e a NT 2026.005 v1.00 (Simples Nacional) ainda não estão no
  nfelib: regenerar o `l10n_br_nfcom_spec` quando estiverem.
- Regras da NT 2026.002 que dependem de cadastro: `CNPJCobrTerc` para itens de
  `cClass` do grupo 110 (cobrança de terceiros) e a rejeição 310 (grupo
  IBS/CBS obrigatório para CRT 3).
- Grupo `IBSCBS`: só `gIBSCBS`; faltam `gEstornoCred`, diferimento,
  devolução de tributos, redução por compra governamental e o IBS municipal
  separado do estadual (exportado com zero, como na NF-e).
- Faturamento: grupos `gFat` (competência, vencimento, código de barras,
  débito automático, PIX), `gFatCentral`, `gCofat`, `gSub` (substituição),
  `gFidelidade`, `pgtoVinc` e `gRespTec`, e o faturamento recorrente a partir
  de contratos.
- Itens: `gProcRef`, `gRessarc`, `ICMSUFDest`, FUST, FUNTTEL, retenções por
  item (`retTrib`), `indSemCST` e validação do CFOP pela lista do item 7.7 do
  MOC e do `cClass` pela tabela do item 7.8.
- Contingência (`tpEmis` 2, `dhCont`, `xJust` e assinatura do QR Code).
- DANFE-COM (Anexo II do MOC).
- Tipo de documento 62: levar o registro para os dados do `l10n_br_fiscal` e
  incluir o 62 nas classificações tributárias do IBS e da CBS
  (`tax_classification`) que se aplicam à NFCom.
- Importação do XML da NFCom.
