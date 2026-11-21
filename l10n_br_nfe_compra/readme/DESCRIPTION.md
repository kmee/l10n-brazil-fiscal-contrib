Este módulo preenche o grupo de informações de compra da NF-e (grupo
ZB, `compra`): a nota de empenho de uma compra pública (`xNEmp`), o
pedido de compra (`xPed`) e o contrato (`xCont`). O grupo é típico das
vendas a órgãos da administração pública, que pagam contra uma nota de
empenho.

Os três valores são campos do documento fiscal (aba *Others*):

- nota de empenho: digitada (até 22 caracteres);
- pedido de compra do cliente: calculado a partir do pedido de compra
  das linhas do documento (`partner_order`, informado também por item em
  `xPed`) quando todas têm o mesmo, caso contrário a partir da
  referência da fatura do cliente (onde o Odoo copia a referência do
  cliente do pedido de venda); pode ser editado;
- contrato: digitado.

O grupo não é gravado na NFC-e nem na NF-e com DANFE simplificado (regra
ZB01-10, rejeição 762).

Antes da confirmação da NF-e, o módulo recusa uma NF-e com desoneração
de ICMS para venda a órgão público (`motDesICMS` 8) sem a nota de
empenho (regra ZB02-10, rejeição 359, aplicada a critério de cada UF).
