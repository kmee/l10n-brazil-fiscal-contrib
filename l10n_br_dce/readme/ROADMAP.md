## Transmissão

- Levar o cliente de webservice da DC-e (`dce_client`) para a `nfelib`, em
  `nfelib/dce/client/v1_0`, junto com os bindings que hoje estão no
  `l10n_br_dce_spec`.
- Testar em homologação com certificado real: o cliente foi testado só contra
  respostas simuladas. Conferir no WSDL servido com certificado o nome do
  elemento de resposta de cada serviço e se o `infSolicDCe` vazio (o esquema
  exige o grupo, que o MOC descreve como do aplicativo do fisco, regra
  ZB01-10) é aceito.
- `urlChave` usa o endereço do QR Code publicado no Portal DC-e; o portal não
  publica um endereço próprio de consulta pela chave.
- Consulta da situação (`DCeConsulta`) e status do serviço
  (`DCeStatusServico`) estão no cliente, mas não têm botão no documento.

## Leiaute

- Emissão pelo fisco (`tpEmit` 0, grupo `Fisco`) e pelos Correios (`tpEmit` 4,
  grupo `ECT`), que não são casos do Odoo.
- Contingência off-line (`tpEmis` 2): QR Code com o parâmetro `sign` (Anexo II,
  item 3.2) e regras ZX02-40 a ZX02-60.
- Emitente e destinatário sem CPF ou CNPJ (`idOutros`) e destinatário no
  exterior (UF `EX`, município 9999999, regras E10-30 e E14-30).
- Pessoas autorizadas a obter o XML (`autXML`), informações adicionais do
  marketplace (`infAdMarketplace`) e grupos de uso livre (`obs*`).
- CNPJ alfanumérico na chave de acesso, quando o Portal DC-e publicar os
  esquemas da emissão com ele.
- A NT 2024.001 v1.30 lista o grupo `EmpEmisProp` e o campo `infAdTransp`,
  que o esquema do pacote da NT não tem: o módulo segue o esquema.

## Regras de negócio

- Exceções da obrigatoriedade (Ajuste SINIEF 35/26) e limites e exceções de
  cada UF (cláusula 15ª-A do Ajuste SINIEF 05/21): o módulo não decide quando a
  DC-e é exigida.
- Prazo de 24 horas do cancelamento (regra 2P12-14): hoje só o autorizador
  confere.
- DACE (documento auxiliar em PDF, Anexo II) e importação do XML da DC-e.
- Se o `l10n_br_fiscal` passar a ter o tipo de documento 99, este módulo deve
  deixar de criá-lo.

## Técnico

- O documento fiscal empilha vários esquemas (BP-e, NF3e, NFCom, DC-e...) e o
  `spec_driven_model` só roda o hook que torna concretos os modelos restantes
  para o primeiro esquema da MRO; por isso o documento chama esse hook com o
  contexto da DC-e no `_register_hook`. Tirar quando o `spec_driven_model`
  rodar o hook para cada esquema empilhado.
