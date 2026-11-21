## Transmissão

A NF-e ABI ainda não é transmitida: confirmar o documento gera, assina e valida
o XML, e o envio ao autorizador (ou o cancelamento pelo Odoo) avisa que o
serviço não está disponível. O que se sabe em 21/11/2026:

- o MOC NF-e ABI 1.00a (Visão Geral, itens 4 e 5) define serviços síncronos em
  SOAP 1.2 com TLS mútuo, a mensagem em `nfeDadosMsg`, o cabeçalho
  `nfeCabecMsg` e os métodos `nfeAutorizacao`, `nfeConsulta`,
  `nfeStatusServico` e o registro de eventos;
- a SVRS (<https://dfe-portal.svrs.rs.gov.br/Nfabi/Servicos>) lista só a
  homologação do Ambiente Nacional da NF-e ABI
  (`homologacao.nfeabi.fazenda.pr.gov.br/nfeabi/NFeABIAutorizacao`,
  `NFeABIConsulta` e `NFeABIStatusServico`), sem o serviço de eventos e sem
  produção;
- o WSDL só é servido com certificado de cliente, então o namespace e a ação
  SOAP de cada serviço não foram confirmados, e o credenciamento é só
  "mediante prévia requisição do emitente ou de ofício" (MOC, item 4.3.3).

Com o WSDL e a URL de produção publicados, o cliente vai sobre o
`brazil_fiscal_client`, no desenho do cliente do BP-e deste repositório
(`l10n_br_bpe/bpe_client`), e passa a enviar o XML guardado no evento de
autorização, tratar o protocolo (`protNFeABI`, `nfeabiProc`) e transmitir os
eventos que `_nfeabi_cancel_event_xml` e `_nfeabi_undo_event_xml` já montam.
Os endereços do QR Code e da consulta por chave também precisam ser publicados.

## Leiaute

- Modalidade 02 (arrematação judicial, adjudicação ou remição): o declarante é
  o adquirente, com `indDeclarante`, `pAquisicao` e `indContrib` no grupo F e
  `tpEmit` 02 ou 03; hoje o documento é recusado.
- NF-e ABI de transição (`tpNF` 2, grupo `gInfTribTransic`, arts. 485 e 486 da
  LC 214/2025), pagamento antecipado (`tpPagAnt`, `gPagAntecipado`,
  `gInfPagAntecip`) e contingência off-line (`tpEmis` 9, `gCont` e o QR Code
  com o parâmetro `sign` da NT 2026.001, item 5.3).
- Permuta com torna (`indTorna`, `gTorna`, `vTornaIndiv`): sem torna, a permuta
  de imóveis (naturezas 13 e 14) sai com base zero.
- Incorporação e loteamento (`gIncorpLote`, `indIncorpLote` 1 e 2, sem destaque
  de IBS e CBS, sem o grupo de totais e com `detPagIncorpLote`) e o evento de
  pagamento de parcela (112310).
- Pagamento inicialmente previsto (`pag`, `detPagImovel`), documentos
  referenciados (`NFref`), autorizados ao XML (`autXML`), observações
  (`obsCont`, `obsFisco`), substituição (`finNFe` 2) e o evento de apropriação
  de créditos individuais (211310), que é do adquirente.
- IBS e CBS: compras governamentais (`gCompraGov`, `gTribCompraGov`), estorno
  de crédito (`gEstornoCred`) e IBS municipal (hoje exportado zerado, como no
  motor fiscal da OCA). Os indicadores da tabela de `cClassTrib` citados no MOC
  (`ind_gIBSCBS`, `ind_pag_NFeABI`, `ind_Area_NFeABI`) não estão no
  `l10n_br_fiscal`, e a tabela de classificações tributárias da OCA ainda não
  marca o documento 77.
- `tpEmit` fixo em 01 (vendedor), o único das modalidades atendidas.
- DANFE-ABI (NT 2026.001, capítulo 6) e importação do XML.

## Regras de negócio

- Na NF-e ABI completa, o redutor de ajuste e o redutor social individuais usam
  a proporção do declarante em percentual (`pTransIndiv` / 100), leitura das
  fórmulas `pTransIndiv * vRedAjusteImovel` e `pTransIndiv * vRedSocial` da
  Tabela de Códigos.
- Regras ainda de implementação futura no autorizador e não aplicadas aqui:
  G03-10 (CIB, IPTU ou INCRA obrigatório), H21-10 e H22-10.
- Valor do redutor social: o módulo não calcula a atualização pelo IPCA nem a
  proporção da área residencial; o valor é informado no documento.
