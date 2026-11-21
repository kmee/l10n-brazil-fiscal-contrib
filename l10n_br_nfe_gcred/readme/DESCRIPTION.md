Este módulo informa o crédito presumido de ICMS dos itens da NF-e no
grupo `gCred` do produto (campos `cCredPresumido`, `pCredPresumido` e
`vCredPresumido`, até 4 grupos por item), criado pela NT 2019.001 v1.60
e chamado `gCred` (I05g) a partir da v1.62.

O código do benefício e o percentual são definidos no produto, por
empresa (cada empresa pertence a uma UF, e o código é o concedido por
essa UF, o mesmo usado na EFD). As linhas do documento fiscal do produto
recebem um grupo com esse código e percentual, e o valor é o percentual
aplicado à base de ICMS da linha. O grupo é atualizado quando o produto
ou a base de ICMS da linha muda, e outros grupos podem ser digitados na
linha. As NF-e recebidas mantêm os grupos do XML do fornecedor.

Antes da emissão da NF-e, o módulo recusa o que o schema rejeita: mais
de 4 grupos por item, um código que não tem 8 ou 10 caracteres sem
espaços, ou um percentual fora da faixa de 0 a 999.
