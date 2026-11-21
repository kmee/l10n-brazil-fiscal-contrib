Bindings Python e modelos abstratos da Nota Fiscal de Água e Saneamento
Eletrônica (`NFAg`, `modelo 75`), gerados a partir dos esquemas XSD oficiais
publicados no Portal NFAg da SVRS.

O módulo não emite a NFAg: é a base do `l10n_br_nfag`, que injeta estes mixins
no documento fiscal (`l10n_br_fiscal.document`) e nas suas linhas, no mesmo
desenho do `l10n_br_nf3e_spec` e dos módulos `l10n_br_nfe_spec`,
`l10n_br_cte_spec` e `l10n_br_mdfe_spec` da OCA.

A biblioteca `nfelib` 3.3.0 não tem a NFAg. Por isso este módulo traz, além dos
modelos, os próprios bindings (`bindings/v1_0`) e os esquemas (`schemas/v1_0`)
usados na validação do XML, até que eles entrem na `nfelib` (ver o roteiro).

## Esquemas

Pacote `PL_NFAg_NT2026.004 RTC_1.01`, o "Nota Técnica 2026.004 RTC v1.01" da
página de documentos do Portal NFAg
(`https://dfe-portal.svrs.rs.gov.br/NFAG/Documentos`), baixado em 21/11/2026:

- URL: `https://dfe-portal.svrs.rs.gov.br/NFAG/DownloadArquivoEstatico/?sistema=NFAG&tipoArquivo=2&nomeArquivo=PL_NFAg_NT2026.004%20RTC_1.01.zip`
- sha256 do zip: `b2a6d77da9ce288d5b16e38ab84071f61fa344dc988bc5f3f7cb3a7f67b703cc`

É o leiaute 1.00 do MOC NFAg 1.00l (Anexo I, aprovado pelo Ato Técnico Conjunto
RFB/SUFIS/CGIBS 2/2026) com o grupo `IBSCBS` obrigatório no item, as mudanças da
NT 2026.001 (vinculação de pagamento), da NT 2026.002 e as da NT 2026.004 v1.01
(valor líquido `vItemLiq`/`vProdLiq`, faturamento agregado e agregador, grupo
`gIBSCBS` no processo referenciado e origem de quantidade "mínimo"), que entra
em produção em 14/12/2026. Os arquivos estão como publicados, só com as quebras
de linha e os espaços no fim da linha normalizados pelo `pre-commit`.

## Geração dos bindings

Os arquivos de `bindings/v1_0` foram gerados com o xsdata 25.7 pelo script
`generate_bindings.py` do [nfelib](https://github.com/akretion/nfelib) (com os
patches de `nfelib/generate_patches`), com o `.xsdata.xml` do nfelib e três
diferenças:

- o pacote `odoo.addons.l10n_br_nfag_spec.bindings.v1_0`;
- `RelativeImports` ligado, para que as importações não passem de 88 colunas;
- as extensões `nfelib.CommonMixin` das classes `Tnfag`, `TprotNfag`,
  `NfagProc` e `EvCancNfag`, como as do NF3e.

```python
# na raiz de um clone do nfelib, com os XSD em <schemas>
import sys
import generate_bindings as gb

gb.SCHEMAS["nfag"] = gb.SchemaConfig(
    name="nfag",
    schema_dir="<schemas>",
    package="odoo.addons.l10n_br_nfag_spec.bindings.v1_0",
)
sys.argv = ["generate_bindings.py", "nfag"]
gb.main()
```

O arquivo `bindings/ruff.toml` só desliga o E501 nos bindings gerados, cujos
padrões do XSD são expressões regulares longas.

## Geração dos modelos

Os arquivos de `models/v1_0` foram gerados pelo
[xsdata-odoo](https://github.com/akretion/xsdata-odoo) 1.2.2 a partir do
esquema raiz `nfag_v1.00.xsd` (que traz `nfagTiposBasico`, `DFeTiposBasicos` e
`tiposGeralNFAg`):

```bash
export XSDATA_SCHEMA=nfag
export XSDATA_VERSION=10
export XSDATA_LANG="portuguese"
export XSDATA_CURRENCY_FIELD=brl_currency_id
export XSDATA_SCHEMA_NOTE="PL_NFAg_NT2026.004 RTC_1.01"
export XSDATA_HEADER=$'Copyright 2026 KMEE\nLicense AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).'

xsdata generate schemas/v1_0/nfag_v1.00.xsd \
  --package nfag.odoo.v1_0 \
  --output=odoo
```

O arquivo `nfag_v1_00.py` sai vazio (o esquema raiz só declara o elemento
`NFAg`) e não entra no módulo. As tags `competApur` (tipo `xs:gYearMonth`) ficam
de fora, porque o gerador ainda não mapeia esse tipo.

## Prefixo dos campos

Cada campo leva o prefixo do esquema e de dois dígitos da versão: `nfag10_`.
Uma revisão menor do leiaute usa os mesmos campos; uma versão maior teria
campos e tabelas novos.
