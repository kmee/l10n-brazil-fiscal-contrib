Bindings Python e modelos abstratos da Nota Fiscal Eletrônica de Alienação de
Bens Imóveis (`NF-e ABI`, `modelo 77`), gerados a partir dos esquemas XSD
oficiais.

O módulo não emite a NF-e ABI: é a base do `l10n_br_nfeabi`, que injeta estes
mixins no documento fiscal (`l10n_br_fiscal.document`), no mesmo desenho dos
módulos `l10n_br_nfe_spec`, `l10n_br_cte_spec` e `l10n_br_mdfe_spec` da OCA e
do `l10n_br_nf3e_spec` deste repositório.

O `nfelib` 3.3.0 não tem a NF-e ABI. Por isso os bindings (classes `dataclass`
do xsdata) ficam neste módulo, no pacote `bindings/v1_0`, e os esquemas usados
para gerar e validar o XML ficam em `schemas/v1_0`, até a NF-e ABI entrar no
`nfelib`.

## Esquemas

São usados os esquemas do pacote `PL_NFeABI_1.00_NT2026.001_v1.06.zip`, o
"Pacote de Schemas NFeABI 1.00 [versão 1.06]" publicado pela SVRS em
18/11/2026:

- página: <https://dfe-portal.svrs.rs.gov.br/Nfabi/Documentos>
- arquivo:
  <https://dfe-portal.svrs.rs.gov.br/NFABI/DownloadArquivoEstatico/?sistema=NFABI&tipoArquivo=2&nomeArquivo=PL_NFeABI_1.00_NT2026.001_v1.06.zip>
- sha256 do zip:
  `1318a04d671150233e0b3b01efaf235a9edc79f33f18cd2ace96b8e60dd208e6`

O pacote implementa a NT 2026.001 v1.00 ("Ajustes no Leiaute e nas Regras de
Validação da NF-e ABI", aprovada pelo Ato Técnico Conjunto RFB/SUFIS/CGIBS
10/2026), com homologação em 30/11/2026 e produção em 14/12/2026.

## Divergência com o Portal Nacional da NF-e

Em 21/11/2026 o Portal Nacional da NF-e publica só o "Schemas XML NFeABI -
Pacote de Liberação 1.00 (ZIP) - Publicado em 02/09/2026"
(<https://www.nfe.fazenda.gov.br/portal/exibirArquivo.aspx?conteudo=p9XiwqPUDKo=>,
sha256 `8c1a33ef15b353b2a552f3da99fc9d4acbea1ff01029a9452e118e75847e4e26`),
anterior à NT 2026.001. O pacote da SVRS é o mais recente publicado por fonte
oficial e é o que acompanha a NT; em relação ao do Portal ele traz, entre
outros:

- `ide/tpNF` = 2 (transição), `ide/tpPagAnt` e os grupos `gPagAntecipado`,
  `gInfTribTransic` e `gInfPagAntecip`;
- `gModNat`, `transmit`, `adquirente`, `imovel`, `infOper` e `gInfTrib` com
  ocorrência mínima zero (as regras da NT dizem quando são obrigatórios);
- `imovel/cadastro` e `imovel/enquadramento` obrigatórios, as tags renomeadas
  `nIPTU`, `indINCRA` e `nINCRA` e as novas `indRIP` e `nRIP`;
- `tpEmit` 11, o `CNO` em escolha com o `cCIBObra` e `indIncorpLote` 2;
- `qrCode` com até 1000 caracteres e `cStat` com até quatro dígitos;
- o evento de desfazimento da alienação (`evDesfazimAlienac`, 112320) e a lista
  fechada de `tpEvento`.

Quando o Portal Nacional publicar o pacote da NT 2026.001, os dois pacotes
devem ser comparados de novo; se diferirem, o módulo é regerado com o que
estiver em produção.

## Geração dos bindings

Com o `generate_bindings.py` do [nfelib](https://github.com/akretion/nfelib)
(commit `d1b0fbe`), o xsdata 25.7 e os esquemas do pacote acima copiados em
`nfelib/nfeabi/schemas/v1_0` (só os `.xsd`):

- no `.xsdata.xml` do nfelib foram acrescentadas as extensões
  `nfelib.CommonMixin` das classes `TnfeAbi`, `TprotNfeAbi`, `NfeabiProc`,
  `EvCancNfeAbi` e `EvDesfazimAlienac` (as mesmas da NF3e e da NFCom), e
  `RelativeImports` passou a `true`, para o pacote funcionar dentro do módulo;
- no `SCHEMAS` do script foi incluída a entrada `nfeabi`, com o pacote
  `odoo.addons.l10n_br_nfeabi_spec.bindings.v1_0`.

```bash
python generate_bindings.py nfeabi
```

O resultado é o pacote `bindings` deste módulo, sem alteração à mão. Com os
imports relativos, o mesmo pacote pode ser copiado para
`nfelib/nfeabi/bindings/v1_0`. O arquivo `bindings/.ruff.toml` só deixa os
padrões longos do esquema, no código gerado, numa linha só.

## Geração dos modelos

Os arquivos de `models/v1_0` foram gerados pelo
[xsdata-odoo](https://github.com/akretion/xsdata-odoo) 1.2.2, partindo do
esquema raiz `NFeABI_v1.00.xsd` (que traz `nfeabiTiposBasico` e
`tiposGeralNFeABI`):

```bash
export XSDATA_SCHEMA=nfeabi
export XSDATA_VERSION=10
export XSDATA_LANG="portuguese"
export XSDATA_CURRENCY_FIELD=brl_currency_id
export XSDATA_SCHEMA_NOTE="PL_NFeABI_1.00_NT2026.001_v1.06"
export XSDATA_HEADER=$'Copyright 2026 KMEE\nLicense AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).'

xsdata generate nfelib/nfeabi/schemas/v1_0/NFeABI_v1.00.xsd \
  --package nfelib.nfeabi.odoo.v1_0 \
  --output=odoo
```

O `chNFePagAnt` do grupo `gPagAntecipado` é uma lista de chaves no esquema, e o
gerador o mapeia para um único campo.

## Prefixo dos campos

Cada campo leva o prefixo do esquema e de dois dígitos da versão: `nfeabi10_`.
Uma revisão menor do leiaute usa os mesmos campos; uma versão maior teria
campos e tabelas novos.
