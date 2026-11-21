Emissão da Declaração de Conteúdo Eletrônica (`DC-e`, `modelo 99`, leiaute
1.00) a partir do documento fiscal (`l10n_br_fiscal.document`), no padrão do
`l10n_br_mdfe` e do `l10n_br_bpe`: os grupos do leiaute vêm do
`l10n_br_dce_spec` e são empilhados no documento fiscal.

A DC-e documenta o transporte de bens por pessoa física ou jurídica não
contribuinte do ICMS, quando não se exige outro documento fiscal, e é
obrigatória desde 06/04/2026 (Ajuste SINIEF 05/21, na redação do Ajuste SINIEF
22/25, com as exceções do Ajuste SINIEF 35/26). Ela não tem grupo de IBS e CBS.

O `l10n_br_fiscal` 18.0 não tem o tipo de documento 99: o módulo o cria nos
dados (`l10n_br_dce.document_99`).

O módulo emite a DC-e de três formas (campo `tpEmit`, NT 2024.001 v1.30):

- emissor próprio (2): a empresa, não contribuinte do ICMS, declara os bens que
  envia e é o emitente (`emit`);
- marketplace (1) ou transportadora (3): a empresa emite em nome do remetente
  (pessoa física ou jurídica informada no documento), que vai no `emit`, e a
  empresa vai no grupo `Marketplace` ou `Transportadora`.

Nos três casos a empresa assina a DC-e com o seu certificado e o CNPJ dela
compõe a chave de acesso.

O módulo:

- monta o XML: `ide`, `emit`, `Marketplace` ou `Transportadora`, `dest` (o
  parceiro do documento), um `det` por linha do documento fiscal, `total`,
  `transp`, `infAdic`, `infDec` com os textos fixos, `infSolicDCe` e o QR Code
  do `infDCeSupl`;
- gera a chave de acesso de 44 posições da DC-e (com `tpEmit`, `nSiteAutoriz`
  e o código numérico de 6 dígitos), assina o XML e valida contra o XSD do
  `l10n_br_dce_spec`;
- transmite a DC-e ao Ambiente Nacional da DC-e (serviço síncrono
  `DCeAutorizacao`) e registra o protocolo de autorização;
- envia o evento de cancelamento (110111).

## Regras implementadas

Do Manual de Orientação da DC-e (Anexo I e Visão Geral) e da NT 2024.001
v1.30:

- chave de acesso pelo item 3.1 da NT e DV por módulo 11 (campo B09);
- código numérico diferente de dígito repetido e do número da DC-e (B03-10);
- `cUF` igual à UF do emitente (B02-20);
- o remetente contribuinte do ICMS é recusado (C02-30, rejeição 812): a
  indicação vem do campo "Contribuinte do ICMS" do parceiro;
- nome do destinatário fixo em homologação (E04-20);
- itens numerados a partir de 1 (H02-10), até 999 itens, NCM `00000000` quando
  o bem não tem NCM (I03-10), `vProd` de cada item e `vDC` até
  R$ 100.000.000,00 (I06-10 e W16-10) e `vDC` igual à soma dos `vProd`
  (W16-20);
- textos fixos do grupo `infDec` (grupo ZA);
- QR Code com `chDCe` e `tpAmb` (Anexo II, item 3.2);
- evento com `cOrgao` da UF da chave, autor com o CNPJ da chave, `Id` com
  `nSeqEvento` de 3 dígitos e justificativa de 15 a 255 caracteres (Visão
  Geral, itens 5.4 e 5.5).

## Transmissão

O cliente `dce_client`, sobre o `brazil_fiscal_client`, segue o padrão dos
clientes de CT-e e MDF-e da `nfelib` e o MOC (Visão Geral, itens 4.2.2 e 5):
SOAP 1.2, requisição em `dceDadosMsg`, sem cabeçalho SOAP, serviços síncronos.
A DC-e vai sem compactação (o método `dceAutorizacaoZip` é opcional para o
autorizador). Os endereços são os do Portal DC-e
(https://dfe-portal.svrs.rs.gov.br/DCE/Servicos): um ambiente nacional, mantido
pela SEFAZ do Paraná, para todas as UF. O WSDL só é servido com certificado de
cliente; o elemento de resposta segue o nome da operação do WSDL
(`dceAutorizacaoResult`, por exemplo) e o cliente aceita também
`dceResultMsg`.
