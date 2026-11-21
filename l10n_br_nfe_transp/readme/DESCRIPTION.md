Este módulo preenche os subgrupos de transporte da NF-e (grupo X,
`transp`) que a localização deixa vazios: o veículo (`veicTransp`), os
reboques (`reboque`) e a retenção de ICMS do transporte (`retTransp`). A
modalidade do frete (`modFrete`), a transportadora (`transporta`) e os
volumes (`vol`) ficam com o `l10n_br_delivery_nfe`.

Veículo e reboques vêm dos veículos da transportadora do
`l10n_br_delivery` (placa, UF e código da ANTT), que até agora nunca
chegavam à NF-e. No documento fiscal (aba *Delivery*):

- veículo: por padrão o veículo da transportadora, quando ela tem apenas
  um; pode ser alterado;
- reboques: até 5 veículos (limite do leiaute).

Cada um vira um grupo `veicTransp` ou `reboque` com a placa (em
maiúsculas, sem separadores), a UF e o código da ANTT (RNTC, até 20
caracteres). Ficam fora do XML nas operações interestaduais (regra
X02-20, rejeição 868, NT 2017.002), na NFC-e e na NF-e com DANFE
simplificado (regras X18-10 e X22-10, rejeições 756 e 757).

A retenção de ICMS do transporte é usada quando o emitente retém o ICMS
de um serviço de frete (por exemplo, contratado de um transportador
autônomo): valor do serviço, base da retenção (por padrão o valor do
serviço), alíquota, ICMS retido (base vezes alíquota), CFOP do frete e
município do fato gerador (por padrão o município da empresa). É
recusada na NFC-e e na NF-e com DANFE simplificado (regra X11-10,
rejeição 755).

Antes da confirmação da NF-e, o módulo recusa uma placa que não siga o
padrão do leiaute e uma retenção de ICMS sem CFOP ou município.
