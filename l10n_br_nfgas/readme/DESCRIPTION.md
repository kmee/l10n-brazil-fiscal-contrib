Emissão da Nota Fiscal Eletrônica do Gás (`NFGas`, `modelo 76`), instituída
pelo Ajuste SINIEF 38/25 para as distribuidoras de gás canalizado e obrigatória
para o ICMS desde 03/11/2026 (Ajuste SINIEF 16/26), a partir do documento fiscal
do `l10n_br_fiscal` com o tipo de documento 76, que este módulo cria.

O módulo injeta os modelos do `l10n_br_nfgas_spec` no documento fiscal e nas
suas linhas (empilhamento do `spec_driven_model`, no mesmo desenho do
`l10n_br_nf3e`) e, para a NFGas normal com faturamento normal (`finNFGas` 0,
`tpFat` 1):

- numera o documento pela série e monta a chave de acesso (MOC NFGas 1.00g,
  Visão Geral, "Chave de Acesso da NFGas"), com o dígito verificador em módulo
  11, inclusive para CNPJ alfanumérico;
- gera o XML com os grupos `ide`, `emit`, `dest`, `instalacao`, `gMed`
  (equipamentos de medição), `det/gNormal` (itens com `prod`, `gMedicao` e
  `imposto`), `total`, `gFat` (fatura, regra G167), `gAgencia` (histórico de
  consumo, regra G169), `infAdic` e o QR Code de `infNFGasSupl` (Visão Geral,
  item 9);
- leva para o XML os tributos calculados pelo motor fiscal da OCA: ICMS (grupo
  escolhido pelo CST: 00, 20, 40, 41 e 90), PIS, COFINS, retenções e o grupo
  `IBSCBS` do item, obrigatório na NFGas, com o total `IBSCBSTot`;
- calcula o `vNF` (MOC NFGas 1.00g, Anexo I, regra G150) e o `vTotDFe`, que
  repete o `vNF` em 2026 e soma IBS e CBS a partir de 2027, pela data de
  emissão (NT 2026.004 v1.01, item 4, regra 365);
- confere o código de classificação do item (`cClass`) na tabela do Portal
  NFGas (regra G57) e o CFOP na relação de CFOP permitidos (Anexo I, item 2.5,
  regras G66 e G66a);
- assina o XML com o certificado da empresa, valida contra o XSD do
  `l10n_br_nfgas_spec` e guarda o XML assinado no evento de autorização do
  documento;
- transmite a NFGas ao autorizador da SVRS (serviço `NFGasRecepcao`, síncrono,
  com o XML compactado em gzip e base64) e guarda o `nfgasProc` com o protocolo;
- monta, assina, valida e transmite o evento de cancelamento (110111).

A transmissão usa um cliente próprio (`nfgas_client`) sobre o
`brazil_fiscal_client`, no mesmo molde do cliente do `l10n_br_bpe`.
