1. Crie um documento fiscal com o tipo de documento 76, o cliente, a operação
   fiscal e a série da NFGas.
2. Na aba NFGas, preencha a instalação (código, tipo e classe de consumo), os
   dados da fatura (competência, vencimento, próxima leitura, linha digitável e
   débito automático ou banco e agência), os equipamentos de medição com as
   leituras anterior e atual e o histórico de consumo (de 1 a 5 históricos, com
   1 a 13 meses cada).
3. Em cada item, informe um CFOP permitido na NFGas (5352, 5353, 5651 a 5656)
   e, na aba NFGas da linha, o código de classificação do item (`cClass`), a
   unidade de medida e a origem da quantidade faturada; para a quantidade
   medida (origens 2 e 5), escolha o medidor. Para o IBS e a CBS, informe a
   classificação tributária (`cClassTrib`): o motor fiscal calcula os valores.
4. Confirme o documento: o XML é gerado, assinado e validado, e fica no evento
   de autorização. Os erros de esquema aparecem na mensagem de erro do XML.
5. Envie o documento ao autorizador; o cancelamento é feito pelo evento 110111.
