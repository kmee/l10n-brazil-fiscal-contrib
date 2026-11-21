1. Crie um documento fiscal com o tipo de documento 75, o cliente, a operação
   fiscal e a série da NFAg.
2. Na aba NFAg, preencha a ligação (identificação, tipo e coordenadas), os
   dados da fatura (competência, vencimento, próxima leitura, linha digitável
   e débito automático ou banco e agência), a agência reguladora de
   atendimento, os medidores e o histórico de consumo (de 1 a 5 históricos,
   cada um com 1 a 13 meses).
3. Em cada item, informe na aba NFAg da linha o código de classificação do
   item (`cClass`, 7 dígitos), a unidade de medida e a origem da quantidade
   faturada. O produto precisa de código interno (`cProd`). Para o IBS e a
   CBS, informe a classificação tributária: o motor fiscal calcula os valores.
4. Confirme o documento: o XML é gerado, assinado e validado, e fica no evento
   de autorização. Os erros de esquema aparecem na mensagem de erro do XML.
5. Envie o documento: com a autorização, o documento fica autorizado e o
   `nfagProc` fica no evento. O cancelamento envia o evento 110111; uma
   recusa da SEFAZ fica registrada no evento e na conversa do documento.
