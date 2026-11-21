- Levar os bindings e os esquemas da NF-e ABI para o `nfelib` (pacote
  `nfelib.nfeabi`, com a entrada no `generate_bindings.py`, as extensões do
  `.xsdata.xml` e a localização do esquema no `CommonMixin`). Quando estiverem
  no `nfelib`, este módulo passa a apontar para lá e o pacote `bindings` sai
  daqui.
- Conferir o pacote de esquemas do Portal Nacional da NF-e com o da SVRS
  quando a produção da NT 2026.001 abrir (14/12/2026) e regerar se divergirem.
- Os bindings SOAP dos serviços (`NFeABIAutorizacao`, `NFeABIConsulta`,
  `NFeABIStatusServico` e o de eventos) não estão no pacote de esquemas: os
  WSDL só são servidos pelo autorizador.
