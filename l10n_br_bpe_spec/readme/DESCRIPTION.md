This module provides the abstract models of the Electronic Passenger Ticket
(`BP-e`, `model 63`), generated from the official XSD schemas of version 1.00
published on the BP-e Portal (SVRS), in the copy that the `nfelib` library
keeps in `nfelib/bpe/schemas/v1_0`.

Like `l10n_br_mdfe_spec` and `l10n_br_cte_spec`, it does not issue the BP-e by
itself: it is the base for the `l10n_br_bpe` module, which stacks these models
onto the fiscal document (`l10n_br_fiscal.document`).

The models cover the three layouts of model 63, all defined in
`bpeTiposBasico_v1.00.xsd`:

- BP-e (`bpe.10.tbpe_*`): ticket for passenger transport by road, water and
  rail.
- BP-e TM (`bpe.10.tbpetm_*`): metropolitan and semi-urban transport charged
  by turnstile or counter.
- BP-e TA (`bpe.10.tbpeta_*`): air transport (NT 2025.002).

The `IBSCBS` group of the tax reform (NT 2025.001 RTC) comes from
`DFeTiposBasicos_v1.00.xsd` (`bpe.10.ttribbpe`, `bpe.10.tcibs` and the
subgroups). The ICMS groups by CST (`ICMS00`, `ICMS20`, `ICMS45`, `ICMS90` and
`ICMSSN`) are left out of the generation, as in CT-e, because `l10n_br_bpe`
builds them from the fiscal document lines.

## Generation

The models were generated with
[xsdata-odoo](https://github.com/akretion/xsdata-odoo) from the `nfelib` 3.3.0
schemas, starting from `bpe_v1.00.xsd` (which includes
`bpeTiposBasico_v1.00.xsd`, `tiposGeralBPe_v1.00.xsd` and
`DFeTiposBasicos_v1.00.xsd`):

```bash
export XSDATA_SCHEMA=bpe
export XSDATA_VERSION=10
export XSDATA_SKIP="^ICMS\d+|^ICMSSN+"
export XSDATA_LANG="portuguese"
export XSDATA_CURRENCY_FIELD="brl_currency_id"

xsdata generate nfelib/bpe/schemas/v1_0/bpe_v1.00.xsd \
  --package nfelib.bpe.odoo.v1_0 \
  --output=odoo
```

Generating from the whole schema directory does not work:
`DFeTiposBasicos_v1.00.xsd` has no `targetNamespace` and, when processed on
its own, its types (`TTribBPe`, `TIBSCBSTot`...) can no longer be found by the
other files and the fields become `Char`.

The BP-e has two tags that differ only by case: `infBPe/comp` (buyer) and
`infBPe/infValorBPe/Comp` (value component). xsdata-odoo 1.2.2 compares the
names before normalizing them and generates both groups with the same model
`bpe.10.tbpe_comp`. The generation of this module used xsdata-odoo with that
comparison done after normalization, which yields `bpe.10.tbpe_comp` (buyer)
and `bpe.10.tbpe_infvalorbpe_comp` (component); the same applies to BP-e TA.

## Field prefix and version

Each field has the prefix `bpe10_` (schema name and two digits of the version
1.00), like `nfe40_` for NF-e and `cte40_` for CT-e: a minor schema version
reuses the fields, and a major version gets new fields and tables.
