1. Crie um documento fiscal com o tipo de documento 66, o cliente, a operação
   fiscal e a série da NF3e.
2. Na aba NF3e, preencha a unidade consumidora (acessante), os dados da fatura
   (competência, vencimento, próxima leitura, linha digitável e débito
   automático ou banco e agência), os medidores e o histórico de faturamento
   (de 1 a 5 grandezas, cada uma com os 13 meses que o leiaute exige).
3. Em cada item, informe o CFOP de energia elétrica e, na aba NF3e da linha, o
   código de classificação do item, a unidade de medida e a origem da
   quantidade faturada. Para o IBS e a CBS, informe a classificação tributária
   (`cClassTrib`): o motor fiscal calcula os valores.
4. Confirme o documento: o XML é gerado, assinado e validado, e fica no evento
   de autorização. Os erros de esquema aparecem na mensagem de erro do XML.
