Modelos abstratos (mixins) da Nota Fiscal Fatura de Serviço de Comunicação
Eletrônica (`NFCom`, `modelo 62`), gerados a partir dos schemas oficiais do
leiaute 1.00 pelo [xsdata-odoo](https://github.com/akretion/xsdata-odoo).

O módulo não emite a NFCom: é a base de dados do leiaute para o módulo de
implementação `l10n_br_nfcom`, que mapeia esses modelos no documento fiscal do
Odoo (`l10n_br_fiscal.document`), no mesmo desenho dos módulos
`l10n_br_nfe_spec`, `l10n_br_cte_spec` e `l10n_br_mdfe_spec` da OCA.

Os modelos cobrem o grupo `infNFCom` inteiro (identificação, emitente,
destinatário, assinante, substituição, cofaturamento, itens com ICMS, PIS,
COFINS, FUST, FUNTTEL, retenções e o grupo `IBSCBS` da reforma tributária,
totais, fatura e responsável técnico) e os tipos comuns do `DFeTiposBasicos`
(IBS, CBS e IS).

Schemas usados: pacote `PL_NFCOM_1.00_NT2026.002 RTC_1.01`, distribuído pelo
nfelib 3.3.0 (`nfelib/nfcom/schemas/v1_0`).

Comando de geração:

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

Do resultado entram `tipos_geral_nfcom_v1_00.py`, `dfe_tipos_basicos_v1_00.py`
e `nfcom_tipos_basico_v1_00.py`; o `nfcom_v1_00.py` só reimporta o tipo raiz e
fica de fora. Do `nfcom_tipos_basico_v1_00.py` sai o campo `nfcom10_cUFAdic`
(grupo `assinante`): é uma lista de um tipo simples (`TCodUfIBGE`), que o
xsdata-odoo 1.2.2 gera como `One2many` para um modelo inexistente, o mesmo caso
do `cte40_cInfManu` do CT-e, e impede o carregamento do registro.

Os campos têm o prefixo `nfcom10_` (schema e dois dígitos da versão), como o
`nfe40_` da NF-e: uma revisão menor do leiaute reaproveita os mesmos campos.
