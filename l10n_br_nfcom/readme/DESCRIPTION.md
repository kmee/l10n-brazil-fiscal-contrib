Emissão da Nota Fiscal Fatura de Serviço de Comunicação Eletrônica (`NFCom`,
`modelo 62`) a partir do documento fiscal do Odoo (`l10n_br_fiscal.document`),
no mesmo desenho do `l10n_br_nfe` e do `l10n_br_mdfe`: os modelos do
`l10n_br_nfcom_spec` são empilhados no documento e na linha
(`spec_driven_model`) e o XML é montado com os bindings do nfelib.

A NFCom substitui os modelos 21 (NFSC) e 22 (NFST) para os serviços de
comunicação e telecomunicação (Ajuste SINIEF 7/22) e é obrigatória desde
01/11/2025 (Ajuste SINIEF 34/24). O grupo `IBSCBS` da reforma tributária segue a
NT 2025.001 RTC.

O módulo:

- cria o tipo de documento fiscal 62, que o `l10n_br_fiscal` ainda não tem;
- gera a chave de acesso no formato da NFCom (MOC NFCom 1.00a, item 2.1.3:
  `cUF`, `AAMM`, `CNPJ`, `mod`, `serie`, `nNF`, `tpEmis`, `nSiteAutoriz`, `cNF`
  de 7 dígitos e `cDV` em módulo 11, item 7.3);
- monta os grupos `ide`, `emit`, `dest`, `assinante`, `det` (`prod` e
  `imposto`), `total` e `infAdic`, e o `infNFComSupl` com a URL do QR Code do
  autorizador da UF (página de serviços do Portal NFCom);
- leva o ICMS (grupos `ICMS00`, `ICMS20`, `ICMS40`, `ICMS51`, `ICMS90` e
  `ICMSSN` pelo CST e pelo regime da empresa), PIS, COFINS e o IBS e a CBS
  (`IBSCBS` no item e `IBSCBSTot` no total) calculados pelo motor fiscal do
  `l10n_br_fiscal`;
- calcula o `vProd` do item e o `vNF` pelas regras G86 e G137 do Anexo I do MOC;
- assina o XML com o certificado da empresa e o valida contra o XSD do nfelib
  ao confirmar o documento, guardando o XML assinado no evento de autorização;
- monta e assina o evento de cancelamento (`110111`, MOC item 6.1), validado
  contra o XSD.

A transmissão ao autorizador ainda não está no módulo (ver o roadmap): ao
enviar, o documento avisa que a transmissão não está disponível.
