## Transmissão

A NF3e ainda não é transmitida: confirmar o documento gera, assina e valida o
XML, e o envio ao autorizador (ou o cancelamento pelo Odoo) avisa que o serviço
não está disponível. O destino é uma contribuição ao `nfelib`, no padrão do
cliente de CT-e e MDF-e dele (`nfelib/<doc>/client/`, sobre o
`brazil_fiscal_client`):

- os bindings SOAP gerados pelo xsdata a partir dos WSDL dos serviços
  `NF3eRecepcaoSinc`, `NF3eRecepcaoEvento`, `NF3eConsulta` e
  `NF3eStatusServico`. O `nfelib` 3.3.0 tem os bindings do leiaute e dos eventos
  da NF3e, mas não os WSDL nem os bindings SOAP, e os WSDL só são servidos pelos
  autorizadores (`<serviço>?wsdl`);
- a tabela de servidores dos cinco autorizadores publicados no Portal NF3e
  (`https://dfe-portal.svrs.rs.gov.br/Nf3e/Servicos`): MG, MS, MT, PR e SVRS, em
  produção e homologação;
- o cliente `NF3eClient` com o envio síncrono (XML compactado em gzip e base64),
  o evento, a consulta e o status do serviço.

Com o cliente no `nfelib`, este módulo passa a enviar o XML guardado no evento
de autorização, tratar o protocolo (`protNF3e`, `nf3eProc`) e transmitir o
evento de cancelamento que `_nf3e_cancel_event_xml` já monta, assina e valida
(com a regra de prazo do cancelamento do MOC).

## Leiaute

- NT 2026.004 v1.01 (produção em 14/12/2026): valor líquido do item
  (`vProdLiq`, `vItemLiq`), ICMS previsto para pagamento antecipado, IBS e CBS
  no grupo de processo judicial e o fim da NF3e normal com ajuste. O
  `nfelib` 3.3.0 traz o pacote de esquemas da NT 2026.002 RTC v1.01: o
  `l10n_br_nf3e_spec` precisa ser regerado quando o `nfelib` publicar o pacote
  da NT 2026.004.
- NT 2026.001 RTC (vinculação de pagamento, grupo `pgtoVinc` e eventos de
  vinculação).
- Contingência off-line (`tpEmis` 2): `dhCont`, `xJust` e o parâmetro `sign`
  do QR Code (MOC NF3e 1.00a, Visão Geral, item 9.2).
- Grupos da energia que o leiaute não exige e ainda não são preenchidos:
  tarifas por posto tarifário (`gTarif`, regras G111 e G112), adicional de
  bandeira (`gAdBand`), medição do item (`gMedicao` e `gMedida`, regras G114 a
  G116; por isso a origem de quantidade "contratada" é recusada), grandezas
  contratadas (`gGrContrat`), sistema de compensação de energia (`gSCEE`),
  substituição (`gSub`), processo judicial (`gJudic`, `gProcRef`), contas
  contábeis (`gContab`), itens de NF3e anterior (`detItemAnt`, finalidades 2 e
  3), pagamento antecipado, PIX, endereço de correspondência, autorizados ao
  XML (`autXML`) e responsável técnico (`gRespTec`).
- IBS e CBS: estorno de crédito (`gEstornoCred`), diferimento, devolução de
  tributos, IBS municipal (hoje exportado zerado), compras governamentais
  (`gCompraGov`) e doação (`indDoacao`).

## Regras de negócio

- Sinal de cada item no total conforme a natureza do código de classificação
  (`cClass`, MOC NF3e 1.00a, Visão Geral, item 7.9) e o indicador de devolução:
  hoje todos os itens somam.
- Validação do CFOP permitido e da compatibilidade com o `cClass` (regras G108 e
  G109, itens 7.8 e 7.9 do MOC).
- Histórico de faturamento (`gANEEL`) montado a partir das NF3e anteriores da
  mesma unidade consumidora; hoje é informado no documento.
- Cadastro da unidade consumidora e dos medidores no cliente, com o código de
  classificação e a unidade de medida padrão no produto.
- Mais de um grupo `NFdet` (até 13) e mais de 990 itens.
- DANF3E (MOC NF3e, Anexo II) e importação do XML da NF3e.
