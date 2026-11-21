Este módulo informa os grupos de arma de fogo dos itens da NF-e (grupo
L, `arma`) a partir dos números de série do estoque.

O tipo da arma (uso permitido ou restrito) e sua descrição completa
(calibre, marca, capacidade, tipo de funcionamento, comprimento etc.) são
definidos uma vez no produto. Cada arma é um número de série do
produto: seu nome é o número de série da arma, e ele guarda o número de
série do cano.

Quando uma fatura é criada a partir de uma entrega (faturamento da
separação), a linha da fatura de uma arma recebe um grupo de arma por
número de série expedido. Os grupos podem ser editados na linha da
fatura e na linha do documento fiscal (aba *Firearms*).

Antes da confirmação da NF-e, o módulo recusa um grupo com campo vazio
(os quatro são obrigatórios pelo leiaute), mais de 500 grupos em um
item (limite do leiaute) e os grupos na NFC-e (regra L01-10, rejeição
738, NT 2013/005).
