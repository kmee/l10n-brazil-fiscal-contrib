Emissão da Nota Fiscal de Energia Elétrica Eletrônica (`NF3e`, `modelo 66`),
obrigatória para as distribuidoras e permissionárias de energia elétrica
(Ajuste SINIEF 01/19), a partir do documento fiscal do `l10n_br_fiscal` com o
tipo de documento 66.

O módulo injeta os modelos do `l10n_br_nf3e_spec` no documento fiscal e nas
suas linhas (empilhamento do `spec_driven_model`, no mesmo desenho do
`l10n_br_mdfe` e do `l10n_br_cte`) e:

- numera o documento pela série e monta a chave de acesso da NF3e (MOC NF3e
  1.00a, Visão Geral, item 2.1: código numérico de 7 dígitos, forma de emissão e
  site do autorizador), com o dígito verificador em módulo 11, inclusive para
  CNPJ alfanumérico;
- gera o XML com os grupos `ide`, `emit`, `dest`, `acessante` (unidade
  consumidora), `gMed` (medidores), `NFdet` (itens com `prod` e `imposto`),
  `total`, `gFat` (fatura), `gANEEL` (histórico de faturamento), `infAdic` e o
  QR Code de `infNF3eSupl` (MOC NF3e 1.00a, Visão Geral, item 9.2);
- leva para o XML os tributos calculados pelo motor fiscal da OCA: ICMS (grupo
  escolhido pelo CST), PIS, COFINS, retenções e o grupo `IBSCBS` do item com o
  total `IBSCBSTot` (NT 2025.001 RTC v1.14a);
- calcula o `vNF` (MOC, regra G157) e o `vTotDFe`, que repete o `vNF` em 2026 e
  soma IBS e CBS a partir de 2027, pela data de emissão (NT 2025.001 RTC v1.14a,
  item 9, regras 360 e 365, e NT 2026.004 v1.01);
- assina o XML com o certificado da empresa, valida contra o XSD do `nfelib` e
  guarda o XML assinado no evento de autorização do documento;
- monta, assina e valida o XML do evento de cancelamento (110111).

A transmissão ao autorizador ainda não está disponível: ver o roteiro.
