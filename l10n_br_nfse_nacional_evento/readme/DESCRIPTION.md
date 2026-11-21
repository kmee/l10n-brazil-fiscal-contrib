Este módulo informa o grupo de evento (`serv/atvEvento`, TCAtvEvento) da
DPS da NFS-e Nacional, que o `l10n_br_nfse_nacional` não preenche.

O documento fiscal ganha a descrição do evento, suas datas de início e
de fim, o código do evento dado pela administração tributária municipal
e o local. O local vem do endereço de entrega do documento e pode ser
alterado. A DPS informa o código municipal (`idAtvEvt`) quando
preenchido; caso contrário, o endereço do local (`end`): o leiaute
aceita apenas um dos dois.

A regra E0390 (Anexo VI da NFS-e Nacional, leiaute 1.04.01 publicado com
a NT 009) torna o grupo obrigatório para os serviços do item 12 e do
subitem 17.10 da lista nacional: o módulo recusa montar a DPS desses
serviços sem o evento.
