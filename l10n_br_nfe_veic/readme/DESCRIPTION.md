Este módulo informa o grupo de veículo novo dos itens da NF-e (grupo
JA, `veicProd`) a partir dos números de série do estoque.

Os dados comuns aos veículos de um modelo (cor, potência, cilindrada,
pesos, tipo de combustível, códigos RENAVAM e DENATRAN, tipo de operação
e assim por diante) são definidos uma vez no produto (*New Vehicle
Model*). Cada veículo é um número de série do produto: seu nome é o
chassi (VIN), e ele guarda o número de série do veículo e o número do
motor.

Quando uma fatura é criada a partir de uma entrega (faturamento da
separação), a linha da fatura de um veículo recebe seu próprio grupo de
veículo novo: o modelo de veículo do produto completado com o chassi, o
número de série e o número do motor do número de série expedido. O grupo
descreve um único veículo, então só é preenchido quando a linha tem um
único número de série. Pode ser editado na linha da fatura e na linha do
documento fiscal (aba *New Vehicle*).

O chassi é conferido contra o leiaute (17 letras maiúsculas ou
dígitos). Antes da confirmação da NF-e, o módulo recusa um item cujo
grupo não tenha um campo exigido pelo leiaute, e recusa o grupo na NFC-e
(regra J01-10, rejeição 736, NT 2013/005).
