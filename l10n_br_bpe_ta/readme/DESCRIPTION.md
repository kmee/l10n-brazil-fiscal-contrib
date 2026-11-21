Emissão do BP-e TA, o Bilhete de Passagem Eletrônico do transporte aéreo de
passageiros (modelo 63, `modal` 2, leiaute `bpeTA_v1.00.xsd` da NT BP-e
2025.002 v2.00), a partir do documento fiscal (`l10n_br_fiscal.document`)
com o leiaute "BP-e TA" do `l10n_br_bpe`.

O BP-e TA foi criado pela NT 2025.002, está em produção desde 16/12/2025 e é
facultativo; o grupo de IBS e CBS passa a ser obrigatório em 01/03/2027 (Ato
Conjunto RFB/CGIBS 7/2026). A NT 2025.002 v2.00 foi aprovada pelo Ato Técnico
Conjunto 2/2026.

O XML do BP-e TA usa os mesmos nomes de tag do BP-e com outro conteúdo (voos
no `infViagem`, `imp` só com IBS e CBS, outros códigos de componente e de
desconto). Por isso, como no `l10n_br_gtve`, ele não é empilhado no
documento fiscal ao lado do BP-e: o módulo monta os bindings da `nfelib` a
partir do documento, das linhas, dos voos e dos valores que o `l10n_br_bpe`
já calcula (`ide`, `emit`, comprador, passageiro, pagamentos e `IBSCBS`).

O módulo:

- monta o XML do BP-e TA: `ide` (com `tpCompra` e `nroBPIATA`), `emit`,
  `comp` (do parceiro do documento), `infPassagem` e `infPassageiro`,
  `infViagem` (um por voo), `infValorBPe` (um `Comp` por linha do documento),
  `imp` (grupo `IBSCBS` da NT 2025.001 RTC, `vTotTrib` e `vTotDFe`), `pag`
  ou, na compra vinculada a um BP-e múltiplo, o `infBPeVinculado`, além de
  `infAdic`, `infRespTec` e o QR Code do `infBPeSupl`;
- calcula IBS e CBS pelo motor fiscal (o BP-e TA não tem ICMS) e aplica a
  regra do `vTotDFe` (regra F140): igual ao `vBP` em 2026 e `vBP` mais IBS e
  CBS a partir de 2027;
- gera a chave de acesso, a série e o número como o BP-e, assina o XML com o
  certificado da empresa e valida contra o XSD do BP-e TA da `nfelib`;
- transmite pelo serviço síncrono `BPeRecepcaoTA` do cliente do
  `l10n_br_bpe` (mensagem compactada em GZip e Base64, resposta `retBPe`). A
  NT descreve o ambiente autorizador do BP-e TA como a SEFAZ Virtual e o
  Portal BP-e só publica o `BPeRecepcaoTA` na SVRS: a recepção, os eventos e o
  QR Code do BP-e TA usam a SVRS para todas as UFs;
- envia os eventos de cancelamento (110111) e de não embarque (110115).

Regras da NT BP-e 2025.002 v2.00 conferidas antes da SEFAZ:

- F17 (rejeição 411): destino no exterior vai como `UFFim` EX e `cMunFim`
  9999999;
- F19 a F23 (rejeições 419, 420, 484, 485 e 486): um voo só é trecho Normal;
  com conexões, um trecho inicial e os demais de conexão, com a data da
  conexão só nesses e depois do embarque;
- F49 (rejeição 254): embarque não anterior à emissão;
- F50 a F52 e F55 (rejeições 441, 442, 443 e 446): passageiro na compra
  normal e na vinculada, sem passageiro e com comprador no BP-e múltiplo,
  chave do BP-e múltiplo de modelo 63;
- F65 a F67 (rejeições 437, 401 e 500): tipo, descrição e valor do desconto
  informados juntos;
- F69 (rejeição 438): soma dos pagamentos igual ao valor pago mais o troco
  (mais IBS e CBS a partir de 2027), com a tolerância de 1,00 da NT;
- F71 (rejeição 475): grupo de cartão nos pagamentos com cartão.
