This module reports the construction work group (`serv/obra`,
TCInfoObra) of the NFS-e Nacional DPS, which `l10n_br_nfse_nacional`
does not fill.

The construction site is an address (`res.partner`) that carries the
work registration (CNO, or the former CEI), the Brazilian Real Estate
Registry code (CIB) and the municipal real estate registration. The
fiscal document takes the site from its shipping address and copies
these codes; all of them can be changed on each document.

The group identifies the work by its CNO (`cObra`), or by its CIB
(`cCIB`) when there is no CNO, or by the site address (`end`) when there
is neither. The municipal registration (`inscImobFisc`) goes along when
informed.

Rule E0370 (Anexo VI of the NFS-e Nacional, leiaute 1.04.01 published
with NT 009) makes the group mandatory for the national taxation codes
07.02.01, 07.02.02, 07.04.01, 07.05.01, 07.05.02, 07.06.01, 07.06.02,
07.07.01, 07.08.01, 07.17.01, 07.19.01, 14.14.03 and 14.14.04: the
module refuses to build the DPS of these services without the work
identification. For the other services the group is reported only when
the document has a CNO or a CIB.
