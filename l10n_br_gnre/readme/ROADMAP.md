A transmissão usa o cliente da GNRE da nfelib (akretion/nfelib#157 e o cliente
empilhado sobre ele), instalado pelo git até ser publicado no PyPI. O WSDL do
portal só responde com certificado de cliente, então os namespaces do envelope
seguem a implementação aberta sped-gnre e precisam ser confirmados no primeiro
envio em homologação.

Fora do escopo por decisão consciente:

- apuração de ICMS-ST, com saldo credor anterior, devoluções e ajustes. No SPED,
  apuração (E200 e E210) e obrigação a recolher (E250) são registros distintos, e
  a GNRE por documento não passa por apuração nenhuma;
- modelo genérico de obrigação servindo DARF, DAS e GARE. A promoção deve
  acontecer por extração de mixin quando existir um segundo consumidor real;
- cadastro completo dos códigos de receita das 27 UFs, que é dado e entra por
  contribuição.

Próximos passos:

- consultar as configurações da UF (GnreConfigUF) a partir da regra por UF, para
  preencher sozinho o que cada receita exige (destinatário, detalhamento,
  produto, campos extras);
- campos extras e os valores de multa, juros e atualização monetária no item;
- trocar a serialização em lxml pelo `StackedModel` sobre os mixins `gnre20_`,
  agora que os bindings estão na nfelib.
