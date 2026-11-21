Este módulo preenche o grupo de local de retirada da NF-e (grupo F,
`retirada`), que o leiaute pede apenas quando a mercadoria sai de um
endereço diferente do endereço do emitente: um depósito de filial, um
armazém geral, uma fábrica de terceiros e assim por diante.

O campo já existe no `l10n_br_nfe`, mas nada o preenchia. Aqui ele é
calculado na NF-e de saída a partir das entregas da fatura: quando todas
saem do mesmo depósito e o endereço desse depósito não é o endereço da
empresa emitente, o endereço do depósito vira o local de retirada. Pode
ser editado no documento fiscal (aba *Delivery*).

Antes da confirmação da NF-e, o módulo recusa local de retirada na NFC-e
ou na NF-e com DANFE simplificado (regra F01-10, rejeição 669) e local
de retirada sem CNPJ/CPF, logradouro, número, bairro ou município,
exigidos pelo leiaute.
