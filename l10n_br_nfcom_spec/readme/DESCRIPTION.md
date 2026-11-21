Abstract models (mixins) of the Electronic Communication Services Invoice
(`NFCom`, `model 62`), generated from the official schemas of layout 1.00 by
[xsdata-odoo](https://github.com/akretion/xsdata-odoo).

The module does not issue the NFCom: it is the layout data base for the
implementation module `l10n_br_nfcom`, which maps these models onto the Odoo
fiscal document (`l10n_br_fiscal.document`), following the same pattern as the
OCA modules `l10n_br_nfe_spec`, `l10n_br_cte_spec` and `l10n_br_mdfe_spec`.

The models cover the entire `infNFCom` group (identification, issuer,
recipient, subscriber, replacement, co-billing, items with ICMS, PIS, COFINS,
FUST, FUNTTEL, withholdings and the `IBSCBS` group of the tax reform, totals,
invoice and technical manager) and the common types of `DFeTiposBasicos` (IBS,
CBS and IS).

Schemas used: package `PL_NFCOM_1.00_NT2026.002 RTC_1.01`, distributed by
nfelib 3.3.0 (`nfelib/nfcom/schemas/v1_0`).

Generation command:

```bash
export XSDATA_SCHEMA=nfcom
export XSDATA_VERSION=10
export XSDATA_LANG="portuguese"
export XSDATA_CURRENCY_FIELD=brl_currency_id
export XSDATA_HEADER=$'Copyright 2026 KMEE\nLicense AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).'

xsdata generate nfelib/nfcom/schemas/v1_0/nfcom_v1.00.xsd \
  --package nfelib.nfcom.odoo.v1_0 \
  --output=odoo
```

From the result, `tipos_geral_nfcom_v1_00.py`, `dfe_tipos_basicos_v1_00.py`
and `nfcom_tipos_basico_v1_00.py` are included; `nfcom_v1_00.py` only
re-imports the root type and is left out. From `nfcom_tipos_basico_v1_00.py`
the field `nfcom10_cUFAdic` (group `assinante`) is removed: it is a list of a
simple type (`TCodUfIBGE`), which xsdata-odoo 1.2.2 generates as a `One2many`
to a nonexistent model, the same case as `cte40_cInfManu` in CT-e, and it
prevents the registry from loading.

The fields have the prefix `nfcom10_` (schema and two digits of the version),
like `nfe40_` for NF-e: a minor layout revision reuses the same fields.
