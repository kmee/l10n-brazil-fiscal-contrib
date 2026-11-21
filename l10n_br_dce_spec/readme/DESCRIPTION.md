Este módulo traz os esquemas XSD, os bindings Python e os modelos abstratos da
Declaração de Conteúdo Eletrônica (`DC-e`, `modelo 99`, leiaute 1.00).

Ele não emite a DC-e: é a base do `l10n_br_dce`, que empilha estes modelos no
documento fiscal (`l10n_br_fiscal.document`), no mesmo desenho dos módulos
`l10n_br_mdfe_spec`, `l10n_br_cte_spec` e `l10n_br_bpe_spec`.

A biblioteca `nfelib` (3.3.0) ainda não tem a DC-e. Por isso, além dos modelos
Odoo, o módulo guarda os esquemas oficiais (`schemas/v1_0`) e os bindings
gerados a partir deles (`bindings/v1_0`), no mesmo formato de `nfelib/<doc>/`.

## Esquemas

Pacote "Schemas NT 2024.001" do Portal DC-e (SVRS), publicado em 08/10/2024,
que acompanha a NT 2024.001 (versão vigente da NT: 1.30, de agosto de 2026):

- página: https://dfe-portal.svrs.rs.gov.br/DCE/Documentos
- arquivo:
  https://dfe-portal.svrs.rs.gov.br/DCE/DownloadArquivoEstatico/?sistema=DCE&tipoArquivo=2&nomeArquivo=PL_DCe_v1.00a_NT2024.001v1.00.zip
- `PL_DCe_v1.00a_NT2024.001v1.00.zip`, sha256
  `9530d6c15f44de07cf4acc18566196a381f11051b59af3c2e36e3c8473701a6a`

O pacote traz três pastas (`dce`, `evento` e `consulta`), cada uma com a sua
cópia dos tipos comuns. Os arquivos foram juntados numa pasta só, como a
`nfelib` faz:

- `dce/`: todos os arquivos (DC-e, `procDCe`, `retDCe`, tipos e assinatura);
- `evento/`: `eventoDCe`, `eventoDCeTiposBasico`, `evCancDCe`, `procEventoDCe`
  e `retEventoDCe`;
- `consulta/`: os arquivos de consulta da situação e do status do serviço.

As cópias de `tiposGeralDCe_v1.00.xsd` e `xmldsig-core-schema_v1.01.xsd` das
três pastas são iguais. O `consulta/dceTiposBasico_v1.00.xsd` não entra: é uma
cópia antiga (sem o `tpEmit` 4 e sem o grupo `infSolicDCe`) que nenhum outro
arquivo inclui; vale a de `dce/`. Os finais de linha foram convertidos para LF
e os espaços no fim das linhas, removidos.

## Bindings

Os arquivos de `bindings/v1_0` foram gerados com o `generate_bindings.py` da
[nfelib](https://github.com/akretion/nfelib) 3.3.0 (xsdata 25.7 com os patches
da `nfelib`), com a configuração `.xsdata.xml` da `nfelib` 3.3.0 e três
mudanças:

- as extensões `nfelib.CommonMixin` das classes da DC-e (`^Tdce$`,
  `^TprotDce$`, `^DceProc$` e `^EvCancDce$`), no padrão das outras classes
  raiz da `nfelib`;
- as substituições de nome de campo `^Fisco$`, `^Marketplace$` e
  `^Transportadora$` para `fisco`, `marketplace` e `transportadora`, como a
  `nfelib` faz com o `Comp` do CT-e: no grupo `infDCe` o campo e a classe
  aninhada teriam o mesmo nome, e a classe apagaria o valor padrão do campo
  (a tag no XML continua `Fisco`, `Marketplace` e `Transportadora`);
- `RelativeImports` ligado, porque o pacote mora dentro do módulo Odoo e o
  pylint-odoo da OCA recusa o import absoluto do próprio módulo.

A pasta `bindings` tem um `.ruff.toml` que estende o da raiz e desliga só o
E501: os padrões dos tipos do esquema são expressões regulares longas que não
quebram linha.

O pacote de destino foi registrado no `SCHEMAS` do script:

```python
SCHEMAS["dce"] = SchemaConfig(
    name="dce",
    schema_dir="odoo/addons/l10n_br_dce_spec/schemas/v1_0",
    package="odoo.addons.l10n_br_dce_spec.bindings.v1_0",
)
```

e a geração rodou com `python generate_bindings.py dce`.

## Modelos

Os arquivos de `models/v1_0` foram gerados pelo
[xsdata-odoo](https://github.com/akretion/xsdata-odoo) 1.2.2 a partir do
esquema raiz `dce_v1.00.xsd`:

```bash
export XSDATA_SCHEMA=dce
export XSDATA_VERSION=10
export XSDATA_LANG="portuguese"
export XSDATA_CURRENCY_FIELD=brl_currency_id
export XSDATA_SCHEMA_NOTE="PL_DCe_v1.00a_NT2024.001v1.00"
export XSDATA_HEADER=$'Copyright 2026 KMEE\nLicense AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).'

xsdata generate odoo/addons/l10n_br_dce_spec/schemas/v1_0/dce_v1.00.xsd \
  --package odoo.addons.l10n_br_dce_spec.models.v1_0 \
  --output=odoo
```

O arquivo `dce_v1_00.py` sai vazio (o esquema raiz só declara o elemento `DCe`)
e não entra no módulo. O atributo `xCampo` dos grupos `obsEmit`, `obsFisco`,
`obsMarketplace` e `obsECT` não tem tipo no esquema (`anySimpleType`) e o
gerador não o mapeia.

## Prefixo dos campos

Cada campo leva o prefixo do esquema e de dois dígitos da versão: `dce10_`.
Uma revisão menor do leiaute usa os mesmos campos; uma versão maior teria campos
e tabelas novos.
