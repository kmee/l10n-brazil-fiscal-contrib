Este módulo preenche o grupo de rastreabilidade dos itens da NF-e
(grupo I80, `rastro`) a partir dos lotes do estoque, e o confere antes da
emissão da NF-e.

O grupo foi criado pela NT 2016.002 para produtos sujeitos a regulação
sanitária ou a recolhimento: medicamentos, bebidas, água envasada,
produtos veterinários e agrícolas, entre outros. Cada item pode levar
até 500 lotes, cada um com número, quantidade, data de fabricação e data
de validade.

Quando uma fatura é criada a partir de uma entrega (faturamento da
separação), cada lote expedido vira um grupo de rastreabilidade da linha
da fatura:

- número do lote: o nome do lote;
- quantidade: a quantidade do lote na unidade da linha da fatura;
- data de fabricação: a data de produção do lote;
- data de validade: a data de validade do lote.

As duas datas são lidas como datas de calendário no fuso horário do
usuário.

Antes da confirmação da NF-e, o módulo recusa os dados que a SEFAZ
rejeitaria: número do lote ou datas ausentes, mais de 500 lotes, data de
fabricação posterior à data de emissão (regra I83-10, rejeição 877) e
data de validade anterior à data de fabricação (regra I84-10, rejeição
870).

Os lotes de uma NF-e recebida são mantidos nas linhas importadas, e os
grupos podem ser editados à mão na linha da fatura e na linha do
documento fiscal (aba Traceability).
