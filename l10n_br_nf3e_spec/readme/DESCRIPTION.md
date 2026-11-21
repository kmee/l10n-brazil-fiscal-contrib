Modelos abstratos da Nota Fiscal de Energia Elétrica Eletrônica (`NF3e`,
`modelo 66`), gerados a partir dos esquemas XSD oficiais do Portal NF3e.

O módulo não emite a NF3e: é a base do `l10n_br_nf3e`, que injeta estes mixins
no documento fiscal (`l10n_br_fiscal.document`) e nas suas linhas, no mesmo
desenho dos módulos `l10n_br_nfe_spec`, `l10n_br_cte_spec` e
`l10n_br_mdfe_spec` da OCA.

Os modelos cobrem o leiaute 1.00 da NF3e com o grupo de IBS e CBS da reforma
tributária, na versão do pacote de esquemas `PL_NF3E_1.00a_NT2026.002_RTC_1.01`
(NT 2026.002 RTC v1.01), que é a que acompanha o `nfelib` 3.3.0.

## Geração

Os arquivos de `models/v1_0` foram gerados pelo
[xsdata-odoo](https://github.com/akretion/xsdata-odoo) 1.2.2 a partir dos
esquemas que o [nfelib](https://github.com/akretion/nfelib) guarda em
`nfelib/nf3e/schemas/v1_0`, partindo do esquema raiz `nf3e_v1.00.xsd` (que traz
`nf3eTiposBasico`, `DFeTiposBasicos` e `tiposGeralNF3e`):

```bash
git clone https://github.com/akretion/nfelib
cd nfelib
export XSDATA_SCHEMA=nf3e
export XSDATA_VERSION=10
export XSDATA_LANG="portuguese"
export XSDATA_CURRENCY_FIELD=brl_currency_id
export XSDATA_SCHEMA_NOTE="PL_NF3E_1.00a_NT2026.002_RTC_1.01"
export XSDATA_HEADER=$'Copyright 2026 KMEE\nLicense AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).'
export XSDATA_SKIP='gConsumidor\.tpPosTar(Injet)?$'

xsdata generate nfelib/nf3e/schemas/v1_0/nf3e_v1.00.xsd \
  --package nfelib.nf3e.odoo.v1_0 \
  --output=odoo
```

O arquivo `nf3e_v1_00.py` sai vazio (o esquema raiz só declara o elemento
`NF3e`) e não entra no módulo.

O `XSDATA_SKIP` tira os campos `tpPosTar` e `tpPosTarInjet` do grupo
`gSCEE/gConsumidor`: no esquema eles são listas de valores simples (uma
sequência repetida de `enerAloc` e `tpPosTar`), que o gerador transformaria num
`One2many` para um modelo que não existe. As tags `competApur` (tipo
`xs:gYearMonth`) também ficam de fora, porque o gerador ainda não mapeia esse
tipo.

## Prefixo dos campos

Cada campo leva o prefixo do esquema e de dois dígitos da versão: `nf3e10_`.
Uma revisão menor do leiaute (1.00a, 1.01) usa os mesmos campos; uma versão
maior teria campos e tabelas novos.
