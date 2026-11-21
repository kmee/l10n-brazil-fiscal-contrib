This module reports the event group (`serv/atvEvento`, TCAtvEvento) of
the NFS-e Nacional DPS, which `l10n_br_nfse_nacional` does not fill.

The fiscal document gets the description of the event, its start and
end dates, the event code given by the municipal tax administration and
the venue. The venue comes from the shipping address of the document and
can be changed. The DPS reports the municipal code (`idAtvEvt`) when
informed, otherwise the venue address (`end`): the leiaute accepts only
one of them.

Rule E0390 (Anexo VI of the NFS-e Nacional, leiaute 1.04.01 published
with NT 009) makes the group mandatory for the services of item 12 and
of subitem 17.10 of the national list: the module refuses to build the
DPS of these services without the event.
