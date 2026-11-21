- Levar os esquemas e os bindings da DC-e para a `nfelib`
  (`nfelib/dce/schemas/v1_0` e `nfelib/dce/bindings/v1_0`, com as extensões
  `CommonMixin` na `.xsdata.xml` dela). Os bindings ficam neste módulo só até
  lá; depois, o `_dce10_binding_module` passa a apontar para a `nfelib` e as
  pastas `schemas` e `bindings` saem daqui.
- Serviço de distribuição da DC-e (pacote "Schemas BT 2024.001 - SVD",
  `PL_DCe_100_BT2024.001_SVD_v1.00.zip`, de 13/04/2026): ele traz outra versão do
  `tiposGeralDCe_v1.00.xsd`, já com o CNPJ alfanumérico, que não cabe na mesma
  pasta destes esquemas. Gerar num pacote próprio quando algum módulo precisar.
- CNPJ alfanumérico: os esquemas da emissão ainda só aceitam CNPJ numérico;
  regerar quando o Portal DC-e publicar o pacote da NT conjunta do CNPJ
  alfanumérico.
- Mapear o atributo `xCampo` dos grupos `obs*` quando o xsdata-odoo tratar o
  tipo `anySimpleType`.
