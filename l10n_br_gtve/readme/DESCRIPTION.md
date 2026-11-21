Este módulo emite a Guia de Transporte de Valores Eletrônica (GTV-e,
modelo 64), obrigatória desde 01/03/2023 para os contribuintes do ICMS
que transportam valores (Ajuste SINIEF 03/20 e 44/22). A GTV-e faz parte
do projeto do CT-e 4.00: é autorizada pelo autorizador do CT-e e depois
consolidada em um CT-e OS.

O módulo adiciona o tipo de documento 64 e monta a GTV-e a partir do
`l10n_br_fiscal.document`, reaproveitando o módulo de CT-e
(`l10n_br_cte`): os modelos de spec da GTV-e do `l10n_br_cte_spec`, os
mapeamentos de emitente e de parceiros, as pessoas autorizadas a baixar
o XML (`autXML`), a assinatura, o QR Code e os eventos.

- O `infCte` da GTV-e é empilhado em um modelo próprio, porque suas tags
  têm os mesmos nomes `cte40_` das do CT-e com outros conteúdos.
- O XML é assinado e validado contra o `GTVe_v4.00.xsd` na confirmação
  do documento.
- A transmissão usa o web service síncrono `CTeRecepcaoGTVe`, com a
  GTV-e compactada em GZip e codificada em Base64 (MOC 4.00, Visão
  Geral, itens 3.4.1 e 4.4). Quando autorizada, o `GTVeProc` (GTV-e com
  o protocolo) é guardado no evento de autorização.
- O cancelamento é o evento 110111 por meio do `CTeRecepcaoEvento` (MOC
  4.00, Visão Geral, item 3.7.1).

Regras do MOC 4.00 conferidas pelo módulo antes da SEFAZ:

- Anexo I, capítulo 6: remetente, destinatário, CFOP, datas de saída e
  de chegada, ao menos uma espécie transportada e um veículo; modal
  rodoviário (01) ou multimodal (06).
- Anexo I, regra I04 (rejeição 670): séries de 890 a 899 não são
  permitidas.
- Anexo I, regras I02 e I03 (rejeições 646 e 649): em homologação os
  nomes do remetente e do destinatário são substituídos pelo texto
  obrigatório.
- Anexo I, regras I10 e I12 (rejeições 875 e 253): a chave de acesso
  traz o modelo 64 e um dígito verificador válido.
- Anexo I, regra I70 (rejeição 850): o QR Code (`infCTeSupl`) é sempre
  enviado.
- Visão Geral, item 5 (rejeição 595): a GTV-e não tem carta de
  correção.

A GTV-e não tem grupo de IBS/CBS: as notas técnicas da reforma
tributária do CT-e (NT 2025.001 e 2026.002) se aplicam apenas aos
modelos 57 e 67.
