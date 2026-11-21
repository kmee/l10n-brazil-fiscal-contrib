Emissão da Nota Fiscal de Água e Saneamento Eletrônica (`NFAg`, `modelo 75`),
instituída pelo art. 114, I, do regulamento da CBS (Decreto 12.955/2026) e do
regulamento do IBS (Resolução CGIBS 6/2026), para quem presta abastecimento de
água e esgotamento sanitário. Em 2026 a NFAg é facultativa; o Ato Conjunto
RFB/CGIBS 4/2026, na redação do Ato Conjunto 7/2026, a torna obrigatória para o
IBS e a CBS a partir de 01/01/2027.

O módulo parte do documento fiscal do `l10n_br_fiscal` com o tipo de documento
75 (que já existe nos dados do `l10n_br_fiscal`) e injeta nele os modelos do
`l10n_br_nfag_spec` (empilhamento do `spec_driven_model`, no mesmo desenho do
`l10n_br_nf3e`). Ele:

- numera o documento pela série e monta a chave de acesso da NFAg (MOC NFAg
  1.00l, Visão Geral, chave de acesso: código numérico de 7 dígitos, forma de
  emissão e site do autorizador), com o dígito verificador em módulo 11,
  inclusive para CNPJ alfanumérico;
- gera o XML com os grupos `ide`, `emit`, `dest`, `ligacao`, `gMed`
  (medidores), `det` (itens com `prod` e `imposto`), `total`, `gFat` (fatura),
  `gAgencia` (agência reguladora com o histórico de consumo), `infAdic` e o QR
  Code de `infNFAgSupl` (MOC NFAg 1.00l, Visão Geral, item 9);
- leva para o XML os tributos calculados pelo motor fiscal da OCA: o grupo
  `IBSCBS`, obrigatório em todo item da NFAg, com o total `IBSCBSTot`, o PIS, a
  COFINS e as retenções federais;
- calcula os totais pelo sinal de cada item (os itens com `cClass` iniciado
  por 5 deduzem, MOC NFAg 1.00l, Visão Geral, classificação de produtos, e
  Anexo I, observação do grupo de totais), o `vNF` (regra G177) e o `vTotDFe`,
  que repete o `vNF` em 2026 e soma IBS e CBS a partir de 2027, pela data de
  emissão (NT 2026.004 v1.01, item 4, regra 365);
- assina o XML com o certificado da empresa, valida contra o XSD do
  `l10n_br_nfag_spec` e guarda o XML assinado no evento de autorização;
- transmite a NFAg ao autorizador da SVRS (único autorizador da NFAg) pelo
  serviço síncrono `NFAgRecepcao`, trata o protocolo e guarda o `nfagProc`;
- monta, assina, valida e transmite o evento de cancelamento (110111).

O cliente de webservice (`nfag_client`) segue o do `l10n_br_bpe`, sobre o
`brazil_fiscal_client`: SOAP 1.2, mensagem em `nfagDadosMsg`, retorno em
`nfagResultMsg` e só a recepção compactada em gzip e base64 (MOC NFAg 1.00l,
Visão Geral, item 3).
