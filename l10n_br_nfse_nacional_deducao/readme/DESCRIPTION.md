This module reports the tax base adjustment group (`valores/vAjusteBC`,
TCInfoAjusteBC) of the NFS-e Nacional DPS, which `l10n_br_nfse_nacional`
does not fill: the deduction from the ISSQN base and the documents that
support the deductions and the refunds (`documentos/docAjusteBC`).

The ISSQN deduction comes from the *ISSQN Deduction Value* of the fiscal
line (`vAjusteBCISSQN`), the same field the NF-e reports as `vDeducao`.

The documents are listed on the NFS-e, each with the adjustment type
(`tpAjusteBC`), the document amount and the part of it applied to this
NFS-e. A document can be an electronic document of the national
repository (NFS-e, NF-e, CT-e or other, by its access key), a fiscal
document outside the repository or a non fiscal document. Choosing a
fiscal document registered in Odoo fills the key, the amount, the dates
and the supplier, all of which can be changed.

The module checks the rules of the group that do not depend on the
municipal parameters or on the national registries (Anexo VI of the
NFS-e Nacional, leiaute 1.04.01 published with NT 009):

- on each document: E0464 and E0465 (description only and always for
  the types 99 and 199), E0469 (applied amount up to the document
  amount), E0472 and E0474 (competence not after the issue date), E0470
  (description of an electronic document of type Other), E0460 (access
  key of 50 digits for an NFS-e and 44 for an NF-e or CT-e), E0476
  (fiscal document outside the repository only with a competence before
  2026) and E0479 (types 101, 103, 104 and 199 need a fiscal document);
- when building the DPS: E0435 (a service not taxed by the ISSQN only
  takes the refunds, types 101 to 199), E0462 (the ISSQN deduction
  excludes the documents of types 2 to 99), E0463 (services 06.01 and
  06.02 only take the types 9 and 199) and E0467 (applied amount up to
  the service amount).
