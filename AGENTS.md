# AGENTS.md

Orientações para agentes de IA que trabalham neste repositório. Pessoas devem ler o
[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) e o
[docs/ARQUITETURA.md](docs/ARQUITETURA.md); este arquivo resume o que um agente precisa
e acrescenta as armadilhas que já custaram rodadas de CI. O `CLAUDE.md` é um link para
este arquivo.

## O que é este repositório

Addons do Odoo para documentos fiscais brasileiros, sobre o
[OCA/l10n-brazil](https://github.com/OCA/l10n-brazil), no template de addons da OCA:

- `l10n_br_<documento>_<grupo>`: preenche um grupo do leiaute de um documento que o
  OCA/l10n-brazil já emite (NF-e, NFC-e, NFS-e nacional, CT-e);
- `l10n_br_<documento>_spec`: modelos gerados pelo xsdata-odoo a partir do XSD de um
  documento;
- `l10n_br_<documento>`: emite um documento inteiro que o OCA/l10n-brazil não emite;
- `l10n_br_fiscal_contrib_setup_tests`: só para o CI, carrega um plano de contas nas
  empresas demo.

Séries: `18.0` (principal) e `16.0` (portes). As dependências do OCA/l10n-brazil vêm do
PyPI: leia o código delas nos pacotes publicados ou num clone do OCA/l10n-brazil, nunca
as altere a partir daqui.

## Regras

- Não invente regra fiscal, código, data ou nota técnica. Toda validação cita a fonte
  oficial (MOC, NT, XSD); o que não puder ser confirmado vai para o `readme/ROADMAP.md`.
- Um módulo por pull request, um commit por módulo sempre que possível.
- Mensagem de commit: `[ADD|FIX|IMP|MIG] <módulo>: <resumo>` em inglês, mais o trailer
  `Assisted-by: <nome da ferramenta>`. Nunca acrescente `Co-authored-by` de ferramenta
  de IA.
- Não suba a versão de um módulo existente. Módulo novo começa em `<série>.1.0.0`,
  licença AGPL-3, autor `<empresa>, Odoo Community Association (OCA)`.
- Edite os fragmentos `readme/*.md` (em português), nunca o `README.rst` ou o
  `static/description/index.html`, que o pre-commit gera. Código e comentários no código
  ficam em inglês.
- Nunca edite à mão os arquivos gerados dos módulos de spec; regere como o readme do
  spec descreve.
- Arquivos da raiz (`test-requirements.txt`, `.pre-commit-config.yaml`,
  `requirements.txt`, o módulo de setup) são compartilhados: mude-os num pull request
  próprio. O `requirements.txt` só muda pelo hook do pre-commit, a partir do
  `external_dependencies` declarado pelo nome.
- Nenhum dado real de contribuinte (CNPJ, CPF, nome, endereço) em código, teste ou dado
  de demonstração.
- Teste nunca chama webservice real: simule o transporte.
- Em texto e comentário, use pontuação ASCII simples (sem travessão tipográfico, aspas
  curvas ou caractere de reticências).

## Comandos

```bash
pre-commit run --all-files        # rode duas vezes: a primeira regera os readmes
```

Os testes rodam no CI da OCA (imagens `oca-ci`, jobs `test with Odoo` e
`test with OCB`). Para rodar localmente, use a mesma imagem com um PostgreSQL
descartável, passando os addons a testar; apague os containers ao terminar e nunca deixe
volume anônimo do Docker para trás.

## Armadilhas de CI já pagas

- O banco do CI tem só este repositório e as dependências dele. As empresas demo do
  `l10n_br_base` ficam sem plano de contas sem o módulo de setup, e qualquer módulo que
  puxa o `sale` quebra na criação do banco sem ele.
- Dado de demonstração não gera fatura nem chama o assistente de faturamento.
- As NF-e de demonstração da `16.0` não recebem o grupo de pagamento (`detPag`)
  sozinhas: os testes que validam o XML o preenchem.
- Alguns pacotes publicados da OCA importam bibliotecas que não declaram
  (`brazil_fiscal_client` e `brazilfiscalreport` na `16.0`); as fixações ficam no
  `test-requirements.txt`.
- O `cryptography` mais novo quebra o pyOpenSSL das imagens `oca-ci`: mantenha as
  fixações do `test-requirements.txt`.
- Parceiro de teste não pode repetir CNPJ dos dados de demonstração do OCA/l10n-brazil
  (por exemplo, a transportadora demo do `l10n_br_delivery`).
- CI verde pode significar que nada rodou: confira no log que os testes do módulo
  começaram e passaram.
- Um PR verde sozinho pode quebrar a base junto com os outros módulos: rebaseie sobre a
  branch atualizada antes do merge e confira o CI de novo.
- No `spec_driven_model`, deixe o marcador `spec_schema` só no pacote que guarda os
  modelos do spec, ou o documento fiscal pode resolver o schema errado pela MRO.
- O hook que cria as tabelas dos modelos restantes do spec só roda para o primeiro
  schema que a MRO do `l10n_br_fiscal.document` resolve. Módulo de documento leva um
  `_register_hook` no documento que chama `_register_remaining_schema_models_hook` com
  `spec_schema` e `spec_version` do próprio schema no contexto (veja o `l10n_br_bpe`),
  ou as tabelas dele não nascem quando outro módulo de documento está instalado.
- Campo calculado editável tem o próprio método de cálculo: o Odoo pula todos os campos
  de um método compartilhado quando um deles vem no `create`.

## Por onde começar

1. Leia o [docs/ARQUITETURA.md](docs/ARQUITETURA.md).
2. Veja um módulo do mesmo tipo: `l10n_br_nfe_med` ou `l10n_br_nfe_rastro` para grupo,
   `l10n_br_bpe_spec` e `l10n_br_bpe` para documento inteiro.
3. Procure no OCA/l10n-brazil um módulo ou pull request aberto antes de escrever código.
