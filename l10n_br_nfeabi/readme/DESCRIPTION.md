Emissão da Nota Fiscal Eletrônica de Alienação de Bens Imóveis (`NF-e ABI`,
`modelo 77`) a partir do documento fiscal (`l10n_br_fiscal.document`).

A NF-e ABI foi instituída pelo art. 114, III, do regulamento da CBS (Decreto
12.955/2026) e do regulamento do IBS (Resolução CGIBS 6/2026), sem Ajuste
SINIEF. É um documento só de IBS e CBS, do regime específico de bens imóveis da
LC 214/2025 (arts. 251 a 263). A produção abre em 14/12/2026 e o Ato Conjunto
RFB/CGIBS 7/2026 tornou o documento obrigatório em 01/03/2027.

O módulo segue o MOC NF-e ABI 1.00a (Visão Geral e Anexo I), a NT 2026.001
v1.00 e a Tabela de Códigos NF-e ABI v1.01, e usa os modelos e os bindings do
`l10n_br_nfeabi_spec` (pacote de esquemas 1.06 da SVRS). Ele:

- cria o tipo de documento 77, que o `l10n_br_fiscal` ainda não tem;
- injeta no documento fiscal a identificação (`ide`, com modalidade, natureza e
  detalhamento da operação), o emitente (a empresa), os transmitentes, os
  adquirentes, os corretores, o imóvel, a operação (instrumento, redutor de
  ajuste e redutor social), a tributação, os totais, as informações adicionais
  e o responsável técnico;
- cadastra o imóvel (`l10n_br_nfeabi.property`): tipo, espécie, enquadramento,
  CIB, IPTU, INCRA, RIP, cartório, matrícula, área e endereço;
- calcula os valores individuais do declarante e a base do IBS e da CBS pelas
  fórmulas da Tabela de Códigos (abas `vOperacIndiv`, `vRedAjusteIndiv`,
  `vRedSocialIndiv` e `vBC`) e faz o motor fiscal da OCA calcular o IBS e a CBS
  da linha sobre essa base, com o CST, o `cClassTrib`, a alíquota e a redução
  da linha;
- monta a chave de acesso (com CNPJ alfanumérico) e o QR Code da emissão normal
  (NT 2026.001, item 5.2), assina o XML e o valida no esquema oficial;
- monta, assina e valida os eventos de cancelamento (110111) e de
  desfazimento da alienação (112320).

A transmissão ao autorizador ainda não está disponível (ver o roteiro).
